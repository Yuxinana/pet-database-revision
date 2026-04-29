from __future__ import annotations

import json
import os
import re
import sqlite3
import threading
import time
from dataclasses import dataclass
from http import HTTPStatus
from pathlib import Path
from typing import Any, Protocol
from urllib.parse import quote

ROOT_DIR = Path(__file__).resolve().parents[3]
from . import query_registry

DEFAULT_MODEL = "glm-5.1"
DEFAULT_BASE_URL = "https://open.bigmodel.cn/api/paas/v4/"
DEFAULT_TIMEOUT_SECONDS = 90
DEFAULT_GLM_MAX_CONCURRENT_REQUESTS = 1
DEFAULT_GLM_MIN_REQUEST_INTERVAL_SECONDS = 1.0
DEFAULT_GLM_RATE_LIMIT_RETRIES = 4
DEFAULT_GLM_RATE_LIMIT_BACKOFF_SECONDS = 2.0
DEFAULT_GLM_TIMEOUT_RETRIES = 1
DEFAULT_GLM_TIMEOUT_BACKOFF_SECONDS = 2.0
DEFAULT_GLM_EMPTY_RESPONSE_RETRIES = 2
DEFAULT_GLM_EMPTY_RESPONSE_BACKOFF_SECONDS = 1.0
MAX_GLM_RATE_LIMIT_SLEEP_SECONDS = 30.0
MAX_GLM_TIMEOUT_SLEEP_SECONDS = 15.0
MAX_GLM_EMPTY_RESPONSE_SLEEP_SECONDS = 5.0
MAX_RESULT_ROWS = 50
MAX_REVIEWED_QUERY_CANDIDATES = 3
MAX_REVIEWED_QUERY_CONTEXT = 2
PROMPT_METHODS = ("zero_shot", "schema_grounded", "few_shot", "self_check_repair")
ENV_PATH = ROOT_DIR / ".env"

BLOCKED_SQL_KEYWORDS = (
    "INSERT",
    "UPDATE",
    "DELETE",
    "DROP",
    "ALTER",
    "CREATE",
    "REPLACE",
    "TRUNCATE",
    "ATTACH",
    "DETACH",
    "PRAGMA",
    "VACUUM",
    "REINDEX",
)

PROMPT_STOPWORDS = {
    "a",
    "about",
    "all",
    "an",
    "and",
    "are",
    "by",
    "each",
    "for",
    "from",
    "has",
    "have",
    "how",
    "i",
    "in",
    "is",
    "list",
    "me",
    "most",
    "of",
    "on",
    "please",
    "show",
    "the",
    "their",
    "to",
    "what",
    "which",
    "who",
    "with",
}

PROMPT_DOMAIN_TOKENS = {
    "adopt",
    "adoption",
    "applicant",
    "application",
    "assignment",
    "available",
    "capacity",
    "care",
    "due",
    "follow",
    "followup",
    "health",
    "housing",
    "medical",
    "occupancy",
    "pet",
    "review",
    "shelter",
    "species",
    "status",
    "vaccination",
    "vaccine",
    "volunteer",
}

READ_ONLY_QUERY_HINTS = {
    "analyze",
    "any",
    "compare",
    "count",
    "find",
    "give",
    "how",
    "list",
    "show",
    "summarize",
    "what",
    "which",
    "who",
}

MUTATION_INTENT_TOKENS = {
    "alter",
    "attach",
    "create",
    "delete",
    "detach",
    "drop",
    "insert",
    "remove",
    "replace",
    "truncate",
    "update",
}

SEMANTIC_REWRITE_RULES: tuple[tuple[str, str | Any, str], ...] = (
    (
        r"\bhow full is each shelter\b",
        "what is the occupancy rate of each shelter",
        "Mapped how full is each shelter to an occupancy-rate question.",
    ),
    (
        r"\bhow full are the shelters\b",
        "what is the occupancy rate of the shelters",
        "Mapped how full are the shelters to an occupancy-rate question.",
    ),
    (
        r"\bfullest\b",
        "highest occupancy rate",
        "Mapped fullest to highest occupancy rate.",
    ),
    (
        r"\banimals?\b",
        lambda match: "pets" if match.group(0).lower().endswith("s") else "pet",
        "Interpreted animal as pet, because PET is the canonical animal entity in this database.",
    ),
    (
        r"\badoptable\b",
        "available for adoption",
        "Expanded adoptable to available for adoption to align with PET.status semantics.",
    ),
    (
        r"\bup for adoption\b",
        "available for adoption",
        "Expanded up for adoption to available for adoption to align with PET.status semantics.",
    ),
    (
        r"\bcan be adopted\b",
        "available for adoption",
        "Expanded can be adopted to available for adoption to align with PET.status semantics.",
    ),
    (
        r"\bshots?\b",
        lambda match: "vaccinations" if match.group(0).lower().endswith("s") else "vaccination",
        "Mapped shots to vaccinations for the VACCINATION table.",
    ),
    (
        r"\bimmuni[sz]ations?\b",
        lambda match: "vaccinations" if match.group(0).lower().endswith("s") else "vaccination",
        "Mapped immunization wording to vaccinations for the VACCINATION table.",
    ),
    (
        r"\bmedical history\b",
        "health timeline",
        "Mapped medical history to a health timeline over vaccinations and medical records.",
    ),
    (
        r"\bhealth history\b",
        "health timeline",
        "Mapped health history to a health timeline over vaccinations and medical records.",
    ),
    (
        r"\bbranches?\b",
        lambda match: "shelters" if match.group(0).lower().endswith("s") else "shelter",
        "Mapped branch wording to shelters.",
    ),
    (
        r"\bfacilit(?:y|ies)\b",
        lambda match: "shelters" if match.group(0).lower().endswith("ies") else "shelter",
        "Mapped facility wording to shelters.",
    ),
    (
        r"\bpending review\b",
        "under review",
        "Mapped pending review to the Under Review application status.",
    ),
    (
        r"\bwaiting for review\b",
        "under review",
        "Mapped waiting for review to the Under Review application status.",
    ),
    (
        r"\bstill waiting\b",
        "under review",
        "Mapped still waiting to the Under Review application status.",
    ),
    (
        r"\bfollow[\s-]?ups?\b",
        lambda match: "follow-up outcomes" if match.group(0).lower().endswith("s") else "follow-up outcome",
        "Normalized follow-up wording to the FOLLOW_UP table vocabulary.",
    ),
    (
        r"\bdid the most work\b",
        "completed the most care tasks",
        "Mapped did the most work to completed the most care tasks for volunteer workload questions.",
    ),
    (
        r"\bhow full\b",
        "occupancy rate",
        "Mapped how full to occupancy rate for shelter-capacity questions.",
    ),
)

TABLE_SEMANTICS = {
    "SHELTER": "Shelter branches with a name, location, and capacity. PET.shelter_id points here.",
    "PET": "Animals cared for by shelters. Age questions usually use estimated_birth_date; length-of-stay questions use intake_date.",
    "APPLICANT": "People who apply to adopt pets, including housing_type and prior pet experience.",
    "ADOPTION_APPLICATION": "Adoption requests that connect one applicant to one pet. status is the review workflow.",
    "ADOPTION_RECORD": "Final completed adoptions created from approved applications.",
    "VOLUNTEER": "Shelter volunteers who can receive care assignments.",
    "CARE_ASSIGNMENT": "Volunteer tasks scheduled for a pet on a date and shift, with task_type and status.",
    "VACCINATION": "Vaccination events for pets, including vaccination_date and next_due_date.",
    "MEDICAL_RECORD": "Medical visits or treatment records for pets.",
    "FOLLOW_UP": "Post-adoption follow-up records linked to a completed adoption.",
    "SYSTEM_LOG": "Operational audit events used for system activity tracking.",
}

CANONICAL_DOMAIN_VALUES = {
    ("PET", "status"): ("available", "reserved", "adopted", "medical_hold"),
    ("PET", "species"): ("Bird", "Cat", "Dog", "Rabbit"),
    ("PET", "sex"): ("Female", "Male"),
    ("ADOPTION_APPLICATION", "status"): ("Under Review", "Approved", "Rejected"),
    (
        "APPLICANT",
        "housing_type",
    ): (
        "Apartment",
        "Condo",
        "House",
        "Townhouse",
        "House with garden",
        "House without garden",
        "Shared housing",
    ),
    ("CARE_ASSIGNMENT", "shift"): ("Morning", "Afternoon", "Evening"),
    (
        "CARE_ASSIGNMENT",
        "task_type",
    ): (
        "Cleaning",
        "Feeding",
        "Grooming",
        "Socializing",
        "Walking",
        "Medical support",
    ),
    ("CARE_ASSIGNMENT", "status"): ("Scheduled", "Completed", "Cancelled"),
    ("FOLLOW_UP", "followup_type"): ("Phone Check", "Home Visit", "Vet Check"),
    ("FOLLOW_UP", "result_status"): ("Excellent", "Good", "Satisfactory", "Needs Improvement"),
    ("MEDICAL_RECORD", "record_type"): ("Check-up", "Surgery", "Treatment", "Injury", "Dental"),
}

QUERY_INTENT_HINTS = {
    "view_all_pets_currently_housed_in_a_specific_shelter": (
        "pets in shelter",
        "shelter roster",
        "housed in shelter",
    ),
    "view_all_pets_that_are_currently_available_for_adoption": (
        "available pets",
        "adoptable pets",
        "ready for adoption",
        "available dogs",
        "available cats",
        "available rabbits",
        "available birds",
    ),
    "view_the_full_health_information_of_a_specific_pet": (
        "health timeline",
        "medical history",
        "vaccination history",
        "what happened medically",
    ),
    "view_pets_whose_vaccination_due_date_is_approaching": (
        "vaccination due",
        "shots due",
        "immunization due",
        "due soon",
    ),
    "view_upcoming_care_assignments_for_a_volunteer": (
        "volunteer schedule",
        "upcoming assignments",
        "care tasks",
    ),
    "view_all_adoption_applications_that_are_currently_under_review": (
        "under review",
        "pending review",
        "review queue",
        "still waiting",
    ),
    "analyze_current_occupancy_of_each_shelter": (
        "occupancy rate",
        "how full",
        "capacity pressure",
        "fullest shelter",
    ),
    "analyze_pets_that_have_stayed_the_longest_in_the_shelter": (
        "longest stay",
        "been here the longest",
        "days in shelter",
    ),
    "analyze_adoption_application_results_by_housing_type": (
        "approval rate",
        "housing type",
        "approval outcomes",
        "houses versus apartments",
    ),
    "analyze_adoption_demand_and_success_rate_by_pet_species": (
        "adoption performance",
        "success rate",
        "demand by species",
        "approved vs rejected applications",
    ),
    "analyze_volunteer_workload_based_on_care_assignments": (
        "volunteer workload",
        "completed tasks",
        "assignment load",
        "most work",
    ),
    "analyze_postadoption_followup_outcomes": (
        "follow-up outcomes",
        "post adoption outcomes",
        "adjusting well",
    ),
}

SEMANTIC_FAILURE_EXPLANATION_PATTERNS = (
    "unclear",
    "incomplete",
    "not enough context",
    "does not provide enough context",
    "typo",
)


class LlmSqlError(Exception):
    def __init__(self, status: HTTPStatus, message: str, payload: dict[str, Any] | None = None):
        super().__init__(message)
        self.status = status
        self.message = message
        self.payload = payload or {}


class ChatClient(Protocol):
    def complete_json(self, messages: list[dict[str, str]], response_format: dict[str, str] | None = None) -> str:
        ...


@dataclass(frozen=True)
class PromptSemantics:
    normalized_prompt: str
    rewrite_notes: tuple[str, ...]
    hints: tuple[str, ...]
    meaningful: bool


@dataclass(frozen=True)
class ReviewedQueryCandidate:
    name: str
    title: str
    description: str
    sql: str
    category: str
    score: int
    matched_terms: tuple[str, ...]


@dataclass(frozen=True)
class DirectSqlResolution:
    sql: str
    explanation: str
    tables_used: tuple[str, ...]
    assumptions: tuple[str, ...]
    confidence: float
    intent: str
    strategy: str = "rule_based"


@dataclass(frozen=True)
class LlmConfig:
    api_key: str | None
    model: str = DEFAULT_MODEL
    base_url: str = DEFAULT_BASE_URL
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS
    max_concurrent_requests: int = DEFAULT_GLM_MAX_CONCURRENT_REQUESTS
    min_request_interval_seconds: float = DEFAULT_GLM_MIN_REQUEST_INTERVAL_SECONDS
    rate_limit_retries: int = DEFAULT_GLM_RATE_LIMIT_RETRIES
    rate_limit_backoff_seconds: float = DEFAULT_GLM_RATE_LIMIT_BACKOFF_SECONDS
    timeout_retries: int = DEFAULT_GLM_TIMEOUT_RETRIES
    timeout_backoff_seconds: float = DEFAULT_GLM_TIMEOUT_BACKOFF_SECONDS
    empty_response_retries: int = DEFAULT_GLM_EMPTY_RESPONSE_RETRIES
    empty_response_backoff_seconds: float = DEFAULT_GLM_EMPTY_RESPONSE_BACKOFF_SECONDS

    @classmethod
    def from_env(cls) -> "LlmConfig":
        local_env = read_local_env()

        def config_value(name: str, default: str | None = None) -> str | None:
            return os.getenv(name) or local_env.get(name) or default

        def int_config(name: str, default: int, minimum: int) -> int:
            raw = config_value(name, str(default))
            try:
                return max(minimum, int(raw or default))
            except ValueError:
                return default

        def float_config(name: str, default: float, minimum: float) -> float:
            raw = config_value(name, str(default))
            try:
                return max(minimum, float(raw or default))
            except ValueError:
                return default

        return cls(
            api_key=config_value("ZAI_API_KEY") or config_value("GLM_API_KEY"),
            model=config_value("GLM_MODEL", DEFAULT_MODEL) or DEFAULT_MODEL,
            base_url=config_value("GLM_BASE_URL", DEFAULT_BASE_URL) or DEFAULT_BASE_URL,
            timeout_seconds=int_config("LLM_SQL_TIMEOUT_SECONDS", DEFAULT_TIMEOUT_SECONDS, 1),
            max_concurrent_requests=int_config(
                "GLM_MAX_CONCURRENT_REQUESTS",
                DEFAULT_GLM_MAX_CONCURRENT_REQUESTS,
                1,
            ),
            min_request_interval_seconds=float_config(
                "GLM_MIN_REQUEST_INTERVAL_SECONDS",
                DEFAULT_GLM_MIN_REQUEST_INTERVAL_SECONDS,
                0.0,
            ),
            rate_limit_retries=int_config("GLM_RATE_LIMIT_RETRIES", DEFAULT_GLM_RATE_LIMIT_RETRIES, 0),
            rate_limit_backoff_seconds=float_config(
                "GLM_RATE_LIMIT_BACKOFF_SECONDS",
                DEFAULT_GLM_RATE_LIMIT_BACKOFF_SECONDS,
                0.0,
            ),
            timeout_retries=int_config("GLM_TIMEOUT_RETRIES", DEFAULT_GLM_TIMEOUT_RETRIES, 0),
            timeout_backoff_seconds=float_config(
                "GLM_TIMEOUT_BACKOFF_SECONDS",
                DEFAULT_GLM_TIMEOUT_BACKOFF_SECONDS,
                0.0,
            ),
            empty_response_retries=int_config(
                "GLM_EMPTY_RESPONSE_RETRIES",
                DEFAULT_GLM_EMPTY_RESPONSE_RETRIES,
                0,
            ),
            empty_response_backoff_seconds=float_config(
                "GLM_EMPTY_RESPONSE_BACKOFF_SECONDS",
                DEFAULT_GLM_EMPTY_RESPONSE_BACKOFF_SECONDS,
                0.0,
            ),
        )


def read_local_env(path: Path | None = None) -> dict[str, str]:
    path = path or ENV_PATH
    if not path.exists():
        return {}
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            values[key] = value
    return values


_GLM_CONCURRENCY_CONDITION = threading.Condition()
_GLM_ACTIVE_REQUESTS = 0
_GLM_REQUEST_SPACING_LOCK = threading.Lock()
_GLM_NEXT_REQUEST_AT = 0.0


class _GlmRequestSlot:
    def __init__(self, max_concurrent_requests: int):
        self.max_concurrent_requests = max(1, max_concurrent_requests)
        self.acquired = False

    def __enter__(self) -> "_GlmRequestSlot":
        global _GLM_ACTIVE_REQUESTS
        with _GLM_CONCURRENCY_CONDITION:
            while _GLM_ACTIVE_REQUESTS >= self.max_concurrent_requests:
                _GLM_CONCURRENCY_CONDITION.wait()
            _GLM_ACTIVE_REQUESTS += 1
            self.acquired = True
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        global _GLM_ACTIVE_REQUESTS
        if not self.acquired:
            return
        with _GLM_CONCURRENCY_CONDITION:
            _GLM_ACTIVE_REQUESTS = max(0, _GLM_ACTIVE_REQUESTS - 1)
            self.acquired = False
            _GLM_CONCURRENCY_CONDITION.notify_all()


def _wait_for_glm_request_window(min_interval_seconds: float) -> None:
    global _GLM_NEXT_REQUEST_AT
    if min_interval_seconds <= 0:
        return
    with _GLM_REQUEST_SPACING_LOCK:
        now = time.monotonic()
        scheduled_at = max(now, _GLM_NEXT_REQUEST_AT)
        _GLM_NEXT_REQUEST_AT = scheduled_at + min_interval_seconds
    sleep_seconds = scheduled_at - now
    if sleep_seconds > 0:
        time.sleep(sleep_seconds)


def _glm_error_status_code(exc: Exception) -> int | None:
    status_code = getattr(exc, "status_code", None)
    if status_code is None:
        response = getattr(exc, "response", None)
        status_code = getattr(response, "status_code", None)
    try:
        return int(status_code) if status_code is not None else None
    except (TypeError, ValueError):
        return None


def _is_glm_rate_limit_error(exc: Exception) -> bool:
    status_code = _glm_error_status_code(exc)
    message = str(exc).lower()
    return (
        status_code == 429
        or "error code: 429" in message
        or "too many requests" in message
        or "rate limit" in message
        or "速率限制" in message
        or "1302" in message
    )


def _is_glm_timeout_error(exc: Exception) -> bool:
    class_name = exc.__class__.__name__.lower()
    message = str(exc).lower()
    return (
        isinstance(exc, TimeoutError)
        or "timeout" in class_name
        or "timed out" in message
        or "timeout" in message
    )


def _retry_after_seconds(exc: Exception) -> float | None:
    response = getattr(exc, "response", None)
    headers = getattr(response, "headers", None)
    if not headers or not hasattr(headers, "get"):
        return None
    retry_after = headers.get("retry-after") or headers.get("Retry-After")
    if retry_after is None:
        return None
    try:
        return max(0.0, float(retry_after))
    except (TypeError, ValueError):
        return None


def _glm_rate_limit_sleep_seconds(config: LlmConfig, exc: Exception, retry_index: int) -> float:
    retry_after = _retry_after_seconds(exc)
    if retry_after is not None:
        return min(retry_after, MAX_GLM_RATE_LIMIT_SLEEP_SECONDS)
    return min(
        config.rate_limit_backoff_seconds * (2**retry_index),
        MAX_GLM_RATE_LIMIT_SLEEP_SECONDS,
    )


def _glm_timeout_sleep_seconds(config: LlmConfig, retry_index: int) -> float:
    return min(
        config.timeout_backoff_seconds * (2**retry_index),
        MAX_GLM_TIMEOUT_SLEEP_SECONDS,
    )


def _glm_empty_response_sleep_seconds(config: LlmConfig, retry_index: int) -> float:
    return min(
        config.empty_response_backoff_seconds * (2**retry_index),
        MAX_GLM_EMPTY_RESPONSE_SLEEP_SECONDS,
    )


class GlmChatClient:
    def __init__(self, config: LlmConfig):
        if not config.api_key:
            raise LlmSqlError(
                HTTPStatus.SERVICE_UNAVAILABLE,
                "ZAI_API_KEY is not configured. Set ZAI_API_KEY or GLM_API_KEY before using GLM-generated SQL.",
            )
        self.config = config

    def complete_json(self, messages: list[dict[str, str]], response_format: dict[str, str] | None = None) -> str:
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise LlmSqlError(
                HTTPStatus.SERVICE_UNAVAILABLE,
                "The openai package is required for GLM-generated SQL. Run pip install -r requirements.txt.",
            ) from exc

        client = OpenAI(
            api_key=self.config.api_key,
            base_url=self.config.base_url,
            timeout=self.config.timeout_seconds,
            max_retries=0,
        )
        rate_limit_attempt = 0
        timeout_attempt = 0
        empty_response_attempt = 0
        with _GlmRequestSlot(self.config.max_concurrent_requests):
            while True:
                _wait_for_glm_request_window(self.config.min_request_interval_seconds)
                try:
                    response = client.chat.completions.create(
                        model=self.config.model,
                        messages=messages,
                        temperature=0,
                        max_tokens=1200,
                        response_format=response_format or {"type": "json_object"},
                    )
                except Exception as exc:
                    message = str(exc)
                    if _is_glm_timeout_error(exc):
                        if timeout_attempt < self.config.timeout_retries:
                            time.sleep(_glm_timeout_sleep_seconds(self.config, timeout_attempt))
                            timeout_attempt += 1
                            continue
                        raise LlmSqlError(
                            HTTPStatus.GATEWAY_TIMEOUT,
                            (
                                f"GLM request timed out after {timeout_attempt + 1} attempt(s) "
                                f"of {self.config.timeout_seconds} seconds. "
                                "Increase LLM_SQL_TIMEOUT_SECONDS or try again later."
                            ),
                            {
                                "timeout": True,
                                "timeoutSeconds": self.config.timeout_seconds,
                                "timeoutAttempts": timeout_attempt + 1,
                                "timeoutRetries": self.config.timeout_retries,
                            },
                        ) from exc
                    if _is_glm_rate_limit_error(exc):
                        if rate_limit_attempt < self.config.rate_limit_retries:
                            time.sleep(_glm_rate_limit_sleep_seconds(self.config, exc, rate_limit_attempt))
                            rate_limit_attempt += 1
                            continue
                        raise LlmSqlError(
                            HTTPStatus.TOO_MANY_REQUESTS,
                            (
                                f"GLM account rate limit reached after {rate_limit_attempt + 1} attempt(s). "
                                "Reduce request frequency or increase the provider quota. "
                                f"Last error: {message}"
                            ),
                            {
                                "rateLimited": True,
                                "providerStatus": _glm_error_status_code(exc),
                                "maxConcurrentRequests": self.config.max_concurrent_requests,
                                "rateLimitRetries": self.config.rate_limit_retries,
                            },
                        ) from exc
                    status = HTTPStatus.GATEWAY_TIMEOUT if "timeout" in message.lower() else HTTPStatus.BAD_GATEWAY
                    raise LlmSqlError(status, f"GLM request failed: {message}") from exc

                content = response.choices[0].message.content
                if content:
                    return content
                if empty_response_attempt < self.config.empty_response_retries:
                    time.sleep(_glm_empty_response_sleep_seconds(self.config, empty_response_attempt))
                    empty_response_attempt += 1
                    continue
                raise LlmSqlError(
                    HTTPStatus.BAD_GATEWAY,
                    "GLM returned an empty response.",
                    {
                        "emptyResponse": True,
                        "emptyResponseAttempts": empty_response_attempt + 1,
                        "emptyResponseRetries": self.config.empty_response_retries,
                    },
                )


def contains_any_phrase(text: str, phrases: tuple[str, ...] | list[str] | set[str]) -> bool:
    return any(re.search(rf"\b{re.escape(phrase)}\b", text, flags=re.IGNORECASE) for phrase in phrases)


def merge_prompt_semantics(prompt_semantics: PromptSemantics, prepend_notes: list[str] | tuple[str, ...]) -> PromptSemantics:
    if not prepend_notes:
        return prompt_semantics
    merged_notes: list[str] = []
    for note in [*prepend_notes, *prompt_semantics.rewrite_notes]:
        if note and note not in merged_notes:
            merged_notes.append(note)
    return PromptSemantics(
        normalized_prompt=prompt_semantics.normalized_prompt,
        rewrite_notes=tuple(merged_notes),
        hints=prompt_semantics.hints,
        meaningful=prompt_semantics.meaningful,
    )


def extract_read_only_subprompt(prompt: str) -> tuple[str, tuple[str, ...]]:
    segments = [
        normalize_prompt_whitespace(part)
        for part in re.split(r"\s*(?:;|\b(?:and then|then|after that)\b)\s*", prompt, flags=re.IGNORECASE)
        if normalize_prompt_whitespace(part)
    ]
    if len(segments) <= 1:
        return prompt, ()
    kept_segments: list[str] = []
    for segment in segments:
        lower = segment.lower()
        has_query_signal = contains_any_phrase(lower, tuple(READ_ONLY_QUERY_HINTS))
        has_mutation_signal = contains_any_phrase(lower, tuple(MUTATION_INTENT_TOKENS))
        if has_query_signal and not has_mutation_signal:
            kept_segments.append(segment)
    if not kept_segments:
        return prompt, ()
    sanitized = kept_segments[-1]
    if sanitized == prompt:
        return prompt, ()
    return sanitized, ("Ignored destructive instructions and kept the read-only part of the request.",)


def normalize_prompt_whitespace(prompt: str) -> str:
    return re.sub(r"\s+", " ", prompt).strip()


def tokenize_prompt(text: str) -> list[str]:
    tokens: list[str] = []
    for token in re.findall(r"[a-z0-9_]+", text.lower()):
        tokens.append(token)
        if token.endswith("ies") and len(token) > 4:
            tokens.append(token[:-3] + "y")
        elif token.endswith("s") and len(token) > 3 and not token.endswith("ss"):
            tokens.append(token[:-1])
    return tokens


def prompt_has_meaningful_content(prompt: str) -> bool:
    content_tokens = [token for token in tokenize_prompt(prompt) if token not in PROMPT_STOPWORDS]
    long_tokens = [token for token in content_tokens if len(token) >= 3]
    has_domain_token = any(token in PROMPT_DOMAIN_TOKENS for token in content_tokens)
    return has_domain_token or len(long_tokens) >= 1


def extract_numeric_reference(prompt: str, entity: str) -> int | None:
    match = re.search(rf"\b{re.escape(entity)}\s*#?\s*(\d+)\b", prompt, flags=re.IGNORECASE)
    if not match:
        return None
    try:
        return int(match.group(1))
    except ValueError:
        return None


def extract_requested_species(prompt: str) -> str | None:
    species_aliases = {
        "bird": "Bird",
        "birds": "Bird",
        "cat": "Cat",
        "cats": "Cat",
        "dog": "Dog",
        "dogs": "Dog",
        "rabbit": "Rabbit",
        "rabbits": "Rabbit",
    }
    for alias, canonical in species_aliases.items():
        if re.search(rf"\b{re.escape(alias)}\b", prompt, flags=re.IGNORECASE):
            return canonical
    return None


def extract_requested_housing_types(prompt: str) -> list[str]:
    housing_aliases = {
        "apartment": "Apartment",
        "apartments": "Apartment",
        "condo": "Condo",
        "condos": "Condo",
        "house": "House",
        "houses": "House",
        "townhouse": "Townhouse",
        "townhouses": "Townhouse",
    }
    values: list[str] = []
    for alias, canonical in housing_aliases.items():
        if re.search(rf"\b{re.escape(alias)}\b", prompt, flags=re.IGNORECASE) and canonical not in values:
            values.append(canonical)
    return values


def extract_requested_application_statuses(prompt: str) -> list[str]:
    status_aliases = (
        ("under review", "Under Review"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    )
    values: list[str] = []
    prompt_lower = prompt.lower()
    for alias, canonical in status_aliases:
        if alias in prompt_lower and canonical not in values:
            values.append(canonical)
    return values


def sql_quote(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def build_direct_resolution(
    sql: str,
    explanation: str,
    tables_used: tuple[str, ...],
    assumptions: tuple[str, ...] = (),
    confidence: float = 0.99,
    intent: str = "rule_based",
) -> DirectSqlResolution:
    return DirectSqlResolution(
        sql=sql.strip(),
        explanation=explanation,
        tables_used=tables_used,
        assumptions=assumptions,
        confidence=confidence,
        intent=intent,
    )


def analyze_prompt_semantics(prompt: str) -> PromptSemantics:
    normalized = normalize_prompt_whitespace(prompt)
    rewrite_notes: list[str] = []
    for pattern, replacement, note in SEMANTIC_REWRITE_RULES:
        normalized, replacements = re.subn(pattern, replacement, normalized, flags=re.IGNORECASE)
        normalized = normalize_prompt_whitespace(normalized)
        if replacements and note not in rewrite_notes:
            rewrite_notes.append(note)

    normalized_lower = normalized.lower()
    hints: list[str] = []
    if re.search(r"\b(oldest|youngest)\b", normalized_lower):
        if re.search(r"\b(stay|stayed|longest|been here|intake)\b", normalized_lower):
            hints.append("Interpret shelter-stay questions with PET.intake_date or days_in_shelter.")
        else:
            hints.append("Interpret oldest or youngest pet questions with PET.estimated_birth_date when available.")
    if re.search(r"\boccupancy rate\b", normalized_lower):
        hints.append(
            "Shelter occupancy should count active pets whose status is available, reserved, or medical_hold against SHELTER.capacity."
        )
    if re.search(r"\b(been here|stay|stayed|longest)\b", normalized_lower):
        hints.append("Length-of-stay questions should rank PET.intake_date or derived shelter days, not birth date.")
    if re.search(r"\badoption performance\b", normalized_lower):
        hints.append("Broad adoption performance questions should return a conservative adoption summary instead of a placeholder refusal.")
    if "vaccination" in normalized_lower and "soon" in normalized_lower:
        hints.append(
            "When vaccinations are due soon and the user gives no window, use next_due_date from today through the next 30 days."
        )

    return PromptSemantics(
        normalized_prompt=normalized,
        rewrite_notes=tuple(rewrite_notes),
        hints=tuple(hints),
        meaningful=prompt_has_meaningful_content(normalized),
    )


def build_query_match_text(query: query_registry.StoredQuery) -> str:
    extras = " ".join(QUERY_INTENT_HINTS.get(query.name, ()))
    return " ".join(part for part in (query.title, query.description, query.category, extras) if part)


def find_reviewed_query_candidates(prompt: str, limit: int = MAX_REVIEWED_QUERY_CANDIDATES) -> list[ReviewedQueryCandidate]:
    prompt_lower = prompt.lower()
    prompt_tokens = {token for token in tokenize_prompt(prompt_lower) if token not in PROMPT_STOPWORDS}
    candidates: list[ReviewedQueryCandidate] = []
    for query in query_registry.load_query_registry():
        query_tokens = {
            token for token in tokenize_prompt(build_query_match_text(query)) if token not in PROMPT_STOPWORDS
        }
        matched_terms = sorted(prompt_tokens & query_tokens)
        phrase_hits = [phrase for phrase in QUERY_INTENT_HINTS.get(query.name, ()) if phrase in prompt_lower]
        score = len(matched_terms) + len(phrase_hits) * 2
        if score < 2:
            continue
        candidates.append(
            ReviewedQueryCandidate(
                name=query.name,
                title=query.title,
                description=query.description,
                sql=query.sql,
                category=query.category,
                score=score,
                matched_terms=tuple(matched_terms),
            )
        )
    candidates.sort(key=lambda item: (-item.score, -len(item.matched_terms), item.title))
    return candidates[:limit]


def build_reviewed_query_context(candidates: list[ReviewedQueryCandidate]) -> str:
    if not candidates:
        return ""
    lines = ["Closest reviewed SQL patterns from this repository:"]
    for candidate in candidates[:MAX_REVIEWED_QUERY_CONTEXT]:
        matched_terms = ", ".join(candidate.matched_terms) if candidate.matched_terms else "semantic similarity"
        lines.append(f"\nPattern: {candidate.title} ({candidate.category})")
        if candidate.description:
            lines.append(f"Purpose: {candidate.description}")
        lines.append(f"Matched terms: {matched_terms}")
        lines.append("SQL pattern:")
        lines.append(candidate.sql)
    return "\n".join(lines)


def build_schema_context(conn: sqlite3.Connection) -> str:
    tables = conn.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
          AND name NOT LIKE 'sqlite_%'
        ORDER BY name
        """
    ).fetchall()
    lines = ["SQLite database schema for the pet adoption center:"]
    lines.append("\nBusiness meaning of core tables:")
    for table in tables:
        table_name = table["name"]
        description = TABLE_SEMANTICS.get(table_name)
        if description:
            lines.append(f"- {table_name}: {description}")
    for table in tables:
        table_name = table["name"]
        lines.append(f"\nTABLE {table_name}")
        for col in conn.execute(f"PRAGMA table_info({quote_identifier(table_name)})").fetchall():
            nullable = "NOT NULL" if col["notnull"] else "NULLABLE"
            pk = " PRIMARY KEY" if col["pk"] else ""
            default = f" DEFAULT {col['dflt_value']}" if col["dflt_value"] is not None else ""
            lines.append(f"- {col['name']} {col['type']} {nullable}{pk}{default}")
        foreign_keys = conn.execute(f"PRAGMA foreign_key_list({quote_identifier(table_name)})").fetchall()
        for fk in foreign_keys:
            lines.append(f"- FK {fk['from']} -> {fk['table']}.{fk['to']}")
        indexes = conn.execute(f"PRAGMA index_list({quote_identifier(table_name)})").fetchall()
        for idx in indexes:
            index_cols = conn.execute(f"PRAGMA index_info({quote_identifier(idx['name'])})").fetchall()
            cols = ", ".join(col["name"] for col in index_cols)
            unique = " UNIQUE" if idx["unique"] else ""
            lines.append(f"- INDEX{unique} {idx['name']}({cols})")

    domain_lines = build_domain_context(conn)
    if domain_lines:
        lines.append("\nKnown business domains:")
        lines.extend(domain_lines)
    lines.append(
        "\nImportant rule: generate SQLite SQL only. Use date('now', '+8 hours') for current local date logic."
    )
    return "\n".join(lines)


def quote_identifier(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'


def build_domain_context(conn: sqlite3.Connection) -> list[str]:
    domains = [
        ("PET", "status"),
        ("PET", "species"),
        ("PET", "sex"),
        ("ADOPTION_APPLICATION", "status"),
        ("APPLICANT", "housing_type"),
        ("CARE_ASSIGNMENT", "shift"),
        ("CARE_ASSIGNMENT", "task_type"),
        ("CARE_ASSIGNMENT", "status"),
        ("FOLLOW_UP", "followup_type"),
        ("FOLLOW_UP", "result_status"),
        ("MEDICAL_RECORD", "record_type"),
    ]
    lines: list[str] = []
    for table_name, column_name in domains:
        observed_values: list[str] = []
        try:
            rows = conn.execute(
                f"""
                SELECT DISTINCT {quote_identifier(column_name)} AS value
                FROM {quote_identifier(table_name)}
                WHERE {quote_identifier(column_name)} IS NOT NULL
                ORDER BY value
                """
            ).fetchall()
            observed_values = [str(row["value"]) for row in rows]
        except sqlite3.Error:
            observed_values = []
        canonical_values = list(CANONICAL_DOMAIN_VALUES.get((table_name, column_name), ()))
        values = canonical_values[:]
        for value in observed_values:
            if value not in values:
                values.append(value)
        if values:
            lines.append(f"- {table_name}.{column_name}: {', '.join(values)}")
    return lines


def try_rule_based_resolution(prompt: str, prompt_semantics: PromptSemantics) -> DirectSqlResolution | None:
    prompt_lower = prompt.lower()
    normalized_lower = prompt_semantics.normalized_prompt.lower()
    species = extract_requested_species(normalized_lower)
    housing_types = extract_requested_housing_types(normalized_lower)
    pet_id = extract_numeric_reference(normalized_lower, "pet")
    volunteer_id = extract_numeric_reference(normalized_lower, "volunteer")
    shelter_id = extract_numeric_reference(normalized_lower, "shelter")
    application_statuses = extract_requested_application_statuses(normalized_lower)

    if shelter_id is not None and contains_any_phrase(normalized_lower, ("pets in shelter", "housed in shelter", "current pet list")):
        return build_direct_resolution(
            f"""
SELECT
    pet_id,
    name,
    species,
    breed,
    sex,
    status,
    intake_date
FROM PET
WHERE shelter_id = {shelter_id}
ORDER BY date(intake_date) DESC, pet_id DESC;
""",
            f"Lists the pets currently associated with shelter {shelter_id}.",
            ("PET",),
            confidence=0.98,
            intent="shelter_pet_roster",
        )

    if "medical hold" in normalized_lower and "pet" in normalized_lower:
        return build_direct_resolution(
            """
SELECT
    p.pet_id,
    p.name,
    p.species,
    p.breed,
    p.sex,
    s.name AS shelter_name
FROM PET p
JOIN SHELTER s ON s.shelter_id = p.shelter_id
WHERE p.status = 'medical_hold'
ORDER BY p.pet_id;
""",
            "Lists pets currently on medical hold together with their shelter names.",
            ("PET", "SHELTER"),
            confidence=0.99,
            intent="medical_hold_pets",
        )

    if ("under review" in normalized_lower or "still waiting" in normalized_lower) and (
        "application" in normalized_lower or "applicant" in normalized_lower
    ):
        if "applicant" in normalized_lower:
            return build_direct_resolution(
                """
SELECT
    ap.applicant_id,
    ap.full_name AS applicant_name,
    ap.housing_type,
    a.application_id,
    a.application_date,
    p.pet_id,
    p.name AS pet_name,
    p.species
FROM ADOPTION_APPLICATION a
JOIN APPLICANT ap ON ap.applicant_id = a.applicant_id
JOIN PET p ON p.pet_id = a.pet_id
WHERE a.status = 'Under Review'
ORDER BY date(a.application_date), a.application_id;
""",
                "Lists applicants whose adoption applications are still under review.",
                ("ADOPTION_APPLICATION", "APPLICANT", "PET"),
                confidence=0.99,
                intent="waiting_applicants",
            )
        return build_direct_resolution(
            """
SELECT
    a.application_id,
    ap.full_name AS applicant_name,
    p.name AS pet_name,
    p.species,
    a.application_date,
    a.status,
    a.reviewer_name
FROM ADOPTION_APPLICATION a
JOIN APPLICANT ap ON a.applicant_id = ap.applicant_id
JOIN PET p ON a.pet_id = p.pet_id
WHERE a.status = 'Under Review'
ORDER BY date(a.application_date), a.application_id;
""",
            "Lists adoption applications that are currently under review.",
            ("ADOPTION_APPLICATION", "APPLICANT", "PET"),
            confidence=0.99,
            intent="under_review_applications",
        )

    if "vaccination" in normalized_lower and (
        "soon" in normalized_lower or "within 30 days" in normalized_lower or "due" in normalized_lower
    ):
        return build_direct_resolution(
            """
SELECT
    p.pet_id,
    p.name,
    p.species,
    v.vaccine_name,
    v.next_due_date
FROM PET p
JOIN VACCINATION v
    ON p.pet_id = v.pet_id
WHERE v.next_due_date IS NOT NULL
  AND date(v.next_due_date) >= date('now', '+8 hours')
  AND date(v.next_due_date) <= date('now', '+8 hours', '+30 day')
ORDER BY date(v.next_due_date), p.pet_id;
""",
            "Lists vaccinations due from today through the next 30 days.",
            ("PET", "VACCINATION"),
            ("Interpreted soon as the next 30 days and excluded already overdue records.",),
            confidence=0.99,
            intent="vaccinations_due_soon",
        )

    if pet_id is not None and ("health timeline" in normalized_lower or "medical history" in prompt_lower):
        return build_direct_resolution(
            f"""
SELECT
    pet_id,
    pet_name,
    species,
    breed,
    event_kind,
    event_date,
    event_title,
    event_details,
    due_or_followup_date,
    staff_name,
    notes
FROM (
    SELECT
        p.pet_id AS pet_id,
        p.name AS pet_name,
        p.species AS species,
        p.breed AS breed,
        'Vaccination' AS event_kind,
        v.vaccination_date AS event_date,
        v.vaccine_name AS event_title,
        CASE
            WHEN v.dose_no IS NULL THEN 'Dose not recorded'
            ELSE 'Dose ' || v.dose_no
        END AS event_details,
        v.next_due_date AS due_or_followup_date,
        COALESCE(v.vet_name, 'Unknown') AS staff_name,
        COALESCE(v.notes, '') AS notes
    FROM PET p
    JOIN VACCINATION v ON p.pet_id = v.pet_id

    UNION ALL

    SELECT
        p.pet_id AS pet_id,
        p.name AS pet_name,
        p.species AS species,
        p.breed AS breed,
        'Medical' AS event_kind,
        m.visit_date AS event_date,
        COALESCE(m.record_type, 'Medical visit') AS event_title,
        TRIM(
            COALESCE(m.diagnosis, '')
            || CASE WHEN m.diagnosis IS NOT NULL AND m.treatment IS NOT NULL THEN ' | ' ELSE '' END
            || COALESCE(m.treatment, '')
        ) AS event_details,
        NULL AS due_or_followup_date,
        COALESCE(m.vet_name, 'Unknown') AS staff_name,
        COALESCE(m.notes, '') AS notes
    FROM PET p
    JOIN MEDICAL_RECORD m ON p.pet_id = m.pet_id
)
WHERE pet_id = {pet_id}
ORDER BY date(event_date) DESC, event_kind, event_title;
""",
            f"Builds a full health timeline for pet {pet_id} across vaccinations and medical records.",
            ("PET", "VACCINATION", "MEDICAL_RECORD"),
            confidence=0.98,
            intent="pet_health_timeline",
        )

    if pet_id is not None and contains_any_phrase(normalized_lower, ("medically", "medical record", "medical")) and "pet" in normalized_lower:
        return build_direct_resolution(
            f"""
SELECT
    visit_date,
    record_type,
    diagnosis,
    treatment,
    vet_name,
    notes
FROM MEDICAL_RECORD
WHERE pet_id = {pet_id}
ORDER BY date(visit_date) DESC, record_id DESC;
""",
            f"Lists medical records for pet {pet_id}.",
            ("MEDICAL_RECORD",),
            confidence=0.97,
            intent="pet_medical_records",
        )

    if volunteer_id is not None and contains_any_phrase(normalized_lower, ("assignment", "schedule", "upcoming")):
        return build_direct_resolution(
            f"""
SELECT
    c.assignment_id,
    c.assignment_date,
    c.shift,
    c.task_type,
    c.status,
    p.pet_id,
    p.name AS pet_name,
    p.species
FROM CARE_ASSIGNMENT c
JOIN PET p ON c.pet_id = p.pet_id
WHERE c.volunteer_id = {volunteer_id}
ORDER BY date(c.assignment_date) DESC, c.shift, c.assignment_id DESC;
""",
            f"Lists care assignments for volunteer {volunteer_id}.",
            ("CARE_ASSIGNMENT", "PET"),
            confidence=0.98,
            intent="volunteer_schedule",
        )

    if pet_id is not None and (
        re.search(r"\bwho\b", normalized_lower) or "which volunteer" in normalized_lower
    ) and contains_any_phrase(normalized_lower, ("care", "assigned", "assignment")):
        return build_direct_resolution(
            f"""
SELECT
    c.assignment_id,
    c.assignment_date,
    c.shift,
    c.task_type,
    c.status,
    v.volunteer_id,
    v.full_name AS volunteer_name
FROM CARE_ASSIGNMENT c
JOIN VOLUNTEER v ON v.volunteer_id = c.volunteer_id
WHERE c.pet_id = {pet_id}
  AND c.status != 'Cancelled'
ORDER BY date(c.assignment_date) DESC, c.assignment_id DESC;
""",
            f"Lists non-cancelled care assignments for pet {pet_id} together with volunteer names.",
            ("CARE_ASSIGNMENT", "VOLUNTEER"),
            confidence=0.96,
            intent="pet_caregivers",
        )

    if (
        "available for adoption" in normalized_lower
        or ("available" in normalized_lower and "pet" in normalized_lower)
        or ("adopt" in normalized_lower and species is not None)
    ):
        species_filter = f" AND species = {sql_quote(species)}" if species else ""
        explanation = "Lists pets currently available for adoption."
        if species:
            explanation = f"Lists {species.lower()}s currently available for adoption."
        return build_direct_resolution(
            f"""
SELECT
    pet_id,
    name,
    species,
    breed,
    sex,
    color,
    special_needs
FROM PET
WHERE status = 'available'{species_filter}
ORDER BY name;
""",
            explanation,
            ("PET",),
            confidence=0.99,
            intent="available_pets",
        )

    occupancy_filter = "p.status IN ('available', 'reserved', 'medical_hold')"
    if contains_any_phrase(normalized_lower, ("fullest", "highest occupancy", "occupancy rate")):
        if re.search(r"\b(which shelter|fullest|highest)\b", normalized_lower):
            return build_direct_resolution(
                f"""
SELECT
    s.shelter_id,
    s.name AS shelter_name,
    s.capacity,
    COUNT(p.pet_id) AS current_pet_count,
    ROUND(COUNT(p.pet_id) * 100.0 / s.capacity, 2) AS occupancy_rate
FROM SHELTER s
LEFT JOIN PET p
    ON p.shelter_id = s.shelter_id
   AND {occupancy_filter}
GROUP BY s.shelter_id, s.name, s.capacity
ORDER BY occupancy_rate DESC, s.shelter_id
LIMIT 1;
""",
                "Finds the fullest shelter by occupancy rate using active pet statuses only.",
                ("SHELTER", "PET"),
                ("Active occupancy counts pets whose status is available, reserved, or medical_hold.",),
                confidence=0.99,
                intent="fullest_shelter",
            )
        return build_direct_resolution(
            f"""
SELECT
    s.shelter_id,
    s.name AS shelter_name,
    s.capacity,
    COUNT(p.pet_id) AS current_pet_count,
    ROUND(COUNT(p.pet_id) * 100.0 / s.capacity, 2) AS occupancy_rate
FROM SHELTER s
LEFT JOIN PET p
    ON p.shelter_id = s.shelter_id
   AND {occupancy_filter}
GROUP BY s.shelter_id, s.name, s.capacity
ORDER BY occupancy_rate DESC, s.shelter_id;
""",
            "Summarizes current shelter occupancy using active pet statuses only.",
            ("SHELTER", "PET"),
            ("Active occupancy counts pets whose status is available, reserved, or medical_hold.",),
            confidence=0.99,
            intent="shelter_occupancy",
        )

    if re.search(r"\bhow many pets\b", normalized_lower) and "shelter" in normalized_lower and contains_any_phrase(
        normalized_lower, ("care for", "currently care", "each shelter")
    ):
        return build_direct_resolution(
            f"""
SELECT
    s.shelter_id,
    s.name AS shelter_name,
    COUNT(p.pet_id) AS current_pet_count
FROM SHELTER s
LEFT JOIN PET p
    ON p.shelter_id = s.shelter_id
   AND {occupancy_filter}
GROUP BY s.shelter_id, s.name
ORDER BY current_pet_count DESC, s.shelter_id;
""",
            "Counts active pets currently cared for by each shelter.",
            ("SHELTER", "PET"),
            ("Active counts exclude adopted pets.",),
            confidence=0.99,
            intent="shelter_pet_counts",
        )

    if contains_any_phrase(normalized_lower, ("been here the longest", "longest stay", "days in shelter")):
        limit_clause = "LIMIT 1" if re.search(r"\b(which pet|what pet)\b", normalized_lower) else ""
        return build_direct_resolution(
            f"""
SELECT
    pet_id,
    name,
    species,
    breed,
    shelter_id,
    intake_date,
    CAST(julianday(date('now', '+8 hours')) - julianday(intake_date) AS INTEGER) AS days_in_shelter
FROM PET
WHERE status = 'available'
ORDER BY days_in_shelter DESC, pet_id
{limit_clause};
""",
            "Ranks available pets by shelter stay duration.",
            ("PET",),
            confidence=0.98,
            intent="long_stay_pets",
        )

    if "pet" in normalized_lower and contains_any_phrase(normalized_lower, ("oldest", "youngest")):
        order_direction = "ASC" if "oldest" in normalized_lower else "DESC"
        return build_direct_resolution(
            f"""
SELECT
    pet_id,
    name,
    species,
    estimated_birth_date
FROM PET
WHERE estimated_birth_date IS NOT NULL
  AND date(estimated_birth_date) >= date('1900-01-01')
ORDER BY estimated_birth_date {order_direction}, pet_id
LIMIT 1;
""",
            f"Finds the {'oldest' if order_direction == 'ASC' else 'youngest'} pet using estimated birth date.",
            ("PET",),
            ("Ignored implausible placeholder birth dates before 1900-01-01.",),
            confidence=0.97,
            intent="pet_age_extreme",
        )

    if "volunteer" in normalized_lower and contains_any_phrase(
        normalized_lower, ("most work", "most care tasks", "most tasks", "workload", "completed the most care tasks")
    ):
        limit_clause = "LIMIT 1" if re.search(r"\b(which volunteer|who)\b", normalized_lower) else ""
        return build_direct_resolution(
            f"""
SELECT
    v.volunteer_id,
    v.full_name,
    COUNT(c.assignment_id) AS total_assignments,
    SUM(CASE WHEN c.status = 'Completed' THEN 1 ELSE 0 END) AS completed_tasks,
    SUM(CASE WHEN c.status = 'Cancelled' THEN 1 ELSE 0 END) AS cancelled_tasks,
    SUM(CASE WHEN c.status = 'Scheduled' THEN 1 ELSE 0 END) AS scheduled_tasks
FROM VOLUNTEER v
LEFT JOIN CARE_ASSIGNMENT c
    ON v.volunteer_id = c.volunteer_id
GROUP BY v.volunteer_id, v.full_name
ORDER BY completed_tasks DESC, total_assignments DESC, v.volunteer_id
{limit_clause};
""",
            "Summarizes volunteer workload from care assignments.",
            ("VOLUNTEER", "CARE_ASSIGNMENT"),
            confidence=0.97,
            intent="volunteer_workload",
        )

    if application_statuses and "application" in normalized_lower and contains_any_phrase(
        normalized_lower, ("how many", "count", "vs")
    ):
        status_list = ", ".join(sql_quote(status) for status in application_statuses)
        return build_direct_resolution(
            f"""
SELECT
    status,
    COUNT(application_id) AS application_count
FROM ADOPTION_APPLICATION
WHERE status IN ({status_list})
GROUP BY status
ORDER BY application_count DESC, status;
""",
            "Counts adoption applications for the requested workflow statuses.",
            ("ADOPTION_APPLICATION",),
            confidence=0.98,
            intent="application_status_counts",
        )

    if contains_any_phrase(normalized_lower, ("approval rate", "approval rates")) and (
        "housing" in normalized_lower or bool(housing_types)
    ):
        housing_filter = ""
        if housing_types:
            values = ", ".join(sql_quote(value) for value in housing_types)
            housing_filter = f"WHERE ap.housing_type IN ({values})"
        return build_direct_resolution(
            f"""
SELECT
    ap.housing_type,
    COUNT(a.application_id) AS total_applications,
    SUM(CASE WHEN a.status = 'Approved' THEN 1 ELSE 0 END) AS approved_count,
    SUM(CASE WHEN a.status = 'Rejected' THEN 1 ELSE 0 END) AS rejected_count,
    ROUND(
        SUM(CASE WHEN a.status = 'Approved' THEN 1 ELSE 0 END) * 100.0
        / NULLIF(COUNT(a.application_id), 0),
        2
    ) AS approval_rate
FROM APPLICANT ap
JOIN ADOPTION_APPLICATION a
    ON ap.applicant_id = a.applicant_id
{housing_filter}
GROUP BY ap.housing_type
ORDER BY approval_rate DESC, ap.housing_type;
""",
            "Compares adoption approval rates by applicant housing type.",
            ("APPLICANT", "ADOPTION_APPLICATION"),
            confidence=0.97,
            intent="approval_rates_by_housing_type",
        )

    if contains_any_phrase(normalized_lower, ("follow-up outcome", "follow-up outcomes", "post adoption outcomes")):
        return build_direct_resolution(
            """
SELECT
    f.result_status,
    COUNT(f.followup_id) AS total_followups
FROM FOLLOW_UP f
GROUP BY f.result_status
ORDER BY total_followups DESC, f.result_status;
""",
            "Summarizes post-adoption follow-up outcomes.",
            ("FOLLOW_UP",),
            confidence=0.98,
            intent="followup_outcomes",
        )

    return None


def build_prompt_messages(
    prompt: str,
    prompt_method: str,
    schema_context: str,
    prompt_semantics: PromptSemantics | None = None,
    reviewed_candidates: list[ReviewedQueryCandidate] | None = None,
    retry_reason: str | None = None,
) -> list[dict[str, str]]:
    if prompt_method not in PROMPT_METHODS:
        raise LlmSqlError(
            HTTPStatus.BAD_REQUEST,
            f"Unsupported promptMethod '{prompt_method}'. Choose one of: {', '.join(PROMPT_METHODS)}.",
        )

    output_contract = (
        "Return only a JSON object with keys sql, explanation, tables_used, assumptions, confidence, prompt_method. "
        "The sql value must be a single SQLite SELECT query or a read-only WITH query. "
        "Never use INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, REPLACE, TRUNCATE, ATTACH, DETACH, PRAGMA, VACUUM, or REINDEX."
    )
    system = (
        "You convert pet adoption center questions into safe SQLite information-retrieval SQL. "
        "You first translate user wording into the business vocabulary of this schema. "
        "You do not modify data. You prefer clear joins, explicit aliases, readable aggregate names, and only the columns needed to answer the question. "
        "When the wording is broad but still meaningful, choose the closest conservative summary query instead of returning a placeholder message. "
        "Do not answer with a literal placeholder query such as SELECT 'Question unclear' AS message when the user has a meaningful database intent. "
        + output_contract
    )

    user_parts = [f"User question: {prompt}"]
    if prompt_semantics is not None and prompt_semantics.normalized_prompt != prompt:
        user_parts.append(f"Normalized business wording: {prompt_semantics.normalized_prompt}")
    if prompt_semantics is not None and (prompt_semantics.rewrite_notes or prompt_semantics.hints):
        semantic_lines = ["Semantic interpretation notes:"]
        semantic_lines.extend(f"- {note}" for note in [*prompt_semantics.rewrite_notes, *prompt_semantics.hints])
        user_parts.append("\n".join(semantic_lines))
    if retry_reason:
        user_parts.append(
            "\n".join(
                [
                    "Previous generation problem:",
                    retry_reason,
                    "Produce a real database query that best matches the normalized meaning of the question.",
                ]
            )
        )
    if prompt_method in {"schema_grounded", "few_shot", "self_check_repair"}:
        user_parts.append(schema_context)
        reviewed_context = build_reviewed_query_context(reviewed_candidates or [])
        if reviewed_context:
            user_parts.append(reviewed_context)
    if prompt_method in {"few_shot", "self_check_repair"}:
        user_parts.append(build_few_shot_examples())
    if prompt_method == "zero_shot":
        user_parts.append(
            "Use only the database concepts mentioned by the user. If the request is broad but meaningful, choose a conservative read-only summary query."
        )
    if prompt_method == "schema_grounded":
        user_parts.append("Use the provided schema exactly. Do not invent tables or columns.")
    if prompt_method == "few_shot":
        user_parts.append("Follow the style of the examples, but generate a query that answers the user question.")
    if prompt_method == "self_check_repair":
        user_parts.append(
            "Before returning JSON, self-check that every table and column exists in the schema, the SQL is one statement, "
            "and the query is read-only SQLite. If uncertain, simplify the query."
        )
    user_parts.append(f"Set prompt_method to {prompt_method}.")
    return [{"role": "system", "content": system}, {"role": "user", "content": "\n\n".join(user_parts)}]


def build_repair_messages(
    prompt: str,
    prompt_method: str,
    schema_context: str,
    sql: str,
    error: str,
    prompt_semantics: PromptSemantics | None = None,
    reviewed_candidates: list[ReviewedQueryCandidate] | None = None,
) -> list[dict[str, str]]:
    user_parts = [f"Original question: {prompt}", f"Prompt method: {prompt_method}"]
    if prompt_semantics is not None and prompt_semantics.normalized_prompt != prompt:
        user_parts.append(f"Normalized business wording: {prompt_semantics.normalized_prompt}")
    if prompt_semantics is not None and (prompt_semantics.rewrite_notes or prompt_semantics.hints):
        semantic_lines = ["Semantic interpretation notes:"]
        semantic_lines.extend(f"- {note}" for note in [*prompt_semantics.rewrite_notes, *prompt_semantics.hints])
        user_parts.append("\n".join(semantic_lines))
    user_parts.append(schema_context)
    reviewed_context = build_reviewed_query_context(reviewed_candidates or [])
    if reviewed_context:
        user_parts.append(reviewed_context)
    user_parts.extend(
        [
            f"Failed SQL:\n{sql}",
            f"Failure reason:\n{error}",
            "Return a corrected safe SQLite query. Do not use PRAGMA or any write/DDL command. Do not return a placeholder message query.",
        ]
    )
    return [
        {
            "role": "system",
            "content": (
                "Repair or replace a failed SQLite SELECT query. Return only JSON with keys sql, explanation, "
                "tables_used, assumptions, confidence, prompt_method. The repaired SQL must be one read-only SELECT or WITH query."
            ),
        },
        {
            "role": "user",
            "content": "\n\n".join(user_parts),
        },
    ]


def build_few_shot_examples() -> str:
    return """Representative safe SQLite examples:

Question intent: list currently available pets with shelter names.
SQL:
SELECT
    p.pet_id,
    p.name,
    p.species,
    p.status,
    s.name AS shelter_name
FROM PET p
JOIN SHELTER s ON p.shelter_id = s.shelter_id
WHERE p.status = 'available'
ORDER BY p.pet_id;

Question intent: summarize active pet occupancy by shelter.
SQL:
SELECT
    s.shelter_id,
    s.name AS shelter_name,
    s.capacity,
    COUNT(p.pet_id) AS active_pet_count,
    ROUND(COUNT(p.pet_id) * 100.0 / s.capacity, 2) AS occupancy_rate
FROM SHELTER s
LEFT JOIN PET p
    ON p.shelter_id = s.shelter_id
   AND p.status IN ('available', 'reserved', 'medical_hold')
GROUP BY s.shelter_id, s.name, s.capacity
ORDER BY occupancy_rate DESC;

Question intent: count applications by review status.
SQL:
SELECT
    status,
    COUNT(*) AS application_count
FROM ADOPTION_APPLICATION
GROUP BY status
ORDER BY application_count DESC;

Question intent: list vaccinations due soon in the next 30 days, excluding already overdue records.
SQL:
SELECT
    p.pet_id,
    p.name,
    p.species,
    v.vaccine_name,
    v.next_due_date
FROM PET p
JOIN VACCINATION v
    ON p.pet_id = v.pet_id
WHERE v.next_due_date IS NOT NULL
  AND date(v.next_due_date) >= date('now', '+8 hours')
  AND date(v.next_due_date) <= date('now', '+8 hours', '+30 day')
ORDER BY date(v.next_due_date), p.pet_id;

Question intent: find the oldest pet by age, not by shelter stay.
SQL:
SELECT
    p.pet_id,
    p.name,
    p.species,
    p.estimated_birth_date
FROM PET p
WHERE p.estimated_birth_date IS NOT NULL
ORDER BY p.estimated_birth_date ASC, p.pet_id
LIMIT 1;

Question intent: summarize adoption performance conservatively.
SQL:
SELECT
    COUNT(a.application_id) AS total_applications,
    SUM(CASE WHEN a.status = 'Approved' THEN 1 ELSE 0 END) AS approved_applications,
    SUM(CASE WHEN a.status = 'Rejected' THEN 1 ELSE 0 END) AS rejected_applications,
    COUNT(ar.adoption_id) AS completed_adoptions,
    ROUND(
        COUNT(ar.adoption_id) * 100.0 / NULLIF(COUNT(a.application_id), 0),
        2
    ) AS adoption_success_rate
FROM ADOPTION_APPLICATION a
LEFT JOIN ADOPTION_RECORD ar
    ON ar.application_id = a.application_id;"""


def parse_llm_json(raw: str, prompt_method: str) -> dict[str, Any]:
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise LlmSqlError(
            HTTPStatus.BAD_GATEWAY,
            "GLM returned non-JSON output.",
            {"rawResponse": raw[:1000], "jsonValid": False},
        ) from exc
    if not isinstance(data, dict):
        raise LlmSqlError(HTTPStatus.BAD_GATEWAY, "GLM JSON output must be an object.", {"jsonValid": False})
    sql = data.get("sql")
    if not isinstance(sql, str) or not sql.strip():
        raise LlmSqlError(HTTPStatus.BAD_GATEWAY, "GLM JSON output is missing a non-empty sql field.", {"jsonValid": True})
    data.setdefault("explanation", "")
    data.setdefault("tables_used", [])
    data.setdefault("assumptions", [])
    data.setdefault("confidence", None)
    data["prompt_method"] = data.get("prompt_method") or prompt_method
    return data


def strip_sql_comments(sql: str) -> str:
    result: list[str] = []
    i = 0
    in_single = False
    in_double = False
    while i < len(sql):
        ch = sql[i]
        nxt = sql[i + 1] if i + 1 < len(sql) else ""
        if in_single:
            result.append(ch)
            if ch == "'" and nxt == "'":
                result.append(nxt)
                i += 2
                continue
            if ch == "'":
                in_single = False
            i += 1
            continue
        if in_double:
            result.append(ch)
            if ch == '"' and nxt == '"':
                result.append(nxt)
                i += 2
                continue
            if ch == '"':
                in_double = False
            i += 1
            continue
        if ch == "'":
            in_single = True
            result.append(ch)
            i += 1
            continue
        if ch == '"':
            in_double = True
            result.append(ch)
            i += 1
            continue
        if ch == "-" and nxt == "-":
            i += 2
            while i < len(sql) and sql[i] not in "\r\n":
                i += 1
            result.append(" ")
            continue
        if ch == "/" and nxt == "*":
            i += 2
            while i + 1 < len(sql) and not (sql[i] == "*" and sql[i + 1] == "/"):
                i += 1
            i += 2
            result.append(" ")
            continue
        result.append(ch)
        i += 1
    return "".join(result)


def mask_sql_strings(sql: str) -> str:
    result: list[str] = []
    i = 0
    in_single = False
    in_double = False
    while i < len(sql):
        ch = sql[i]
        nxt = sql[i + 1] if i + 1 < len(sql) else ""
        if in_single:
            result.append(" ")
            if ch == "'" and nxt == "'":
                result.append(" ")
                i += 2
                continue
            if ch == "'":
                in_single = False
            i += 1
            continue
        if in_double:
            result.append(" ")
            if ch == '"' and nxt == '"':
                result.append(" ")
                i += 2
                continue
            if ch == '"':
                in_double = False
            i += 1
            continue
        if ch == "'":
            in_single = True
            result.append(" ")
        elif ch == '"':
            in_double = True
            result.append(" ")
        else:
            result.append(ch)
        i += 1
    return "".join(result)


def split_sql_statements(sql: str) -> list[str]:
    statements: list[str] = []
    current: list[str] = []
    in_single = False
    in_double = False
    i = 0
    while i < len(sql):
        ch = sql[i]
        nxt = sql[i + 1] if i + 1 < len(sql) else ""
        if in_single:
            current.append(ch)
            if ch == "'" and nxt == "'":
                current.append(nxt)
                i += 2
                continue
            if ch == "'":
                in_single = False
            i += 1
            continue
        if in_double:
            current.append(ch)
            if ch == '"' and nxt == '"':
                current.append(nxt)
                i += 2
                continue
            if ch == '"':
                in_double = False
            i += 1
            continue
        if ch == "'":
            in_single = True
            current.append(ch)
        elif ch == '"':
            in_double = True
            current.append(ch)
        elif ch == ";":
            statements.append("".join(current).strip())
            current = []
        else:
            current.append(ch)
        i += 1
    tail = "".join(current).strip()
    if tail:
        statements.append(tail)
    return [statement for statement in statements if statement]


def is_placeholder_literal_query(sql: str) -> bool:
    cleaned = strip_sql_comments(sql).strip()
    statements = split_sql_statements(cleaned)
    if len(statements) != 1:
        return False
    statement = statements[0].strip()
    if re.search(r"\bFROM\b", mask_sql_strings(statement), flags=re.IGNORECASE):
        return False
    return bool(
        re.match(
            r"""^\s*SELECT\s+(?:'[^']*'|"[^"]*"|\d+|NULL)(?:\s+AS\s+[A-Za-z_][A-Za-z0-9_]*)?\s*$""",
            statement,
            flags=re.IGNORECASE | re.DOTALL,
        )
    )


def semantic_failure_reason(prompt: str, sql: str, llm_output: dict[str, Any]) -> str | None:
    if not prompt_has_meaningful_content(prompt):
        return None
    explanation = str(llm_output.get("explanation", "")).lower()
    if is_placeholder_literal_query(sql):
        return "The previous SQL only returned a literal placeholder message instead of querying database tables."
    if any(pattern in explanation for pattern in SEMANTIC_FAILURE_EXPLANATION_PATTERNS):
        return "The previous explanation treated a meaningful prompt as unclear or incomplete."
    return None


def validate_generated_sql(sql: str) -> dict[str, Any]:
    cleaned = strip_sql_comments(sql).strip()
    statements = split_sql_statements(cleaned)
    if len(statements) != 1:
        return validation_result(False, "Generated SQL must contain exactly one statement.")
    statement = statements[0].strip()
    if not statement:
        return validation_result(False, "Generated SQL is empty after removing comments.")

    masked = mask_sql_strings(statement)
    for keyword in BLOCKED_SQL_KEYWORDS:
        if re.search(rf"\b{keyword}\b", masked, flags=re.IGNORECASE):
            return validation_result(False, f"Blocked SQL keyword is not allowed: {keyword}.")

    if not re.match(r"^\s*(SELECT|WITH)\b", statement, flags=re.IGNORECASE):
        return validation_result(False, "Generated SQL must start with SELECT or WITH.")

    return validation_result(True, "SQL passed static read-only checks.", normalized_sql=statement)


def validation_result(safe: bool, reason: str, normalized_sql: str | None = None) -> dict[str, Any]:
    result = {
        "safe": safe,
        "readOnly": safe,
        "reason": reason,
        "checkedBy": ["comment_strip", "single_statement", "blocked_keyword_scan", "select_only"],
    }
    if normalized_sql is not None:
        result["normalizedSql"] = normalized_sql
    return result


def readonly_db_uri(db_path: Path) -> str:
    return f"file:{quote(str(db_path), safe='/:')}?mode=ro"


def install_readonly_authorizer(conn: sqlite3.Connection) -> None:
    allowed = {sqlite3.SQLITE_SELECT, sqlite3.SQLITE_READ, sqlite3.SQLITE_FUNCTION}

    def authorizer(action: int, arg1: str | None, arg2: str | None, db_name: str | None, source: str | None) -> int:
        return sqlite3.SQLITE_OK if action in allowed else sqlite3.SQLITE_DENY

    conn.set_authorizer(authorizer)


def install_progress_guard(conn: sqlite3.Connection, max_callbacks: int = 100000) -> None:
    counter = {"count": 0}

    def progress() -> int:
        counter["count"] += 1
        return 1 if counter["count"] > max_callbacks else 0

    conn.set_progress_handler(progress, 1000)


def execute_generated_select(db_path: Path, sql: str, max_rows: int = MAX_RESULT_ROWS) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    validation = validate_generated_sql(sql)
    if not validation["safe"]:
        raise LlmSqlError(
            HTTPStatus.BAD_REQUEST,
            validation["reason"],
            {"validation": validation, "generatedSql": sql},
        )

    normalized_sql = validation["normalizedSql"]
    try:
        conn = sqlite3.connect(readonly_db_uri(db_path), uri=True, timeout=10)
        conn.row_factory = sqlite3.Row
        install_readonly_authorizer(conn)
        install_progress_guard(conn)
        conn.execute(f"EXPLAIN QUERY PLAN {normalized_sql}").fetchall()
        cursor = conn.execute(normalized_sql)
        rows = [dict(row) for row in cursor.fetchmany(max_rows + 1)]
    except sqlite3.Error as exc:
        raise LlmSqlError(
            HTTPStatus.UNPROCESSABLE_ENTITY,
            f"Generated SQL failed SQLite validation: {exc}",
            {"validation": validation, "generatedSql": sql, "sqliteError": str(exc)},
        ) from exc
    finally:
        try:
            conn.close()
        except UnboundLocalError:
            pass

    if len(rows) > max_rows:
        rows = rows[:max_rows]
        validation["truncated"] = True
    else:
        validation["truncated"] = False
    validation["checkedBy"] = [*validation["checkedBy"], "sqlite_authorizer", "explain_query_plan", "progress_guard"]
    return rows, validation


def run_prompt_to_sql(
    conn: sqlite3.Connection,
    payload: dict[str, Any],
    db_path: Path,
    client: ChatClient | None = None,
) -> dict[str, Any]:
    prompt = normalize_prompt_whitespace((payload.get("prompt") or ""))
    if not prompt:
        raise LlmSqlError(HTTPStatus.BAD_REQUEST, "Prompt is required.")
    prompt, read_only_notes = extract_read_only_subprompt(prompt)
    prompt_semantics = merge_prompt_semantics(analyze_prompt_semantics(prompt), read_only_notes)
    if not prompt_semantics.meaningful:
        raise LlmSqlError(
            HTTPStatus.BAD_REQUEST,
            "Prompt needs more detail. Ask about pets, shelters, applications, volunteers, vaccinations, medical history, or adoptions.",
        )
    prompt_method = payload.get("promptMethod") or "schema_grounded"
    if prompt_method not in PROMPT_METHODS:
        raise LlmSqlError(
            HTTPStatus.BAD_REQUEST,
            f"Unsupported promptMethod '{prompt_method}'. Choose one of: {', '.join(PROMPT_METHODS)}.",
        )
    execute = bool(payload.get("execute", True))
    reviewed_candidates = find_reviewed_query_candidates(prompt_semantics.normalized_prompt)
    direct_resolution = None
    if client is None and prompt_method == "schema_grounded":
        direct_resolution = try_rule_based_resolution(prompt, prompt_semantics)
    if direct_resolution is not None:
        rows: list[dict[str, Any]] = []
        validation = validate_generated_sql(direct_resolution.sql)
        if not validation["safe"]:
            raise LlmSqlError(
                HTTPStatus.BAD_REQUEST,
                validation["reason"],
                {"validation": validation, "generatedSql": direct_resolution.sql},
            )
        if execute:
            rows, validation = execute_generated_select(db_path, direct_resolution.sql)
        return {
            "provider": "assistant-local",
            "model": "rule-based",
            "resolutionStrategy": direct_resolution.strategy,
            "matchedIntent": direct_resolution.intent,
            "prompt": prompt,
            "normalizedPrompt": prompt_semantics.normalized_prompt,
            "promptMethod": prompt_method,
            "generatedSql": direct_resolution.sql,
            "explanation": direct_resolution.explanation,
            "tablesUsed": list(direct_resolution.tables_used),
            "assumptions": list(direct_resolution.assumptions),
            "confidence": direct_resolution.confidence,
            "semanticNotes": [*prompt_semantics.rewrite_notes, *prompt_semantics.hints],
            "reviewedQueryMatches": [
                {
                    "name": candidate.name,
                    "title": candidate.title,
                    "category": candidate.category,
                    "score": candidate.score,
                    "matchedTerms": list(candidate.matched_terms),
                }
                for candidate in reviewed_candidates
            ],
            "validation": validation,
            "rowCount": len(rows),
            "rows": rows,
            "repairAttempts": 0,
            "semanticRetries": 0,
        }

    config = LlmConfig.from_env()
    chat_client = client or GlmChatClient(config)
    schema_context = build_schema_context(conn)
    messages = build_prompt_messages(
        prompt,
        prompt_method,
        schema_context,
        prompt_semantics=prompt_semantics,
        reviewed_candidates=reviewed_candidates,
    )
    raw = chat_client.complete_json(messages, {"type": "json_object"})
    llm_output = parse_llm_json(raw, prompt_method)
    sql = llm_output["sql"]
    repair_attempts = 0
    semantic_retries = 0

    retry_reason = semantic_failure_reason(prompt_semantics.normalized_prompt, sql, llm_output)
    if retry_reason:
        repair_attempts += 1
        semantic_retries += 1
        repaired_raw = chat_client.complete_json(
            build_prompt_messages(
                prompt,
                prompt_method,
                schema_context,
                prompt_semantics=prompt_semantics,
                reviewed_candidates=reviewed_candidates,
                retry_reason=retry_reason,
            ),
            {"type": "json_object"},
        )
        llm_output = parse_llm_json(repaired_raw, prompt_method)
        sql = llm_output["sql"]
        retry_reason = semantic_failure_reason(prompt_semantics.normalized_prompt, sql, llm_output)
        if retry_reason:
            raise LlmSqlError(
                HTTPStatus.BAD_GATEWAY,
                "GLM could not ground the prompt into a meaningful database query.",
                {
                    "generatedSql": sql,
                    "semanticIssue": retry_reason,
                    "normalizedPrompt": prompt_semantics.normalized_prompt,
                },
            )

    validation = validate_generated_sql(sql)
    if not validation["safe"]:
        raise LlmSqlError(
            HTTPStatus.BAD_REQUEST,
            validation["reason"],
            {"validation": validation, "generatedSql": sql},
        )

    rows: list[dict[str, Any]] = []
    if execute:
        try:
            rows, validation = execute_generated_select(db_path, sql)
        except LlmSqlError as exc:
            if exc.status == HTTPStatus.BAD_REQUEST:
                raise
            repair_attempts += 1
            repair_messages = build_repair_messages(
                prompt,
                prompt_method,
                schema_context,
                sql,
                exc.message,
                prompt_semantics=prompt_semantics,
                reviewed_candidates=reviewed_candidates,
            )
            repaired_raw = chat_client.complete_json(repair_messages, {"type": "json_object"})
            llm_output = parse_llm_json(repaired_raw, prompt_method)
            sql = llm_output["sql"]
            repaired_issue = semantic_failure_reason(prompt_semantics.normalized_prompt, sql, llm_output)
            if repaired_issue:
                raise LlmSqlError(
                    HTTPStatus.BAD_GATEWAY,
                    "GLM repair attempt did not produce a meaningful database query.",
                    {
                        "generatedSql": sql,
                        "semanticIssue": repaired_issue,
                        "normalizedPrompt": prompt_semantics.normalized_prompt,
                    },
                )
            rows, validation = execute_generated_select(db_path, sql)

    return {
        "provider": "zhipu-glm",
        "model": config.model,
        "resolutionStrategy": "glm_generated",
        "matchedIntent": None,
        "prompt": prompt,
        "normalizedPrompt": prompt_semantics.normalized_prompt,
        "promptMethod": prompt_method,
        "generatedSql": sql,
        "explanation": llm_output.get("explanation", ""),
        "tablesUsed": llm_output.get("tables_used", []),
        "assumptions": llm_output.get("assumptions", []),
        "confidence": llm_output.get("confidence"),
        "semanticNotes": [*prompt_semantics.rewrite_notes, *prompt_semantics.hints],
        "reviewedQueryMatches": [
            {
                "name": candidate.name,
                "title": candidate.title,
                "category": candidate.category,
                "score": candidate.score,
                "matchedTerms": list(candidate.matched_terms),
            }
            for candidate in reviewed_candidates
        ],
        "validation": validation,
        "rowCount": len(rows),
        "rows": rows,
        "repairAttempts": repair_attempts,
        "semanticRetries": semantic_retries,
    }


import json
import os
import sqlite3
import sys
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient


ROOT_DIR = Path(__file__).resolve().parents[2]

from backend.app.main import app as fastapi_app
from backend.app.services import llm_sql_assistant
from backend.app.services import query_registry
from backend.app.services import pawtrack_service as web_server


class FakeGlmClient:
    def __init__(self, *responses: str):
        self.responses = list(responses)
        self.calls: list[list[dict[str, str]]] = []

    def complete_json(self, messages: list[dict[str, str]], response_format: dict[str, str] | None = None) -> str:
        self.calls.append(messages)
        if not self.responses:
            raise AssertionError("FakeGlmClient has no response left.")
        return self.responses.pop(0)


class DatabaseFixtureMixin:
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.original_db_path = web_server.DB_PATH
        self.db_path = Path(self.temp_dir.name) / "pet_database_test.db"
        web_server.DB_PATH = self.db_path
        web_server.initialize_database(reset=True)

    def tearDown(self) -> None:
        web_server.DB_PATH = self.original_db_path
        self.temp_dir.cleanup()

    def connect(self) -> sqlite3.Connection:
        return web_server.connect()

    def find_open_application_pair(self) -> tuple[int, int]:
        with closing(self.connect()) as conn:
            row = conn.execute(
                """
                SELECT ap.applicant_id, p.pet_id
                FROM APPLICANT ap
                CROSS JOIN PET p
                WHERE p.status = 'available'
                  AND NOT EXISTS (
                      SELECT 1
                      FROM ADOPTION_APPLICATION a
                      WHERE a.applicant_id = ap.applicant_id
                        AND a.pet_id = p.pet_id
                  )
                ORDER BY p.pet_id, ap.applicant_id
                LIMIT 1
                """
            ).fetchone()
        self.assertIsNotNone(row, "Expected at least one applicant/pet pair for a new application.")
        return int(row["applicant_id"]), int(row["pet_id"])


class InitializationTests(DatabaseFixtureMixin, unittest.TestCase):
    def test_initialization_builds_indexes_and_clean_audit(self) -> None:
        expected_indexes = {
            "idx_pet_shelter_id",
            "idx_pet_status",
            "idx_pet_intake_date",
            "idx_vaccination_pet_id",
            "idx_vaccination_next_due_date",
            "idx_medical_record_pet_id",
            "idx_adoption_application_applicant_id",
            "idx_adoption_application_status",
            "idx_adoption_application_pet_id",
            "idx_care_assignment_volunteer_id",
            "idx_care_assignment_volunteer_date",
            "idx_follow_up_adoption_id",
            "idx_adoption_record_application_id",
        }
        with closing(self.connect()) as conn:
            actual_indexes = {
                row["name"]
                for row in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'index' AND name NOT LIKE 'sqlite_%'"
                ).fetchall()
            }

        self.assertTrue(expected_indexes.issubset(actual_indexes))

    def test_dashboard_recent_activity_covers_more_event_types_and_timezone(self) -> None:
        with closing(self.connect()) as conn:
            baseline_dashboard = web_server.fetch_dashboard(conn)
            baseline_event_types = {activity["eventType"] for activity in baseline_dashboard["activities"]}

            applicant_payload = {
                "name": "Recent Activity Applicant",
                "phone": "555-7777",
                "email": "recent.activity@example.com",
                "address": "88 Test Street",
                "housingType": "Townhouse",
                "hasPetExperience": True,
                "createdAt": web_server.local_today_iso(),
            }
            web_server.create_resource(conn, "applicants", applicant_payload)

            pet_row = conn.execute(
                "SELECT pet_id FROM PET WHERE date(intake_date) <= date(?) ORDER BY pet_id LIMIT 1",
                (web_server.local_today_iso(),),
            ).fetchone()
            self.assertIsNotNone(pet_row)
            pet_id = int(pet_row["pet_id"])

            web_server.create_resource(
                conn,
                "medical-records",
                {
                    "petId": pet_id,
                    "date": web_server.local_today_iso(),
                    "type": "Check-up",
                    "diagnosis": "Recent dashboard test",
                    "treatment": "Observation",
                    "vet": "Dr. Recent",
                    "notes": "Medical activity regression test",
                },
            )
            web_server.create_resource(
                conn,
                "vaccinations",
                {
                    "petId": pet_id,
                    "vaccine": "Recent Test Vaccine",
                    "doseNo": 1,
                    "vaccinationDate": web_server.local_today_iso(),
                    "dueDate": (web_server.local_today() + web_server.timedelta(days=15)).isoformat(),
                    "vet": "Dr. Recent",
                    "notes": "Vaccination activity regression test",
                },
            )

            dashboard = web_server.fetch_dashboard(conn)

        event_types = {activity["eventType"] for activity in dashboard["activities"]}
        self.assertEqual(dashboard["timezone"], web_server.APP_TIMEZONE_NAME)
        self.assertGreater(len(baseline_dashboard["activities"]), 12)
        self.assertTrue({"applicant", "volunteer", "medical", "vaccination"}.issubset(baseline_event_types))
        self.assertTrue({"applicant", "medical", "vaccination"}.issubset(event_types))


class ConstraintTests(DatabaseFixtureMixin, unittest.TestCase):
    def test_invalid_pet_status_is_rejected_by_schema(self) -> None:
        with closing(self.connect()) as conn:
            with self.assertRaises(sqlite3.IntegrityError):
                conn.execute(
                    """
                    INSERT INTO PET (
                        pet_id, shelter_id, name, species, breed, sex, color,
                        estimated_birth_date, intake_date, status, is_sterilized, special_needs
                    )
                    VALUES (999, 1, 'Test', 'Dog', 'Mix', 'Male', 'Brown',
                            '2025-01-01', '2025-02-01', 'flying', 0, NULL)
                    """
                )

    def test_duplicate_adoption_record_application_id_is_rejected_by_schema(self) -> None:
        with closing(self.connect()) as conn:
            existing = conn.execute(
                "SELECT application_id FROM ADOPTION_RECORD ORDER BY adoption_id LIMIT 1"
            ).fetchone()
            self.assertIsNotNone(existing)
            with self.assertRaises(sqlite3.IntegrityError):
                conn.execute(
                    """
                    INSERT INTO ADOPTION_RECORD (
                        adoption_id, application_id, adoption_date, final_adoption_fee, handover_note
                    )
                    VALUES (?, ?, '2026-04-23', 120.0, 'Duplicate test')
                    """,
                    (999, existing["application_id"]),
                )

    def test_cross_shelter_care_assignment_is_rejected(self) -> None:
        with closing(self.connect()) as conn:
            row = conn.execute(
                """
                SELECT v.volunteer_id, p.pet_id
                FROM VOLUNTEER v
                JOIN PET p ON v.shelter_id != p.shelter_id
                WHERE date(p.intake_date) <= date(?)
                  AND (v.join_date IS NULL OR date(v.join_date) <= date(?))
                LIMIT 1
                """,
                (web_server.local_today_iso(), web_server.local_today_iso()),
            ).fetchone()
            self.assertIsNotNone(row)
            with self.assertRaises(web_server.ApiError):
                web_server.create_resource(
                    conn,
                    "care-assignments",
                    {
                        "volunteerId": row["volunteer_id"],
                        "petId": row["pet_id"],
                        "date": web_server.local_today_iso(),
                        "shift": "Morning",
                        "task": "Cleaning",
                        "status": "Scheduled",
                        "notes": "Cross-shelter should fail",
                    },
                )

    def test_follow_up_before_adoption_is_rejected(self) -> None:
        with closing(self.connect()) as conn:
            row = conn.execute(
                "SELECT adoption_id, adoption_date FROM ADOPTION_RECORD ORDER BY adoption_id LIMIT 1"
            ).fetchone()
            self.assertIsNotNone(row)
            invalid_date = (web_server.db_date(row["adoption_date"]) - web_server.timedelta(days=1)).isoformat()
            with self.assertRaises(web_server.ApiError):
                web_server.create_follow_up(
                    conn,
                    {
                        "adoptionId": row["adoption_id"],
                        "followupDate": invalid_date,
                        "followupType": "Phone Check",
                        "petCondition": "Invalid timing",
                        "adopterFeedback": "Invalid timing",
                        "resultStatus": "Good",
                        "staffNote": "Should be rejected",
                    },
                )

    def test_upcoming_vaccinations_exclude_past_due_records(self) -> None:
        with closing(self.connect()) as conn:
            pet = conn.execute(
                "SELECT pet_id, intake_date FROM PET WHERE date(intake_date) <= date(?) ORDER BY pet_id LIMIT 1",
                (web_server.local_today_iso(),),
            ).fetchone()
            self.assertIsNotNone(pet)
            intake = web_server.db_date(pet["intake_date"])
            vaccination_date = max(intake, web_server.local_today() - web_server.timedelta(days=40))
            past_due = web_server.local_today() - web_server.timedelta(days=1)
            web_server.create_resource(
                conn,
                "vaccinations",
                {
                    "petId": pet["pet_id"],
                    "vaccine": "Past Due Regression",
                    "doseNo": 1,
                    "vaccinationDate": vaccination_date.isoformat(),
                    "dueDate": past_due.isoformat(),
                    "vet": "Dr. Test",
                    "notes": "Should not appear in upcoming list",
                },
            )
            upcoming = web_server.fetch_vaccinations(conn, upcoming_only=True)

        self.assertFalse(any(item["vaccine"] == "Past Due Regression" for item in upcoming))


class QueryRegistryTests(DatabaseFixtureMixin, unittest.TestCase):
    def test_official_queries_are_read_only_and_runnable_in_sqlite(self) -> None:
        queries = query_registry.load_query_registry(ROOT_DIR / "backend" / "app" / "db" / "queries")
        self.assertEqual(len(queries), 12)
        self.assertTrue(all(query_registry.is_read_only_query(query) for query in queries))
        self.assertFalse(
            any(keyword in query.sql.upper() for query in queries for keyword in ("INSERT ", "UPDATE ", "DELETE "))
        )

        with closing(self.connect()) as conn:
            for query in queries:
                rows = [dict(row) for row in conn.execute(query.sql).fetchall()]
                self.assertIsInstance(rows, list, query.name)

    def test_glm_generated_query_executes_after_validation_with_fake_client(self) -> None:
        fake = FakeGlmClient(
            json.dumps(
                {
                    "sql": "SELECT shelter_id, name, capacity FROM SHELTER ORDER BY shelter_id",
                    "explanation": "List shelters for inspection.",
                    "tables_used": ["SHELTER"],
                    "assumptions": [],
                    "confidence": 0.95,
                    "prompt_method": "schema_grounded",
                }
            )
        )
        with closing(self.connect()) as conn:
            result = web_server.run_llm_generate_query(
                conn,
                {"prompt": "Show shelters", "promptMethod": "schema_grounded", "execute": True},
                client=fake,
            )

        self.assertTrue(result["validation"]["safe"])
        self.assertEqual(result["promptMethod"], "schema_grounded")
        self.assertEqual(result["rowCount"], 3)
        self.assertTrue(result["generatedSql"].lstrip().upper().startswith("SELECT"))
        self.assertEqual(result["semanticRetries"], 0)

    def test_glm_generated_query_rejects_unsafe_sql(self) -> None:
        dangerous_sql = [
            "DELETE FROM ADOPTION_APPLICATION",
            "SELECT * FROM PET; DROP TABLE PET;",
            "PRAGMA table_info(PET)",
            "-- hide the next command\nDELETE FROM PET",
        ]
        with closing(self.connect()) as conn:
            for sql in dangerous_sql:
                with self.subTest(sql=sql):
                    fake = FakeGlmClient(
                        json.dumps(
                            {
                                "sql": sql,
                                "explanation": "Unsafe request.",
                                "tables_used": [],
                                "assumptions": [],
                                "confidence": 0.1,
                                "prompt_method": "schema_grounded",
                            }
                        )
                    )
                    with self.assertRaises(web_server.ApiError) as ctx:
                        web_server.run_llm_generate_query(
                            conn,
                            {"prompt": "unsafe", "promptMethod": "schema_grounded"},
                            client=fake,
                        )
                    self.assertEqual(ctx.exception.status, web_server.HTTPStatus.BAD_REQUEST)
                    self.assertFalse(ctx.exception.payload["validation"]["safe"])

    def test_glm_generated_query_reports_non_json_output(self) -> None:
        fake = FakeGlmClient("SELECT * FROM PET")
        with closing(self.connect()) as conn:
            with self.assertRaises(web_server.ApiError) as ctx:
                web_server.run_llm_generate_query(
                    conn,
                    {"prompt": "show pets", "promptMethod": "schema_grounded"},
                    client=fake,
                )

        self.assertEqual(ctx.exception.status, web_server.HTTPStatus.BAD_GATEWAY)
        self.assertFalse(ctx.exception.payload["jsonValid"])

    def test_meaningful_prompt_placeholder_triggers_semantic_retry(self) -> None:
        fake = FakeGlmClient(
            json.dumps(
                {
                    "sql": "SELECT 'Question unclear' AS message",
                    "explanation": "The question appears unclear.",
                    "tables_used": [],
                    "assumptions": [],
                    "confidence": 0.1,
                    "prompt_method": "schema_grounded",
                }
            ),
            json.dumps(
                {
                    "sql": "SELECT pet_id, name FROM PET ORDER BY estimated_birth_date ASC LIMIT 1",
                    "explanation": "Retry grounded the question to the PET table.",
                    "tables_used": ["PET"],
                    "assumptions": ["Oldest uses estimated_birth_date."],
                    "confidence": 0.88,
                    "prompt_method": "schema_grounded",
                }
            ),
        )
        with closing(self.connect()) as conn:
            result = web_server.run_llm_generate_query(
                conn,
                {"prompt": "Which animal is the oldest", "promptMethod": "schema_grounded", "execute": True},
                client=fake,
            )

        self.assertEqual(result["repairAttempts"], 1)
        self.assertEqual(result["semanticRetries"], 1)
        self.assertEqual(len(fake.calls), 2)
        self.assertEqual(result["normalizedPrompt"], "Which pet is the oldest")

    def test_schema_grounded_prompt_includes_semantic_grounding_context(self) -> None:
        fake = FakeGlmClient(
            json.dumps(
                {
                    "sql": "SELECT shelter_id, name, capacity FROM SHELTER ORDER BY shelter_id",
                    "explanation": "List shelters.",
                    "tables_used": ["SHELTER"],
                    "assumptions": [],
                    "confidence": 0.9,
                    "prompt_method": "schema_grounded",
                }
            )
        )
        with closing(self.connect()) as conn:
            web_server.run_llm_generate_query(
                conn,
                {"prompt": "How full is each shelter?", "promptMethod": "schema_grounded", "execute": False},
                client=fake,
            )

        prompt_text = fake.calls[0][1]["content"]
        self.assertIn("Semantic interpretation notes:", prompt_text)
        self.assertIn("Closest reviewed SQL patterns from this repository:", prompt_text)
        self.assertIn("Analyze current occupancy of each shelter", prompt_text)
        self.assertIn("available, reserved, or medical_hold", prompt_text)

    def test_analyze_prompt_semantics_normalizes_common_phrasings(self) -> None:
        occupancy = llm_sql_assistant.analyze_prompt_semantics("How full is each shelter?")
        self.assertEqual(occupancy.normalized_prompt, "what is the occupancy rate of each shelter?")
        self.assertTrue(any("occupancy" in note.lower() for note in occupancy.rewrite_notes))
        self.assertTrue(any("available, reserved, or medical_hold" in hint for hint in occupancy.hints))

        vaccinations = llm_sql_assistant.analyze_prompt_semantics("Which pets need shots soon?")
        self.assertEqual(vaccinations.normalized_prompt, "Which pets need vaccinations soon?")
        self.assertTrue(any("vaccinations" in note.lower() for note in vaccinations.rewrite_notes))
        self.assertTrue(any("today through the next 30 days" in hint for hint in vaccinations.hints))

    def test_extract_read_only_subprompt_keeps_safe_query_clause(self) -> None:
        sanitized, notes = llm_sql_assistant.extract_read_only_subprompt(
            "Delete rejected applications and then show available pets."
        )

        self.assertEqual(sanitized, "show available pets.")
        self.assertTrue(notes)

    def test_build_domain_context_includes_canonical_values_even_if_sparse(self) -> None:
        with closing(self.connect()) as conn:
            lines = llm_sql_assistant.build_domain_context(conn)

        joined = "\n".join(lines)
        self.assertIn("PET.status: available, reserved, adopted, medical_hold", joined)
        self.assertIn("ADOPTION_APPLICATION.status: Under Review, Approved, Rejected", joined)
        self.assertIn("APPLICANT.housing_type: Apartment, Condo, House, Townhouse", joined)
        self.assertIn("Shared housing", joined)

    def test_find_reviewed_query_candidates_matches_common_filtered_prompt(self) -> None:
        candidates = llm_sql_assistant.find_reviewed_query_candidates("Show available dogs")

        self.assertTrue(candidates)
        self.assertEqual(candidates[0].name, "view_all_pets_that_are_currently_available_for_adoption")
        self.assertIn("available", candidates[0].matched_terms)

    def test_schema_grounded_rule_based_resolution_works_without_glm_config(self) -> None:
        old_env_path = llm_sql_assistant.ENV_PATH
        old_zai = os.environ.pop("ZAI_API_KEY", None)
        old_glm = os.environ.pop("GLM_API_KEY", None)
        llm_sql_assistant.ENV_PATH = Path(self.temp_dir.name) / "missing.env"
        try:
            with closing(self.connect()) as conn:
                result = web_server.run_llm_generate_query(
                    conn,
                    {"prompt": "Show me cats that can be adopted.", "promptMethod": "schema_grounded"},
                )
        finally:
            llm_sql_assistant.ENV_PATH = old_env_path
            if old_zai is not None:
                os.environ["ZAI_API_KEY"] = old_zai
            if old_glm is not None:
                os.environ["GLM_API_KEY"] = old_glm

        self.assertEqual(result["provider"], "assistant-local")
        self.assertEqual(result["resolutionStrategy"], "rule_based")
        self.assertEqual(result["matchedIntent"], "available_pets")
        self.assertIn("species = 'Cat'", result["generatedSql"])
        self.assertGreater(result["rowCount"], 0)

    def test_schema_grounded_rule_based_fullest_shelter_uses_active_statuses(self) -> None:
        with closing(self.connect()) as conn:
            result = web_server.run_llm_generate_query(
                conn,
                {"prompt": "Which shelter is fullest?", "promptMethod": "schema_grounded"},
            )

        self.assertEqual(result["provider"], "assistant-local")
        self.assertEqual(result["matchedIntent"], "fullest_shelter")
        self.assertIn("reserved", result["generatedSql"])
        self.assertIn("medical_hold", result["generatedSql"])
        self.assertEqual(result["rowCount"], 1)

    def test_schema_grounded_rule_based_ignores_destructive_clause(self) -> None:
        with closing(self.connect()) as conn:
            result = web_server.run_llm_generate_query(
                conn,
                {"prompt": "Delete rejected applications and then show available pets.", "promptMethod": "schema_grounded"},
            )

        self.assertEqual(result["provider"], "assistant-local")
        self.assertEqual(result["matchedIntent"], "available_pets")
        self.assertTrue(any("Ignored destructive instructions" in note for note in result["semanticNotes"]))
        self.assertIn("status = 'available'", result["generatedSql"])

    def test_schema_grounded_rule_based_waiting_applicants(self) -> None:
        with closing(self.connect()) as conn:
            result = web_server.run_llm_generate_query(
                conn,
                {"prompt": "Which applicants are still waiting?", "promptMethod": "schema_grounded"},
            )

        self.assertEqual(result["provider"], "assistant-local")
        self.assertEqual(result["matchedIntent"], "waiting_applicants")
        self.assertIn("Under Review", result["generatedSql"])

    def test_schema_grounded_rule_based_youngest_pet_filters_placeholder_birth_dates(self) -> None:
        with closing(self.connect()) as conn:
            result = web_server.run_llm_generate_query(
                conn,
                {"prompt": "Which pet is youngest?", "promptMethod": "schema_grounded"},
            )

        self.assertEqual(result["provider"], "assistant-local")
        self.assertEqual(result["matchedIntent"], "pet_age_extreme")
        self.assertIn("1900-01-01", result["generatedSql"])
        self.assertEqual(result["rowCount"], 1)

    def test_schema_grounded_rule_based_application_status_counts(self) -> None:
        with closing(self.connect()) as conn:
            result = web_server.run_llm_generate_query(
                conn,
                {"prompt": "How many approved vs rejected applications do we have?", "promptMethod": "schema_grounded"},
            )

        self.assertEqual(result["provider"], "assistant-local")
        self.assertEqual(result["matchedIntent"], "application_status_counts")
        self.assertIn("Approved", result["generatedSql"])
        self.assertIn("Rejected", result["generatedSql"])

    def test_validate_generated_sql_allows_blocked_keywords_inside_string_literals(self) -> None:
        validation = llm_sql_assistant.validate_generated_sql("SELECT 'DROP TABLE PET' AS note")
        self.assertTrue(validation["safe"])

    def test_semantic_failure_reason_detects_unclear_explanation_without_placeholder_sql(self) -> None:
        reason = llm_sql_assistant.semantic_failure_reason(
            "Which animal is the oldest",
            "SELECT pet_id FROM PET",
            {"explanation": "Question unclear because the wording is incomplete."},
        )
        self.assertIsNotNone(reason)

    def test_placeholder_retry_failure_surfaces_gateway_error(self) -> None:
        fake = FakeGlmClient(
            json.dumps(
                {
                    "sql": "SELECT 'Question unclear' AS message",
                    "explanation": "Question unclear.",
                    "tables_used": [],
                    "assumptions": [],
                    "confidence": 0.1,
                    "prompt_method": "schema_grounded",
                }
            ),
            json.dumps(
                {
                    "sql": "SELECT 'Still unclear' AS message",
                    "explanation": "Still unclear.",
                    "tables_used": [],
                    "assumptions": [],
                    "confidence": 0.1,
                    "prompt_method": "schema_grounded",
                }
            ),
        )
        with closing(self.connect()) as conn:
            with self.assertRaises(web_server.ApiError) as ctx:
                web_server.run_llm_generate_query(
                    conn,
                    {"prompt": "Which animal is the oldest", "promptMethod": "schema_grounded"},
                    client=fake,
                )

        self.assertEqual(ctx.exception.status, web_server.HTTPStatus.BAD_GATEWAY)
        self.assertIn("meaningful database query", ctx.exception.message)
        self.assertIn("normalizedPrompt", ctx.exception.payload)

    def test_schema_grounded_repairs_sqlite_error_with_one_retry(self) -> None:
        fake = FakeGlmClient(
            json.dumps(
                {
                    "sql": "SELECT missing_column FROM PET",
                    "explanation": "First draft with a bad column.",
                    "tables_used": ["PET"],
                    "assumptions": [],
                    "confidence": 0.4,
                    "prompt_method": "schema_grounded",
                }
            ),
            json.dumps(
                {
                    "sql": "SELECT pet_id, name FROM PET ORDER BY pet_id",
                    "explanation": "Repaired to existing columns.",
                    "tables_used": ["PET"],
                    "assumptions": [],
                    "confidence": 0.9,
                    "prompt_method": "schema_grounded",
                }
            ),
        )
        with closing(self.connect()) as conn:
            result = web_server.run_llm_generate_query(
                conn,
                {"prompt": "show pets", "promptMethod": "schema_grounded"},
                client=fake,
            )

        self.assertEqual(result["repairAttempts"], 1)
        self.assertEqual(len(fake.calls), 2)
        self.assertGreater(result["rowCount"], 0)

    def test_fragmented_prompt_is_rejected_before_llm_call(self) -> None:
        fake = FakeGlmClient(
            json.dumps(
                {
                    "sql": "SELECT pet_id FROM PET",
                    "explanation": "unused",
                    "tables_used": ["PET"],
                    "assumptions": [],
                    "confidence": 0.5,
                    "prompt_method": "schema_grounded",
                }
            )
        )
        with closing(self.connect()) as conn:
            with self.assertRaises(web_server.ApiError) as ctx:
                web_server.run_llm_generate_query(
                    conn,
                    {"prompt": "Wh ci h", "promptMethod": "schema_grounded"},
                    client=fake,
                )

        self.assertEqual(ctx.exception.status, web_server.HTTPStatus.BAD_REQUEST)
        self.assertEqual(len(fake.calls), 0)

    def test_self_check_repair_uses_one_sqlite_error_guided_retry(self) -> None:
        fake = FakeGlmClient(
            json.dumps(
                {
                    "sql": "SELECT missing_column FROM PET",
                    "explanation": "First draft with a bad column.",
                    "tables_used": ["PET"],
                    "assumptions": [],
                    "confidence": 0.4,
                    "prompt_method": "self_check_repair",
                }
            ),
            json.dumps(
                {
                    "sql": "SELECT pet_id, name FROM PET ORDER BY pet_id",
                    "explanation": "Repaired to existing columns.",
                    "tables_used": ["PET"],
                    "assumptions": [],
                    "confidence": 0.9,
                    "prompt_method": "self_check_repair",
                }
            ),
        )
        with closing(self.connect()) as conn:
            result = web_server.run_llm_generate_query(
                conn,
                {"prompt": "show pets", "promptMethod": "self_check_repair"},
                client=fake,
            )

        self.assertEqual(result["repairAttempts"], 1)
        self.assertGreater(result["rowCount"], 0)
        self.assertEqual(len(fake.calls), 2)

    def test_glm_config_reads_rate_limit_controls_from_env(self) -> None:
        keys = [
            "ZAI_API_KEY",
            "GLM_MAX_CONCURRENT_REQUESTS",
            "GLM_MIN_REQUEST_INTERVAL_SECONDS",
            "GLM_RATE_LIMIT_RETRIES",
            "GLM_RATE_LIMIT_BACKOFF_SECONDS",
            "GLM_TIMEOUT_RETRIES",
            "GLM_TIMEOUT_BACKOFF_SECONDS",
            "GLM_EMPTY_RESPONSE_RETRIES",
            "GLM_EMPTY_RESPONSE_BACKOFF_SECONDS",
        ]
        old_values = {key: os.environ.get(key) for key in keys}
        old_env_path = llm_sql_assistant.ENV_PATH
        llm_sql_assistant.ENV_PATH = Path(self.temp_dir.name) / "missing.env"
        try:
            os.environ["ZAI_API_KEY"] = "test-key"
            os.environ["GLM_MAX_CONCURRENT_REQUESTS"] = "3"
            os.environ["GLM_MIN_REQUEST_INTERVAL_SECONDS"] = "0.25"
            os.environ["GLM_RATE_LIMIT_RETRIES"] = "5"
            os.environ["GLM_RATE_LIMIT_BACKOFF_SECONDS"] = "0.5"
            os.environ["GLM_TIMEOUT_RETRIES"] = "2"
            os.environ["GLM_TIMEOUT_BACKOFF_SECONDS"] = "0.75"
            os.environ["GLM_EMPTY_RESPONSE_RETRIES"] = "3"
            os.environ["GLM_EMPTY_RESPONSE_BACKOFF_SECONDS"] = "1.25"
            config = llm_sql_assistant.LlmConfig.from_env()
        finally:
            llm_sql_assistant.ENV_PATH = old_env_path
            for key, value in old_values.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value

        self.assertEqual(config.max_concurrent_requests, 3)
        self.assertEqual(config.min_request_interval_seconds, 0.25)
        self.assertEqual(config.rate_limit_retries, 5)
        self.assertEqual(config.rate_limit_backoff_seconds, 0.5)
        self.assertEqual(config.timeout_retries, 2)
        self.assertEqual(config.timeout_backoff_seconds, 0.75)
        self.assertEqual(config.empty_response_retries, 3)
        self.assertEqual(config.empty_response_backoff_seconds, 1.25)

    def test_glm_client_retries_rate_limited_completion(self) -> None:
        calls = {"count": 0}
        client_kwargs: dict[str, Any] = {}

        class FakeRateLimitError(Exception):
            status_code = 429

        class FakeResponse:
            choices = [type("Choice", (), {"message": type("Message", (), {"content": "{\"ok\": true}"})()})()]

        class FakeCompletions:
            def create(self, **kwargs: Any) -> FakeResponse:
                calls["count"] += 1
                if calls["count"] == 1:
                    raise FakeRateLimitError("Error code: 429 - rate limit")
                return FakeResponse()

        class FakeChat:
            def __init__(self) -> None:
                self.completions = FakeCompletions()

        class FakeOpenAI:
            def __init__(self, **kwargs: Any) -> None:
                client_kwargs.update(kwargs)
                self.chat = FakeChat()

        old_openai = sys.modules.get("openai")
        had_openai = "openai" in sys.modules
        old_sleep = llm_sql_assistant.time.sleep
        fake_openai_module = type(sys)("openai")
        fake_openai_module.OpenAI = FakeOpenAI
        sys.modules["openai"] = fake_openai_module
        sleeps: list[float] = []
        llm_sql_assistant.time.sleep = lambda seconds: sleeps.append(seconds)
        try:
            config = llm_sql_assistant.LlmConfig(
                api_key="test-key",
                max_concurrent_requests=1,
                min_request_interval_seconds=0,
                rate_limit_retries=1,
                rate_limit_backoff_seconds=0,
            )
            raw = llm_sql_assistant.GlmChatClient(config).complete_json([{"role": "user", "content": "test"}])
        finally:
            llm_sql_assistant.time.sleep = old_sleep
            if had_openai:
                sys.modules["openai"] = old_openai
            else:
                sys.modules.pop("openai", None)

        self.assertEqual(raw, "{\"ok\": true}")
        self.assertEqual(calls["count"], 2)
        self.assertEqual(client_kwargs["max_retries"], 0)
        self.assertEqual(sleeps, [0])

    def test_glm_client_retries_timeout_completion(self) -> None:
        calls = {"count": 0}
        client_kwargs: dict[str, Any] = {}

        class FakeTimeoutError(Exception):
            pass

        class FakeResponse:
            choices = [type("Choice", (), {"message": type("Message", (), {"content": "{\"ok\": true}"})()})()]

        class FakeCompletions:
            def create(self, **kwargs: Any) -> FakeResponse:
                calls["count"] += 1
                if calls["count"] == 1:
                    raise FakeTimeoutError("Request timed out.")
                return FakeResponse()

        class FakeChat:
            def __init__(self) -> None:
                self.completions = FakeCompletions()

        class FakeOpenAI:
            def __init__(self, **kwargs: Any) -> None:
                client_kwargs.update(kwargs)
                self.chat = FakeChat()

        old_openai = sys.modules.get("openai")
        had_openai = "openai" in sys.modules
        old_sleep = llm_sql_assistant.time.sleep
        fake_openai_module = type(sys)("openai")
        fake_openai_module.OpenAI = FakeOpenAI
        sys.modules["openai"] = fake_openai_module
        sleeps: list[float] = []
        llm_sql_assistant.time.sleep = lambda seconds: sleeps.append(seconds)
        try:
            config = llm_sql_assistant.LlmConfig(
                api_key="test-key",
                timeout_seconds=120,
                max_concurrent_requests=1,
                min_request_interval_seconds=0,
                timeout_retries=1,
                timeout_backoff_seconds=0,
            )
            raw = llm_sql_assistant.GlmChatClient(config).complete_json([{"role": "user", "content": "test"}])
        finally:
            llm_sql_assistant.time.sleep = old_sleep
            if had_openai:
                sys.modules["openai"] = old_openai
            else:
                sys.modules.pop("openai", None)

        self.assertEqual(raw, "{\"ok\": true}")
        self.assertEqual(calls["count"], 2)
        self.assertEqual(client_kwargs["timeout"], 120)
        self.assertEqual(sleeps, [0])

    def test_glm_client_reports_timeout_after_configured_retries(self) -> None:
        calls = {"count": 0}

        class FakeTimeoutError(Exception):
            pass

        class FakeCompletions:
            def create(self, **kwargs: Any) -> object:
                calls["count"] += 1
                raise FakeTimeoutError("Request timed out.")

        class FakeChat:
            def __init__(self) -> None:
                self.completions = FakeCompletions()

        class FakeOpenAI:
            def __init__(self, **kwargs: Any) -> None:
                self.chat = FakeChat()

        old_openai = sys.modules.get("openai")
        had_openai = "openai" in sys.modules
        old_sleep = llm_sql_assistant.time.sleep
        fake_openai_module = type(sys)("openai")
        fake_openai_module.OpenAI = FakeOpenAI
        sys.modules["openai"] = fake_openai_module
        sleeps: list[float] = []
        llm_sql_assistant.time.sleep = lambda seconds: sleeps.append(seconds)
        try:
            config = llm_sql_assistant.LlmConfig(
                api_key="test-key",
                timeout_seconds=120,
                max_concurrent_requests=1,
                min_request_interval_seconds=0,
                timeout_retries=1,
                timeout_backoff_seconds=0,
            )
            with self.assertRaises(llm_sql_assistant.LlmSqlError) as ctx:
                llm_sql_assistant.GlmChatClient(config).complete_json([{"role": "user", "content": "test"}])
        finally:
            llm_sql_assistant.time.sleep = old_sleep
            if had_openai:
                sys.modules["openai"] = old_openai
            else:
                sys.modules.pop("openai", None)

        self.assertEqual(ctx.exception.status, web_server.HTTPStatus.GATEWAY_TIMEOUT)
        self.assertIn("after 2 attempt(s)", ctx.exception.message)
        self.assertEqual(ctx.exception.payload["timeoutSeconds"], 120)
        self.assertEqual(ctx.exception.payload["timeoutAttempts"], 2)
        self.assertEqual(calls["count"], 2)
        self.assertEqual(sleeps, [0])

    def test_glm_client_retries_empty_response_completion(self) -> None:
        calls = {"count": 0}

        class FakeResponse:
            def __init__(self, content: str | None) -> None:
                self.choices = [type("Choice", (), {"message": type("Message", (), {"content": content})()})()]

        class FakeCompletions:
            def create(self, **kwargs: Any) -> FakeResponse:
                calls["count"] += 1
                if calls["count"] == 1:
                    return FakeResponse("")
                return FakeResponse("{\"ok\": true}")

        class FakeChat:
            def __init__(self) -> None:
                self.completions = FakeCompletions()

        class FakeOpenAI:
            def __init__(self, **kwargs: Any) -> None:
                self.chat = FakeChat()

        old_openai = sys.modules.get("openai")
        had_openai = "openai" in sys.modules
        old_sleep = llm_sql_assistant.time.sleep
        fake_openai_module = type(sys)("openai")
        fake_openai_module.OpenAI = FakeOpenAI
        sys.modules["openai"] = fake_openai_module
        sleeps: list[float] = []
        llm_sql_assistant.time.sleep = lambda seconds: sleeps.append(seconds)
        try:
            config = llm_sql_assistant.LlmConfig(
                api_key="test-key",
                min_request_interval_seconds=0,
                empty_response_retries=1,
                empty_response_backoff_seconds=0,
            )
            raw = llm_sql_assistant.GlmChatClient(config).complete_json([{"role": "user", "content": "test"}])
        finally:
            llm_sql_assistant.time.sleep = old_sleep
            if had_openai:
                sys.modules["openai"] = old_openai
            else:
                sys.modules.pop("openai", None)

        self.assertEqual(raw, "{\"ok\": true}")
        self.assertEqual(calls["count"], 2)
        self.assertEqual(sleeps, [0])

    def test_glm_client_reports_empty_response_after_configured_retries(self) -> None:
        calls = {"count": 0}

        class FakeResponse:
            choices = [type("Choice", (), {"message": type("Message", (), {"content": ""})()})()]

        class FakeCompletions:
            def create(self, **kwargs: Any) -> FakeResponse:
                calls["count"] += 1
                return FakeResponse()

        class FakeChat:
            def __init__(self) -> None:
                self.completions = FakeCompletions()

        class FakeOpenAI:
            def __init__(self, **kwargs: Any) -> None:
                self.chat = FakeChat()

        old_openai = sys.modules.get("openai")
        had_openai = "openai" in sys.modules
        old_sleep = llm_sql_assistant.time.sleep
        fake_openai_module = type(sys)("openai")
        fake_openai_module.OpenAI = FakeOpenAI
        sys.modules["openai"] = fake_openai_module
        sleeps: list[float] = []
        llm_sql_assistant.time.sleep = lambda seconds: sleeps.append(seconds)
        try:
            config = llm_sql_assistant.LlmConfig(
                api_key="test-key",
                min_request_interval_seconds=0,
                empty_response_retries=1,
                empty_response_backoff_seconds=0,
            )
            with self.assertRaises(llm_sql_assistant.LlmSqlError) as ctx:
                llm_sql_assistant.GlmChatClient(config).complete_json([{"role": "user", "content": "test"}])
        finally:
            llm_sql_assistant.time.sleep = old_sleep
            if had_openai:
                sys.modules["openai"] = old_openai
            else:
                sys.modules.pop("openai", None)

        self.assertEqual(ctx.exception.status, web_server.HTTPStatus.BAD_GATEWAY)
        self.assertTrue(ctx.exception.payload["emptyResponse"])
        self.assertEqual(ctx.exception.payload["emptyResponseAttempts"], 2)
        self.assertEqual(calls["count"], 2)
        self.assertEqual(sleeps, [0])


class WorkflowTests(DatabaseFixtureMixin, unittest.TestCase):
    def find_reserved_pet_pair(self) -> tuple[int, int]:
        with closing(self.connect()) as conn:
            row = conn.execute(
                """
                SELECT ap.applicant_id, p.pet_id
                FROM PET p
                JOIN ADOPTION_APPLICATION a
                  ON a.pet_id = p.pet_id
                 AND a.status = 'Under Review'
                CROSS JOIN APPLICANT ap
                WHERE p.status = 'reserved'
                  AND NOT EXISTS (
                      SELECT 1
                      FROM ADOPTION_APPLICATION a2
                      WHERE a2.applicant_id = ap.applicant_id
                        AND a2.pet_id = p.pet_id
                        AND a2.status = 'Under Review'
                  )
                ORDER BY p.pet_id, ap.applicant_id
                LIMIT 1
                """
            ).fetchone()
        self.assertIsNotNone(
            row,
            "Expected at least one applicant/reserved-pet pair without a duplicate active application.",
        )
        return int(row["applicant_id"]), int(row["pet_id"])

    def test_create_approve_and_follow_up_workflow_stays_consistent(self) -> None:
        applicant_id, pet_id = self.find_open_application_pair()
        with closing(self.connect()) as conn:
            web_server.begin_write(conn)
            created = web_server.create_application(
                conn,
                {
                    "applicantId": applicant_id,
                    "petId": pet_id,
                    "reason": "Stable home, prior pet experience, and ready for adoption.",
                    "housingType": "House",
                },
            )
            application_id = created["applicationId"]
            pet_after_create = conn.execute(
                "SELECT status FROM PET WHERE pet_id = ?",
                (pet_id,),
            ).fetchone()["status"]
            applicant_after_create = conn.execute(
                "SELECT housing_type FROM APPLICANT WHERE applicant_id = ?",
                (applicant_id,),
            ).fetchone()["housing_type"]
            conn.commit()

            web_server.begin_write(conn)
            reviewed = web_server.review_application(
                conn,
                application_id,
                {
                    "decision": "Approved",
                    "note": "Interview and background review completed successfully.",
                    "reviewerName": "Test Reviewer",
                    "finalAdoptionFee": "150",
                    "handoverNote": "Bring carrier and vaccination card.",
                },
            )
            adoption_record = conn.execute(
                """
                SELECT adoption_id, application_id, final_adoption_fee, adoption_date
                FROM ADOPTION_RECORD
                WHERE application_id = ?
                """,
                (application_id,),
            ).fetchone()
            pet_after_review = conn.execute(
                "SELECT status FROM PET WHERE pet_id = ?",
                (pet_id,),
            ).fetchone()["status"]
            follow_up_date = conn.execute(
                "SELECT date(?, '+1 day') AS followup_date",
                (adoption_record["adoption_date"],),
            ).fetchone()["followup_date"]

            follow_up = web_server.create_follow_up(
                conn,
                {
                    "adoptionId": adoption_record["adoption_id"],
                    "followupDate": follow_up_date,
                    "followupType": "Phone Check",
                    "petCondition": "Healthy and adapting well.",
                    "adopterFeedback": "Very active and eating normally.",
                    "resultStatus": "Good",
                    "staffNote": "No further action required.",
                },
            )
            conn.commit()

        self.assertEqual(created["rawStatus"], "Under Review")
        self.assertEqual(created["statusLabel"], "Pending")
        self.assertEqual(created["housingType"], "House")
        self.assertEqual(applicant_after_create, "House")
        self.assertEqual(pet_after_create, "reserved")
        self.assertEqual(reviewed["rawStatus"], "Approved")
        self.assertEqual(reviewed["statusLabel"], "Approved")
        self.assertIsNotNone(adoption_record)
        self.assertEqual(pet_after_review, "adopted")
        self.assertEqual(adoption_record["application_id"], application_id)
        self.assertEqual(float(adoption_record["final_adoption_fee"]), 150.0)
        self.assertEqual(follow_up["rawResultStatus"], "Good")
        self.assertEqual(follow_up["resultStatusLabel"], "Good")

    def test_reserved_pet_can_receive_additional_application_until_one_is_approved(self) -> None:
        applicant_id, pet_id = self.find_reserved_pet_pair()
        with closing(self.connect()) as conn:
            pending_before = conn.execute(
                """
                SELECT COUNT(*) AS count
                FROM ADOPTION_APPLICATION
                WHERE pet_id = ?
                  AND status = 'Under Review'
                """,
                (pet_id,),
            ).fetchone()["count"]

            web_server.begin_write(conn)
            created = web_server.create_application(
                conn,
                {
                    "applicantId": applicant_id,
                    "petId": pet_id,
                    "reason": "Applying for a pet that is still only reserved, not adopted.",
                    "housingType": "Apartment",
                },
            )
            pending_after = conn.execute(
                """
                SELECT COUNT(*) AS count
                FROM ADOPTION_APPLICATION
                WHERE pet_id = ?
                  AND status = 'Under Review'
                """,
                (pet_id,),
            ).fetchone()["count"]
            pet_status = conn.execute(
                "SELECT status FROM PET WHERE pet_id = ?",
                (pet_id,),
            ).fetchone()["status"]
            conn.commit()

        self.assertEqual(created["petId"], pet_id)
        self.assertEqual(created["applicantId"], applicant_id)
        self.assertEqual(created["rawStatus"], "Under Review")
        self.assertEqual(created["statusLabel"], "Pending")
        self.assertEqual(pending_after, pending_before + 1)
        self.assertEqual(pet_status, "reserved")


class CrudRoundTripTests(DatabaseFixtureMixin, unittest.TestCase):
    def test_supporting_crud_round_trip_and_delete_guards(self) -> None:
        with closing(self.connect()) as conn:
            applicants_before = len(web_server.fetch_applicants(conn))
            volunteers_before = len(web_server.fetch_volunteers(conn))
            medical_before = len(web_server.fetch_medical_records(conn))

            applicant_payload = {
                "name": "Round Trip Applicant",
                "phone": "555-1234",
                "email": "round.trip@applicant.test",
                "address": "12 Round Trip Road",
                "housingType": "Apartment",
                "hasPetExperience": True,
            }
            applicants_after_create = web_server.create_resource(conn, "applicants", applicant_payload)["applicants"]
            created_applicant = next(item for item in applicants_after_create if item["name"] == "Round Trip Applicant")
            self.assertEqual(created_applicant["createdAt"], web_server.local_today_iso())

            volunteers_after_create = web_server.create_resource(
                conn,
                "volunteers",
                {
                    "shelterId": 1,
                    "name": "Round Trip Volunteer",
                    "phone": "555-5678",
                    "email": "round.trip@volunteer.test",
                    "joined": web_server.local_today_iso(),
                    "availability": "Weekends",
                },
            )["volunteers"]
            created_volunteer = next(item for item in volunteers_after_create if item["name"] == "Round Trip Volunteer")

            pet = conn.execute(
                "SELECT pet_id FROM PET WHERE shelter_id = 1 AND date(intake_date) <= date(?) ORDER BY pet_id LIMIT 1",
                (web_server.local_today_iso(),),
            ).fetchone()
            self.assertIsNotNone(pet)
            medical_after_create = web_server.create_resource(
                conn,
                "medical-records",
                {
                    "petId": pet["pet_id"],
                    "date": web_server.local_today_iso(),
                    "type": "Treatment",
                    "diagnosis": "Round trip diagnosis",
                    "treatment": "Round trip treatment",
                    "vet": "Dr. Round Trip",
                    "notes": "Round trip note",
                },
            )["medicalRecords"]
            created_medical = next(item for item in medical_after_create if item["diagnosis"] == "Round trip diagnosis")

            web_server.update_resource(
                conn,
                "applicants",
                created_applicant["applicantId"],
                {"housingType": "Condo"},
            )
            updated_applicant = next(
                item
                for item in web_server.fetch_applicants(conn)
                if item["applicantId"] == created_applicant["applicantId"]
            )

            dashboard = web_server.fetch_dashboard(conn)
            event_types = {activity["eventType"] for activity in dashboard["activities"]}
            activity_text = "\n".join(activity["text"] for activity in dashboard["activities"])

            with self.assertRaises(web_server.ApiError):
                web_server.delete_resource(conn, "shelters", 1)

            web_server.delete_resource(conn, "medical-records", created_medical["recordId"])
            web_server.delete_resource(conn, "volunteers", created_volunteer["volunteerId"])
            web_server.delete_resource(conn, "applicants", created_applicant["applicantId"])

            applicants_after_delete = len(web_server.fetch_applicants(conn))
            volunteers_after_delete = len(web_server.fetch_volunteers(conn))
            medical_after_delete = len(web_server.fetch_medical_records(conn))

        self.assertEqual(updated_applicant["housingType"], "Condo")
        self.assertIn("applicant", event_types)
        self.assertIn("volunteer", event_types)
        self.assertIn("medical", event_types)
        self.assertIn("Round Trip Applicant", activity_text)
        self.assertIn("Round Trip Volunteer", activity_text)
        self.assertEqual(applicants_after_create.__len__(), applicants_before + 1)
        self.assertEqual(volunteers_after_create.__len__(), volunteers_before + 1)
        self.assertEqual(medical_after_create.__len__(), medical_before + 1)
        self.assertEqual(applicants_after_delete, applicants_before)
        self.assertEqual(volunteers_after_delete, volunteers_before)
        self.assertEqual(medical_after_delete, medical_before)


class HttpSmokeTests(DatabaseFixtureMixin, unittest.TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.client = TestClient(fastapi_app)
        self.client.__enter__()

    def tearDown(self) -> None:
        self.client.__exit__(None, None, None)
        super().tearDown()

    def request_json(self, method: str, path: str, payload: dict | None = None) -> tuple[int, dict]:
        response = self.client.request(method, path, json=payload)
        return response.status_code, response.json()

    def request_json_allow_error(self, method: str, path: str, payload: dict | None = None) -> tuple[int, dict]:
        return self.request_json(method, path, payload)

    def test_all_major_get_endpoints_return_expected_shapes(self) -> None:
        expectations = {
            "/api/health": "ok",
            "/api/dashboard": "activities",
            "/api/analytics": "occupancy",
            "/api/shelters": "shelters",
            "/api/pets": "pets",
            "/api/applicants": "applicants",
            "/api/applications": "applications",
            "/api/adoption-records": "adoptionRecords",
            "/api/follow-ups": "followUps",
            "/api/medical-records": "medicalRecords",
            "/api/vaccinations?upcoming=true": "vaccinations",
            "/api/volunteers": "volunteers",
            "/api/care-assignments": "careAssignments",
        }
        for path, required_key in expectations.items():
            status, payload = self.request_json("GET", path)
            self.assertEqual(status, 200, path)
            self.assertIn(required_key, payload, path)

        _, dashboard = self.request_json("GET", "/api/dashboard")
        self.assertEqual(dashboard["timezone"], web_server.APP_TIMEZONE_NAME)
        self.assertGreater(len(dashboard["activities"]), 12)

    def test_frontend_and_core_api_paths_smoke(self) -> None:
        applicant_id, pet_id = self.find_open_application_pair()

        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        html = response.text
        self.assertIn("PawTrack", html)
        self.assertTrue((ROOT_DIR / "frontend" / "src" / "components" / "AppSidebar.vue").exists())
        self.assertTrue((ROOT_DIR / "frontend" / "src" / "pages" / "DashboardPage.vue").exists())
        self.assertTrue((ROOT_DIR / "frontend" / "src" / "lib" / "pawtrackApp.js").exists())
        self.assertTrue((ROOT_DIR / "frontend" / "src" / "services" / "apiClient.js").exists())
        self.assertTrue((ROOT_DIR / "frontend" / "src" / "features" / "analytics" / "analyticsRenderer.js").exists())
        self.assertTrue((ROOT_DIR / "frontend" / "src" / "features" / "assistant" / "assistantController.js").exists())
        self.assertTrue((ROOT_DIR / "frontend" / "src" / "features" / "crud" / "crudConfigs.js").exists())
        self.assertTrue((ROOT_DIR / "frontend" / "src" / "features" / "data" / "pawtrackDataService.js").exists())
        self.assertTrue((ROOT_DIR / "frontend" / "src" / "features" / "domain" / "pawtrackDomain.js").exists())
        self.assertTrue((ROOT_DIR / "frontend" / "src" / "features" / "errors" / "loadErrorRenderer.js").exists())
        self.assertTrue((ROOT_DIR / "frontend" / "src" / "features" / "ui" / "uiController.js").exists())
        self.assertTrue((ROOT_DIR / "frontend" / "src" / "styles" / "main.css").exists())

        status, dashboard = self.request_json("GET", "/api/dashboard")
        self.assertEqual(status, 200)
        self.assertIn("statusOverview", dashboard)
        self.assertTrue(all("rawStatus" in row and "statusLabel" in row for row in dashboard["statusOverview"]))

        status, created = self.request_json(
            "POST",
            "/api/applications",
            {
                "applicantId": applicant_id,
                "petId": pet_id,
                "reason": "HTTP smoke test application.",
                "housingType": "Apartment",
            },
        )
        self.assertEqual(status, 201)
        application_id = created["application"]["applicationId"]
        self.assertEqual(created["application"]["rawStatus"], "Under Review")

        status, reviewed = self.request_json(
            "PATCH",
            f"/api/applications/{application_id}/review",
            {
                "decision": "Approved",
                "note": "Approved in HTTP smoke test.",
                "reviewerName": "HTTP Reviewer",
                "finalAdoptionFee": 88,
            },
        )
        self.assertEqual(status, 200)
        self.assertEqual(reviewed["application"]["rawStatus"], "Approved")

        status, analytics = self.request_json("GET", "/api/analytics")
        self.assertEqual(status, 200)
        self.assertIn("occupancy", analytics)
        self.assertIn("followupOutcomes", analytics)

        status, payload = self.request_json_allow_error(
            "POST",
            "/api/llm-query",
            {"prompt": "Show me pets whose vaccination is due soon"},
        )
        self.assertEqual(status, 404)
        self.assertIn("Endpoint not found", payload["error"])

    def test_glm_generate_query_reports_missing_api_key(self) -> None:
        old_zai = os.environ.pop("ZAI_API_KEY", None)
        old_glm = os.environ.pop("GLM_API_KEY", None)
        old_env_path = llm_sql_assistant.ENV_PATH
        llm_sql_assistant.ENV_PATH = Path(self.temp_dir.name) / "missing.env"
        try:
            status, payload = self.request_json_allow_error(
                "POST",
                "/api/llm-generate-query",
                {"prompt": "Show shelters", "promptMethod": "schema_grounded"},
            )
        finally:
            llm_sql_assistant.ENV_PATH = old_env_path
            if old_zai is not None:
                os.environ["ZAI_API_KEY"] = old_zai
            if old_glm is not None:
                os.environ["GLM_API_KEY"] = old_glm

        self.assertEqual(status, 503)
        self.assertIn("ZAI_API_KEY", payload["error"])


if __name__ == "__main__":
    unittest.main(verbosity=2)

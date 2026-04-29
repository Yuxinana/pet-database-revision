from __future__ import annotations

from typing import Any

from ..services import web_server_legacy as legacy_web

ApiError = legacy_web.ApiError
CRUD_CONFIGS = legacy_web.CRUD_CONFIGS


def initialize_database(reset: bool = False) -> None:
    legacy_web.initialize_database(reset=reset)


def read_payload(path: str, query: dict[str, list[str]] | None = None) -> dict[str, Any]:
    return legacy_web.api_payload(path, query or {})


def write_transaction(fn, *args, **kwargs):
    with legacy_web.managed_connection() as conn:
        legacy_web.begin_write(conn)
        return fn(conn, *args, **kwargs)


def create_application(payload: dict[str, Any]) -> dict[str, Any]:
    return write_transaction(legacy_web.create_application, payload)


def review_application(application_id: int, payload: dict[str, Any]) -> dict[str, Any]:
    return write_transaction(legacy_web.review_application, application_id, payload)


def create_follow_up(payload: dict[str, Any]) -> dict[str, Any]:
    return write_transaction(legacy_web.create_follow_up, payload)


def run_llm_generate_query(payload: dict[str, Any]) -> dict[str, Any]:
    with legacy_web.managed_connection() as conn:
        return legacy_web.run_llm_generate_query(conn, payload)


def create_resource(resource: str, payload: dict[str, Any]) -> dict[str, Any]:
    return write_transaction(legacy_web.create_resource, resource, payload)


def update_resource(resource: str, item_id: int, payload: dict[str, Any]) -> dict[str, Any]:
    return write_transaction(legacy_web.update_resource, resource, item_id, payload)


def delete_resource(resource: str, item_id: int) -> dict[str, Any]:
    return write_transaction(legacy_web.delete_resource, resource, item_id)

from __future__ import annotations

from typing import Any

from ..services import pawtrack_service

ApiError = pawtrack_service.ApiError
CRUD_CONFIGS = pawtrack_service.CRUD_CONFIGS


def initialize_database(reset: bool = False) -> None:
    pawtrack_service.initialize_database(reset=reset)


def read_payload(path: str, query: dict[str, list[str]] | None = None) -> dict[str, Any]:
    return pawtrack_service.api_payload(path, query or {})


def write_transaction(fn, *args, **kwargs):
    with pawtrack_service.managed_connection() as conn:
        pawtrack_service.begin_write(conn)
        return fn(conn, *args, **kwargs)


def create_application(payload: dict[str, Any]) -> dict[str, Any]:
    return write_transaction(pawtrack_service.create_application, payload)


def review_application(application_id: int, payload: dict[str, Any]) -> dict[str, Any]:
    return write_transaction(pawtrack_service.review_application, application_id, payload)


def create_follow_up(payload: dict[str, Any]) -> dict[str, Any]:
    return write_transaction(pawtrack_service.create_follow_up, payload)


def run_llm_generate_query(payload: dict[str, Any]) -> dict[str, Any]:
    with pawtrack_service.managed_connection() as conn:
        return pawtrack_service.run_llm_generate_query(conn, payload)


def create_resource(resource: str, payload: dict[str, Any]) -> dict[str, Any]:
    return write_transaction(pawtrack_service.create_resource, resource, payload)


def update_resource(resource: str, item_id: int, payload: dict[str, Any]) -> dict[str, Any]:
    return write_transaction(pawtrack_service.update_resource, resource, item_id, payload)


def delete_resource(resource: str, item_id: int) -> dict[str, Any]:
    return write_transaction(pawtrack_service.delete_resource, resource, item_id)

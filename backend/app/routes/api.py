from __future__ import annotations

from http import HTTPStatus
from typing import Any

from fastapi import APIRouter

from ..core import legacy


router = APIRouter(prefix="/api")


@router.get("/health")
def health() -> dict[str, Any]:
    return legacy.read_payload("/api/health")


@router.get("/dashboard")
def dashboard() -> dict[str, Any]:
    return legacy.read_payload("/api/dashboard")


@router.get("/analytics")
def analytics() -> dict[str, Any]:
    return legacy.read_payload("/api/analytics")


@router.get("/shelters")
def shelters() -> dict[str, Any]:
    return legacy.read_payload("/api/shelters")


@router.get("/pets")
def pets() -> dict[str, Any]:
    return legacy.read_payload("/api/pets")


@router.get("/applicants")
def applicants() -> dict[str, Any]:
    return legacy.read_payload("/api/applicants")


@router.get("/applications")
def applications() -> dict[str, Any]:
    return legacy.read_payload("/api/applications")


@router.get("/adoption-records")
def adoption_records() -> dict[str, Any]:
    return legacy.read_payload("/api/adoption-records")


@router.get("/follow-ups")
def follow_ups() -> dict[str, Any]:
    return legacy.read_payload("/api/follow-ups")


@router.get("/medical-records")
def medical_records() -> dict[str, Any]:
    return legacy.read_payload("/api/medical-records")


@router.get("/vaccinations")
def vaccinations(upcoming: bool = False) -> dict[str, Any]:
    return legacy.read_payload("/api/vaccinations", {"upcoming": [str(upcoming).lower()]})


@router.get("/volunteers")
def volunteers() -> dict[str, Any]:
    return legacy.read_payload("/api/volunteers")


@router.get("/care-assignments")
def care_assignments() -> dict[str, Any]:
    return legacy.read_payload("/api/care-assignments")


@router.post("/applications", status_code=HTTPStatus.CREATED)
def create_application(payload: dict[str, Any]) -> dict[str, Any]:
    return {"application": legacy.create_application(payload)}


@router.patch("/applications/{application_id}/review")
def review_application(application_id: int, payload: dict[str, Any]) -> dict[str, Any]:
    return {"application": legacy.review_application(application_id, payload)}


@router.post("/follow-ups", status_code=HTTPStatus.CREATED)
def create_follow_up(payload: dict[str, Any]) -> dict[str, Any]:
    return {"followUp": legacy.create_follow_up(payload)}


@router.post("/llm-generate-query")
def llm_generate_query(payload: dict[str, Any]) -> dict[str, Any]:
    return legacy.run_llm_generate_query(payload)


@router.post("/{resource}", status_code=HTTPStatus.CREATED)
def create_resource(resource: str, payload: dict[str, Any]) -> dict[str, Any]:
    if resource not in legacy.CRUD_CONFIGS:
        raise legacy.ApiError(HTTPStatus.NOT_FOUND, "Endpoint not found.")
    return legacy.create_resource(resource, payload)


@router.patch("/{resource}/{item_id}")
def update_resource(resource: str, item_id: int, payload: dict[str, Any]) -> dict[str, Any]:
    if resource not in legacy.CRUD_CONFIGS:
        raise legacy.ApiError(HTTPStatus.NOT_FOUND, "Endpoint not found.")
    return legacy.update_resource(resource, item_id, payload)


@router.delete("/{resource}/{item_id}")
def delete_resource(resource: str, item_id: int) -> dict[str, Any]:
    if resource not in legacy.CRUD_CONFIGS:
        raise legacy.ApiError(HTTPStatus.NOT_FOUND, "Endpoint not found.")
    return legacy.delete_resource(resource, item_id)

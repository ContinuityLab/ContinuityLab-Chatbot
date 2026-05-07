"""HTTP client implementation of MangroveRepo against the live API.

Endpoint: https://mangrove-api.azurewebsites.net (configurable via env).

Authentication strategy:
- If MANGROVE_API_TOKEN is set, use it directly as a bearer token.
- Otherwise, fall back to azure.identity.DefaultAzureCredential and request a
  token for the API's resource scope.

If the API rejects the call or the env is not configured, callers should
catch the exception and fall back to the stub repo.
"""
from __future__ import annotations

import os
from typing import Any

import httpx

from mangrove_copilot.models import (
    AuditEntry,
    JourneyStatus,
    RACI,
    SurveyData,
)


class MangroveApiError(RuntimeError):
    pass


class ApiClientRepo:
    def __init__(
        self,
        base_url: str,
        token_provider: "TokenProvider | None" = None,
        timeout: float = 10.0,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._token_provider = token_provider or _default_token_provider()
        self._timeout = timeout

    def _headers(self) -> dict[str, str]:
        token = self._token_provider()
        headers = {"Accept": "application/json", "Content-Type": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers

    def _request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        url = f"{self._base_url}{path}"
        try:
            with httpx.Client(timeout=self._timeout) as client:
                response = client.request(method, url, headers=self._headers(), **kwargs)
        except httpx.HTTPError as exc:
            raise MangroveApiError(f"{method} {url} failed: {exc}") from exc
        if response.status_code >= 400:
            raise MangroveApiError(
                f"{method} {url} returned {response.status_code}: {response.text}"
            )
        return response

    def get_survey(self, survey_id: str, workspace_id: int) -> SurveyData:
        response = self._request(
            "GET",
            f"/api/Surveys/{survey_id}",
            params={"workspaceId": workspace_id},
        )
        return _survey_from_api(response.json())

    def update_survey_field(
        self, survey_id: str, workspace_id: int, field: str, value: Any
    ) -> None:
        if hasattr(value, "model_dump"):
            value = value.model_dump(mode="json")
        self._request(
            "PATCH",
            f"/api/Surveys/{survey_id}",
            params={"workspaceId": workspace_id},
            json={field: value},
        )

    def link_workflow(
        self, survey_id: str, workspace_id: int, workflow: str
    ) -> None:
        self._request(
            "POST",
            f"/api/Surveys/{survey_id}/link-workflow",
            params={"workspaceId": workspace_id},
            json={"workflow": workflow},
        )

    def write_audit_log(self, entry: AuditEntry) -> None:
        self._request(
            "POST",
            "/api/AuditLog",
            json=entry.model_dump(mode="json"),
        )

    def update_dashboard_status(
        self, survey_id: str, workspace_id: int, status: JourneyStatus
    ) -> None:
        self._request(
            "POST",
            f"/api/Dashboard/{survey_id}/status",
            params={"workspaceId": workspace_id},
            json={"status": status},
        )


# ---- helpers ----

TokenProvider = "callable[[], str | None]"


def _default_token_provider():  # type: ignore[no-untyped-def]
    """Returns a callable that yields a bearer token, or None.

    Resolution order:
    1. MANGROVE_API_TOKEN env var (static token).
    2. DefaultAzureCredential scoped against MANGROVE_API_SCOPE (default: api://mangrove/.default).
    3. None (anonymous).
    """
    static = os.environ.get("MANGROVE_API_TOKEN")
    if static:
        return lambda: static

    scope = os.environ.get("MANGROVE_API_SCOPE")
    if not scope:
        return lambda: None

    try:
        from azure.identity import DefaultAzureCredential  # type: ignore
    except ImportError:
        return lambda: None

    credential = DefaultAzureCredential()

    def _get():  # type: ignore[no-untyped-def]
        try:
            return credential.get_token(scope).token
        except Exception:  # pragma: no cover - defensive
            return None

    return _get


def _survey_from_api(payload: dict[str, Any]) -> SurveyData:
    """Map the API JSON shape onto SurveyData.

    The Mangrove API field names are not fully documented; this helper
    normalizes a few obvious aliases. Unknown fields are ignored.
    """
    raci_payload = payload.get("raci") or payload.get("RACI") or {}
    raci = RACI(
        responsible=raci_payload.get("responsible") or raci_payload.get("Responsible"),
        accountable=raci_payload.get("accountable") or raci_payload.get("Accountable"),
        consulted=raci_payload.get("consulted") or raci_payload.get("Consulted"),
        informed=raci_payload.get("informed") or raci_payload.get("Informed"),
    )

    def pick(*keys: str, default: Any = None) -> Any:
        for k in keys:
            if k in payload and payload[k] is not None:
                return payload[k]
        return default

    return SurveyData(
        survey_id=pick("survey_id", "SurveyID", "id"),
        workspace_id=pick("workspace_id", "WorkspaceID"),
        name=pick("name", "Name", default="(unnamed)"),
        category=pick("category", "Category", default="Redundancy"),
        recovery_time=pick("recovery_time", "Recovery_Time", default="24-72 Hrs"),
        country_impact=pick("country_impact", "Country_Impact", default="No"),
        company_critical=pick("company_critical", "Company_Critical", default="No"),
        customer_time_critical=pick(
            "customer_time_critical", "Customer_Time_Critical", default="No"
        ),
        customer_data=pick("customer_data", "Customer_Data", default="No"),
        employee_data=pick("employee_data", "Employee_Data", default="No"),
        proprietary_info=pick("proprietary_info", "Proprietary_Info", default="No"),
        financial_data=pick("financial_data", "Financial_Data", default="No"),
        backed_up=pick("backed_up", "Backed_Up", default="No"),
        raci=raci,
        workflow=pick("workflow", "Workflow"),
        regulated=pick("regulated", "Regulated", default="No"),
        connected_workflows=pick("connected_workflows", default=[]),
        connected_services=pick("connected_services", default=[]),
        connected_assets=pick("connected_assets", default=[]),
    )

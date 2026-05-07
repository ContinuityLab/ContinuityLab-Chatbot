"""In-memory stub implementation of MangroveRepo for offline / CI runs."""
from __future__ import annotations

from copy import deepcopy
from typing import Any

from mangrove_copilot.models import (
    AuditEntry,
    JourneyStatus,
    RACI,
    SurveyData,
)


def _seed() -> dict[tuple[str, int], SurveyData]:
    return {
        ("survey-001", 12): SurveyData(
            survey_id="survey-001",
            workspace_id=12,
            name="AWS Multi-AZ Backup",
            category="Redundancy",
            recovery_time="3-6 Hrs",
            country_impact="Yes",
            company_critical="Yes",
            customer_time_critical="Yes",
            customer_data="Yes",
            employee_data="Yes",
            proprietary_info="Yes",
            financial_data="Yes",
            backed_up="Yes",
            raci=RACI(
                responsible="Eddy Mangrove",
                accountable="Sam Chen",
                consulted="Risk APAC",
                informed="Investor Relations",
            ),
            workflow=None,
            regulated="No",
            connected_workflows=["KYC", "Customer Service"],
            connected_services=["Order Processing"],
            connected_assets=["Salesforce", "AWS US-East-1"],
        ),
        ("survey-002", 12): SurveyData(
            survey_id="survey-002",
            workspace_id=12,
            name="Legacy On-Prem Reporting Server",
            category="Dependency",
            recovery_time="12-18 Hrs",
            country_impact="No",
            company_critical="No",
            customer_time_critical="No",
            customer_data="No",
            employee_data="Yes",
            proprietary_info="No",
            financial_data="Yes",
            backed_up="No",
            raci=RACI(responsible="Pat Lee", accountable="Sam Chen"),
            workflow="Monthly Payroll",
            regulated="No",
            connected_workflows=["Monthly Payroll"],
            connected_assets=["On-Prem DC"],
        ),
    }


class StubRepo:
    """Mutable in-memory repo. State is per-instance."""

    def __init__(self) -> None:
        self._data: dict[tuple[str, int], SurveyData] = _seed()
        self._audit: list[AuditEntry] = []
        self._dashboard: dict[tuple[str, int], JourneyStatus] = {}

    def get_survey(self, survey_id: str, workspace_id: int) -> SurveyData:
        key = (survey_id, workspace_id)
        if key not in self._data:
            raise LookupError(
                f"No survey found for SurveyID={survey_id} WorkspaceID={workspace_id}"
            )
        return deepcopy(self._data[key])

    def update_survey_field(
        self, survey_id: str, workspace_id: int, field: str, value: Any
    ) -> None:
        key = (survey_id, workspace_id)
        survey = self._data[key]
        if not hasattr(survey, field):
            raise AttributeError(f"SurveyData has no field {field!r}")
        setattr(survey, field, value)

    def link_workflow(
        self, survey_id: str, workspace_id: int, workflow: str
    ) -> None:
        self.update_survey_field(survey_id, workspace_id, "workflow", workflow)

    def write_audit_log(self, entry: AuditEntry) -> None:
        self._audit.append(entry)

    def update_dashboard_status(
        self, survey_id: str, workspace_id: int, status: JourneyStatus
    ) -> None:
        self._dashboard[(survey_id, workspace_id)] = status

    # -- test helpers --
    @property
    def audit(self) -> list[AuditEntry]:
        return self._audit

    @property
    def dashboard(self) -> dict[tuple[str, int], JourneyStatus]:
        return self._dashboard

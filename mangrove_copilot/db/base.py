"""Repo Protocol for Mangrove DB access."""
from __future__ import annotations

from typing import Protocol

from mangrove_copilot.models import AuditEntry, JourneyStatus, SurveyData


class MangroveRepo(Protocol):
    def get_survey(self, survey_id: str, workspace_id: int) -> SurveyData: ...

    def update_survey_field(
        self, survey_id: str, workspace_id: int, field: str, value: object
    ) -> None: ...

    def link_workflow(
        self, survey_id: str, workspace_id: int, workflow: str
    ) -> None: ...

    def write_audit_log(self, entry: AuditEntry) -> None: ...

    def update_dashboard_status(
        self, survey_id: str, workspace_id: int, status: JourneyStatus
    ) -> None: ...

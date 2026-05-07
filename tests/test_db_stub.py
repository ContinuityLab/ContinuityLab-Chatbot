import pytest

from mangrove_copilot.db.stub import StubRepo
from mangrove_copilot.models import AuditEntry


def test_get_survey_found():
    repo = StubRepo()
    survey = repo.get_survey("survey-001", 12)
    assert survey.name == "AWS Multi-AZ Backup"
    assert survey.raci.responsible == "Eddy Mangrove"


def test_get_survey_not_found_raises():
    repo = StubRepo()
    with pytest.raises(LookupError):
        repo.get_survey("missing", 12)


def test_update_field_persists():
    repo = StubRepo()
    repo.update_survey_field("survey-001", 12, "recovery_time", "12-18 Hrs")
    assert repo.get_survey("survey-001", 12).recovery_time == "12-18 Hrs"


def test_link_workflow_persists():
    repo = StubRepo()
    repo.link_workflow("survey-001", 12, "DR Workflow")
    assert repo.get_survey("survey-001", 12).workflow == "DR Workflow"


def test_audit_log_appends():
    repo = StubRepo()
    entry = AuditEntry(
        survey_id="survey-001",
        workspace_id=12,
        category="Redundancy",
        journey_status="Resolved",
    )
    repo.write_audit_log(entry)
    assert repo.audit == [entry]


def test_dashboard_status_overwrites():
    repo = StubRepo()
    repo.update_dashboard_status("survey-001", 12, "Monitoring")
    repo.update_dashboard_status("survey-001", 12, "Resolved")
    assert repo.dashboard[("survey-001", 12)] == "Resolved"

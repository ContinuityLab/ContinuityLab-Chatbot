from tests.conftest import run_with_script


def visited(session) -> list[int]:
    return [e["node"] for e in session.transcript if e["kind"] == "enter_node"]


def test_node1_no_exits_immediately(repo):
    session, _ = run_with_script(
        repo, survey_id="survey-001", workspace_id=12, category="Redundancy",
        answers=["No"],
    )
    assert visited(session) == [1]
    assert session.journey_status == "Pending"
    assert repo.audit == []


def test_yes_link_to_workflow_archives(repo):
    session, _ = run_with_script(
        repo, survey_id="survey-001", workspace_id=12, category="Redundancy",
        answers=["Yes", "Yes", "DR Workflow"],
    )
    assert visited(session) == [1, 2, 11]
    assert session.journey_status == "Resolved"
    assert repo.dashboard[("survey-001", 12)] == "Resolved"
    assert len(repo.audit) == 1
    survey_after = repo.get_survey("survey-001", 12)
    assert survey_after.workflow == "DR Workflow"


def test_node2_monitor_path(repo):
    # answers: address?Yes, link?No, choice A, frequency 6, owner accept (blank), notes (blank)
    session, _ = run_with_script(
        repo, survey_id="survey-001", workspace_id=12, category="Redundancy",
        answers=["Yes", "No", "A", "6", "", ""],
    )
    assert visited(session) == [1, 2, 5, 6, 11]
    assert session.journey_status == "Monitoring"
    assert repo.dashboard[("survey-001", 12)] == "Monitoring"
    assert session.monitoring is not None
    assert session.monitoring.review_interval == "biyearly"
    assert session.monitoring.owner == "Eddy Mangrove"


def test_node2_review_then_mitigate(repo):
    # 1:Yes, 2:No, 2-choice:B, node3 proceed:Yes, node4 stakeholders:Yes, choose:B, node7:A, mitigate choice:X, custom action
    session, _ = run_with_script(
        repo, survey_id="survey-001", workspace_id=12, category="Redundancy",
        answers=["Yes", "No", "B", "Yes", "Yes", "B", "A", "X", "Run quarterly disaster drill"],
    )
    assert visited(session) == [1, 2, 3, 4, 7, 8, 11]
    assert session.intervention is not None
    assert session.intervention.strategy == "Mitigate"
    assert session.intervention.action == "Run quarterly disaster drill"
    assert session.journey_status == "Resolved"


def test_transfer_path(repo):
    # 1:Yes, 2:No, B, node3:Yes, node4:Yes, B, node7:B, transfer choice:X, custom plan
    session, _ = run_with_script(
        repo, survey_id="survey-001", workspace_id=12, category="Redundancy",
        answers=["Yes", "No", "B", "Yes", "Yes", "B", "B", "X", "Cyber insurance via Acme"],
    )
    assert visited(session) == [1, 2, 3, 4, 7, 9, 11]
    assert session.intervention.strategy == "Transfer"
    assert session.intervention.action == "Cyber insurance via Acme"


def test_avoid_complete_path(repo):
    # 1:Yes, 2:No, B, node3:Yes, node4:Yes, B, node7:C, avoid choice:X, custom plan, target date, complete?:Yes
    session, _ = run_with_script(
        repo, survey_id="survey-001", workspace_id=12, category="Redundancy",
        answers=["Yes", "No", "B", "Yes", "Yes", "B", "C", "X", "Decommission server", "2026-06-01", "Yes"],
    )
    assert visited(session) == [1, 2, 3, 4, 7, 10, 11]
    assert session.intervention.strategy == "Avoid"
    assert session.intervention.completed is True


def test_avoid_incomplete_routes_to_monitor(repo):
    # avoid choice:X + custom plan + target date + complete?:No -> node 5 -> 6 -> 11
    session, _ = run_with_script(
        repo, survey_id="survey-001", workspace_id=12, category="Redundancy",
        answers=[
            "Yes", "No", "B", "Yes", "Yes", "B",
            "C", "X", "Decommission server", "2026-06-01", "No",
            "3", "", "",
        ],
    )
    assert visited(session) == [1, 2, 3, 4, 7, 10, 5, 6, 11]
    assert session.intervention.strategy == "Avoid"
    assert session.intervention.completed is False
    assert session.journey_status == "Monitoring"


def test_accept_path_routes_to_monitor(repo):
    # 1:Yes, 2:No, B, 3:Yes, 4:Yes, B, 7:D, freq 12, accept owner, no notes
    session, _ = run_with_script(
        repo, survey_id="survey-001", workspace_id=12, category="Redundancy",
        answers=["Yes", "No", "B", "Yes", "Yes", "B", "D", "12", "", ""],
    )
    assert visited(session) == [1, 2, 3, 4, 7, 5, 6, 11]
    assert session.monitoring.review_interval == "yearly"


def test_node3_field_correction_loops_then_proceeds(repo):
    # 1:Y, 2:No-Review(B), 3:No, pick field 1 (recovery_time), new value, then 3:Yes, 4:Yes, B (address), 7:A, mit choice:X, custom action
    session, _ = run_with_script(
        repo, survey_id="survey-001", workspace_id=12, category="Redundancy",
        answers=[
            "Yes", "No", "B",
            "No", "1", "12-18 Hrs",
            "Yes",
            "Yes", "B",
            "A", "X", "tweak backup playbook",
        ],
    )
    nodes = visited(session)
    # Node 3 should appear twice (once before correction, once after)
    assert nodes.count(3) == 2
    survey_after = repo.get_survey("survey-001", 12)
    assert survey_after.recovery_time == "12-18 Hrs"


def test_node4_raci_correction_loops(repo):
    # 1:Y, 2:No-B, 3:Yes, 4:No, choose R, "New Owner", then 4:Yes, A monitor, freq 6, owner blank, notes blank
    session, _ = run_with_script(
        repo, survey_id="survey-001", workspace_id=12, category="Redundancy",
        answers=[
            "Yes", "No", "B",
            "Yes",
            "No", "R", "New Owner",
            "Yes", "A",
            "6", "", "",
        ],
    )
    nodes = visited(session)
    assert nodes.count(4) == 2
    survey_after = repo.get_survey("survey-001", 12)
    assert survey_after.raci.responsible == "New Owner"
    # Node 5 should default to the *new* responsible owner
    assert session.monitoring.owner == "New Owner"


def test_node3_abort_closes_flow(repo):
    session, _ = run_with_script(
        repo, survey_id="survey-001", workspace_id=12, category="Redundancy",
        answers=["Yes", "No", "B", "No", "X"],
    )
    assert visited(session) == [1, 2, 3]
    assert repo.audit == []
    assert ("survey-001", 12) not in repo.dashboard

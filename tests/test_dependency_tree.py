from tests.conftest import run_with_script


def visited(session) -> list[int]:
    return [e["node"] for e in session.transcript if e["kind"] == "enter_node"]


def test_low_impact_path(repo):
    # Node1: critical?No -> Node 4. Then data correct?Yes, freq 6, owner accept, accept Yes
    session, _ = run_with_script(
        repo, survey_id="survey-002", workspace_id=12, category="Dependency",
        answers=["No", "Yes", "6", "", "Yes"],
    )
    assert visited(session) == [1, 4, 99]
    assert session.journey_status == "Monitoring"
    assert session.monitoring.review_interval == "biyearly"
    assert len(repo.audit) == 1


def test_high_impact_full_address(repo):
    # Node1:Yes, Node2 review:Yes, Node3 address:Yes,
    # probability=8, then 6 impacts (5,7,3,6,8,4),
    # Step3 time threshold:Yes, Step4 template:No, plan text,
    # Step5 supporting (skip), Step6 freq=3, Step7 owner override blank, Step8 accept Yes
    session, _ = run_with_script(
        repo, survey_id="survey-002", workspace_id=12, category="Dependency",
        answers=[
            "Yes", "Yes", "Yes",
            "8",
            "5", "7", "3", "6", "8", "4",
            "Yes",
            "No", "Build hot-standby DR",
            "",
            "3", "",
            "Yes",
        ],
    )
    assert visited(session) == [1, 2, 3, 99]
    assert session.dependency_impact is not None
    assert session.dependency_impact.probability == 8
    assert session.dependency_impact.financial == 7
    assert session.intervention is not None
    assert session.intervention.action == "Build hot-standby DR"
    assert session.journey_status == "Resolved"
    assert session.monitoring.review_interval == "quarterly"


def test_node3_recovery_window_outdated_aborts(repo):
    # Node1:Yes, Node2:Yes, Node3:Yes, probability+impacts, Step3:No
    session, _ = run_with_script(
        repo, survey_id="survey-002", workspace_id=12, category="Dependency",
        answers=[
            "Yes", "Yes", "Yes",
            "5",
            "1", "1", "1", "1", "1", "1",
            "No",
        ],
    )
    assert visited(session) == [1, 2, 3]
    assert repo.audit == []


def test_node2_says_data_wrong_drops_to_low_impact(repo):
    # Node1:Yes, Node2:No -> Node 4 path
    session, _ = run_with_script(
        repo, survey_id="survey-002", workspace_id=12, category="Dependency",
        answers=["Yes", "No", "Yes", "1", "", "Yes"],
    )
    assert visited(session) == [1, 2, 4, 99]
    assert session.journey_status == "Monitoring"

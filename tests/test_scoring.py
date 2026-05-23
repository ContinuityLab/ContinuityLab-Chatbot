from mangrove_copilot.models import RACI, SurveyData
from mangrove_copilot.scoring import calculate_resilience_score


def make(**overrides):
    base = dict(
        survey_id="s",
        workspace_id=1,
        name="t",
        category="Redundancy",
        recovery_time="24-72 Hrs",
        country_impact="No",
        company_critical="No",
        customer_time_critical="No",
        customer_data="No",
        employee_data="No",
        proprietary_info="No",
        financial_data="No",
        backed_up="No",
        raci=RACI(),
    )
    base.update(overrides)
    return SurveyData(**base)


def test_zero_score_for_all_no():
    assert calculate_resilience_score(make()) == 0


def test_max_score_capped_at_100():
    survey = make(
        recovery_time="Immediately",
        country_impact="Yes",
        company_critical="Yes",
        customer_time_critical="Yes",
        customer_data="Yes",
        employee_data="Yes",
        proprietary_info="Yes",
        financial_data="Yes",
        backed_up="Yes",
    )
    assert calculate_resilience_score(survey) == 100


def test_recovery_time_buckets():
    expected = {
        "Immediately": 20,
        "0-1 Hr": 20,
        "1-3 Hrs": 20,
        "3-6 Hrs": 10,
        "6-12 Hrs": 8,
        "12-18 Hrs": 6,
        "18-24 Hrs": 4,
        "24-72 Hrs": 0,
        "3-7 Days": 0,
        "> 1 Week": 0,
    }
    for bucket, points in expected.items():
        assert calculate_resilience_score(make(recovery_time=bucket)) == points


def test_individual_weights():
    assert calculate_resilience_score(make(country_impact="Yes")) == 12
    assert calculate_resilience_score(make(company_critical="Yes")) == 12
    assert calculate_resilience_score(make(customer_time_critical="Yes")) == 12
    assert calculate_resilience_score(make(customer_data="Yes")) == 15
    assert calculate_resilience_score(make(employee_data="Yes")) == 15
    assert calculate_resilience_score(make(proprietary_info="Yes")) == 8
    assert calculate_resilience_score(make(financial_data="Yes")) == 4
    assert calculate_resilience_score(make(backed_up="Yes")) == 2

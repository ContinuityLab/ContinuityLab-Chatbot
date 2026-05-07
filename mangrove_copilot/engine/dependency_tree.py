"""Dependency decision tree (Nodes 1-4 with high-impact / low-impact paths).

Implements the spec from the Mangrove Plus Co-Pilot Logic document.
"""
from __future__ import annotations

from typing import Optional

from mangrove_copilot.console import (
    prompt_choice,
    prompt_int,
    prompt_optional,
    prompt_yes_no,
)
from mangrove_copilot.engine.state_machine import Node, Session
from mangrove_copilot.models import (
    DependencyImpact,
    InterventionPlan,
    MonitoringPlan,
    ReviewInterval,
)
from mangrove_copilot.scoring import calculate_resilience_score


_INTERVAL_BY_INPUT: dict[str, ReviewInterval] = {
    "1": "monthly",
    "3": "quarterly",
    "6": "biyearly",
    "12": "yearly",
}


def _print_review_block(session: Session) -> None:
    s = session.survey
    session.console.say("Current dependency facts:")
    session.console.say(f"  Country impact:        {s.country_impact}")
    session.console.say(f"  Company critical:      {s.company_critical}")
    session.console.say(f"  Customer time-crit:    {s.customer_time_critical}")
    session.console.say(f"  Customer data:         {s.customer_data}")
    session.console.say(f"  Employee data:         {s.employee_data}")
    session.console.say(f"  Proprietary info:      {s.proprietary_info}")
    session.console.say(f"  Financial data:        {s.financial_data}")
    session.console.say(
        f"  Connected workflows:   {', '.join(s.connected_workflows) or '(none)'}"
    )
    session.console.say(
        f"  Connected services:    {', '.join(s.connected_services) or '(none)'}"
    )
    session.console.say(
        f"  Connected assets:      {', '.join(s.connected_assets) or '(none)'}"
    )


# ---------------------------------------------------------------------------
# Node 1: critical to the business?
# ---------------------------------------------------------------------------


def node_1_critical(session: Session) -> Optional[int]:
    score = calculate_resilience_score(session.survey)
    session.resilience_score = score
    session.console.say(
        f"\n[Dependency Node 1] Resilience score: {score}/100 — "
        f"{session.survey.name}"
    )
    session.console.say(
        session.voice.say("Is this dependency critical to the business?")
    )
    if prompt_yes_no(session.console, "Critical? (Yes/No): "):
        session.log("decision", node=1, choice="critical")
        return 2
    session.log("decision", node=1, choice="not-critical")
    return 4  # low-impact path


# ---------------------------------------------------------------------------
# Node 2: review-and-confirm gate before deep address
# ---------------------------------------------------------------------------


def node_2_review_confirm(session: Session) -> Optional[int]:
    session.console.say("\n[Dependency Node 2] Review the criticality & readiness data.")
    _print_review_block(session)
    session.console.say(
        session.voice.say(
            "Please review these answers. Are they accurate? If not, we'll "
            "drop into the low-impact path so you can update them first."
        )
    )
    if prompt_yes_no(session.console, "Data accurate and want to proceed? (Yes/No): "):
        session.log("decision", node=2, choice="proceed")
        return 3
    session.log("decision", node=2, choice="needs-update")
    return 4


# ---------------------------------------------------------------------------
# Node 3: high-impact deep dive (probability + 6 impact dimensions + plan)
# ---------------------------------------------------------------------------


def node_3_address(session: Session) -> Optional[int]:
    session.console.say("\n[Dependency Node 3] Address the dependency.")
    if not prompt_yes_no(
        session.console,
        "Now that you've reviewed the data, do you want to address it? (Yes/No): ",
    ):
        session.log("decision", node=3, choice="defer-to-monitor")
        return 4

    session.console.say(
        session.voice.say(
            "Step 1 of 8: rate the probability of this dependency failing. "
            "Consider provider reliability, complexity, and external factors."
        )
    )
    probability = prompt_int(
        session.console, "Probability (1=unlikely, 10=probable): ", low=1, high=10
    )

    session.console.say(
        "Step 2: rate the impact across six dimensions, each on a 1-10 scale."
    )
    reputational = prompt_int(session.console, "  Reputational: ", low=1, high=10)
    financial = prompt_int(session.console, "  Financial: ", low=1, high=10)
    regulatory = prompt_int(session.console, "  Regulatory: ", low=1, high=10)
    security = prompt_int(session.console, "  Security / data privacy: ", low=1, high=10)
    third_party = prompt_int(session.console, "  Third-party: ", low=1, high=10)
    resource = prompt_int(session.console, "  Resource: ", low=1, high=10)

    session.dependency_impact = DependencyImpact(
        probability=probability,
        reputational=reputational,
        financial=financial,
        regulatory=regulatory,
        security=security,
        third_party=third_party,
        resource=resource,
    )

    session.console.say(
        f"Step 3: confirming time threshold. Current recovery window: "
        f"{session.survey.recovery_time}."
    )
    if not prompt_yes_no(
        session.console, "Is this still the right window? (Yes/No): "
    ):
        session.console.say(
            "Please update the criticality questionnaire and re-run; closing flow."
        )
        session.log("guardrail", node=3, reason="recovery_window_outdated")
        return None

    use_template = prompt_yes_no(
        session.console, "Step 4: would you like a template plan to address? (Yes/No): "
    )
    plan_lines = []
    if use_template:
        session.console.say(
            "Template generated: Redundancy / Diversification / Contingency / "
            "Risk Transfer. Customise below."
        )
    plan = session.console.ask("Step 4 cont.: action plan summary: ")
    plan_lines.append(plan)

    supporting = prompt_optional(
        session.console,
        "Step 5: link/doc supporting the measures (or press Enter to skip): ",
    )

    session.console.say(
        "Step 6: select periodic review interval. "
        "Options: 1 (monthly), 3 (quarterly), 6 (bi-yearly), 12 (yearly)."
    )
    raw = prompt_choice(
        session.console, "Months between reviews: ", list(_INTERVAL_BY_INPUT)
    )
    interval = _INTERVAL_BY_INPUT[raw]

    default_owner = session.survey.raci.accountable or session.survey.raci.responsible or "(unassigned)"
    session.console.say(
        f"Step 7: the Accountable stakeholder ({default_owner}) is suggested as "
        f"the reviewer."
    )
    override = prompt_optional(
        session.console, "Press Enter to accept, or type a different owner: "
    )
    owner = override or default_owner

    session.monitoring = MonitoringPlan(
        review_interval=interval,
        owner=owner,
        notes="; ".join(filter(None, [*plan_lines, supporting])) or None,
    )
    session.intervention = InterventionPlan(
        strategy="Mitigate", action="; ".join(plan_lines), completed=False
    )

    session.console.say("Step 8: please ACCEPT & CONFIRM this plan.")
    if not prompt_yes_no(session.console, "Accept the conversation flow? (Yes/No): "):
        session.console.say("Plan not accepted; nothing committed.")
        session.log("guardrail", node=3, reason="plan_not_accepted")
        return None

    session.journey_status = "Resolved"
    session.log(
        "intervention",
        strategy=session.intervention.strategy,
        owner=owner,
        interval=interval,
    )
    return 99  # finalize


# ---------------------------------------------------------------------------
# Node 4: low-impact "document + monitor" path
# ---------------------------------------------------------------------------


def node_4_low_impact(session: Session) -> Optional[int]:
    session.console.say("\n[Dependency Node 4] Low-impact path: document + monitor.")
    session.console.say(
        session.voice.say(
            "The recommendation is to document the dependency, assess its "
            "risk, and put basic monitoring in place. Please review the data "
            "first."
        )
    )
    _print_review_block(session)
    if not prompt_yes_no(
        session.console,
        "Are these answers correct? (Yes to monitor / No to update first): ",
    ):
        session.console.say(
            "Please return to the survey and amend the answers; closing flow."
        )
        session.log("guardrail", node=4, reason="data_incorrect")
        return None

    session.console.say(
        "How often should we re-check? "
        "Options: 1 (monthly), 3 (quarterly), 6 (bi-yearly), 12 (yearly)."
    )
    raw = prompt_choice(
        session.console, "Months between reviews: ", list(_INTERVAL_BY_INPUT)
    )
    interval = _INTERVAL_BY_INPUT[raw]

    default_owner = session.survey.raci.accountable or session.survey.raci.responsible or "(unassigned)"
    override = prompt_optional(
        session.console,
        f"Suggested owner (Accountable): {default_owner}. Override (or Enter): ",
    )
    owner = override or default_owner

    session.monitoring = MonitoringPlan(review_interval=interval, owner=owner)
    if not prompt_yes_no(session.console, "ACCEPT & CONFIRM all previous steps? (Yes/No): "):
        session.console.say("Not accepted; nothing committed.")
        session.log("guardrail", node=4, reason="not_accepted")
        return None

    session.journey_status = "Monitoring"
    session.log("monitoring", node=4, owner=owner, interval=interval)
    return 99  # finalize


# ---------------------------------------------------------------------------
# Pseudo-node 99: finalize (mirrors redundancy Node 11)
# ---------------------------------------------------------------------------


def node_99_finalize(session: Session) -> Optional[int]:
    session.console.say("\n[Dependency Finalization]")
    session.repo.update_dashboard_status(
        session.trigger.survey_id,
        session.trigger.workspace_id,
        session.journey_status,
    )
    session.repo.write_audit_log(session.to_audit())
    session.console.say(
        f"Audit log committed. Dashboard status: {session.journey_status}."
    )
    session.console.say("--- Session complete ---")
    return None


DEPENDENCY_NODES: dict[int, Node] = {
    1: node_1_critical,
    2: node_2_review_confirm,
    3: node_3_address,
    4: node_4_low_impact,
    99: node_99_finalize,
}

"""Redundancy decision tree (Phases 1-6, Nodes 1-11).

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
    InterventionPlan,
    MonitoringPlan,
    ReviewInterval,
)
from mangrove_copilot.scoring import calculate_resilience_score


# ---------------------------------------------------------------------------
# Phase 1: Identification & connection
# ---------------------------------------------------------------------------


def node_1_intent(session: Session) -> Optional[int]:
    session.console.say(
        f"\n[Node 1: Intent] Survey: {session.survey.name}"
    )
    session.console.say(
        session.voice.say(
            "I've identified a redundancy tied to this survey entry. "
            "Would you like to address this now?"
        )
    )
    if prompt_yes_no(session.console, "Address now? (Yes/No): "):
        session.log("decision", node=1, choice="Yes")
        return 2
    session.log("decision", node=1, choice="No")
    session.console.say("Understood — exiting flow.")
    return None  # exit


def node_2_workflow_connection(session: Session) -> Optional[int]:
    session.console.say("\n[Node 2: Workflow Connection]")
    session.console.say(
        session.voice.say("Could we connect this redundancy to an active workflow?")
    )
    if prompt_yes_no(session.console, "Tie to a workflow? (Yes/No): "):
        workflow = session.console.ask("Which workflow? ")
        session.repo.link_workflow(
            session.trigger.survey_id, session.trigger.workspace_id, workflow
        )
        session.survey.workflow = workflow
        session.console.say(
            f"Linked to '{workflow}'. The redundancy view will be updated."
        )
        session.log("decision", node=2, choice="Yes-link", workflow=workflow)
        return 11  # straight to archive

    session.console.say(
        "Understood. You can still (A) Monitor this for now, "
        "(B) Review the data and stakeholders, or (C) Do nothing."
    )
    choice = prompt_choice(session.console, "Your choice (A/B/C): ", ["A", "B", "C"])
    session.log("decision", node=2, choice=choice)
    if choice == "A":
        return 5
    if choice == "B":
        return 3
    session.console.say("Exiting flow without changes.")
    return None


# ---------------------------------------------------------------------------
# Phase 2: Validation & stakeholders
# ---------------------------------------------------------------------------


_REVIEWABLE_FIELDS = {
    "1": ("recovery_time", "Recovery window"),
    "2": ("country_impact", "Country impact"),
    "3": ("company_critical", "Company critical"),
    "4": ("customer_time_critical", "Customer time-critical"),
    "5": ("customer_data", "Customer data"),
    "6": ("employee_data", "Employee data"),
    "7": ("proprietary_info", "Proprietary information"),
    "8": ("financial_data", "Financial data"),
    "9": ("backed_up", "Asset data backed up"),
}


def _refresh_score(session: Session) -> int:
    score = calculate_resilience_score(session.survey)
    session.resilience_score = score
    return score


def node_3_data_review(session: Session) -> Optional[int]:
    score = _refresh_score(session)
    session.console.say(f"\n[Node 3: Data Review] Resilience score: {score}/100")
    session.console.say("Current criticality & readiness:")
    for key, (field, label) in _REVIEWABLE_FIELDS.items():
        value = getattr(session.survey, field)
        session.console.say(f"  {key}. {label}: {value}")

    session.console.say("Connected:")
    session.console.say(
        f"  Workflows: {', '.join(session.survey.connected_workflows) or '(none)'}"
    )
    session.console.say(
        f"  Services:  {', '.join(session.survey.connected_services) or '(none)'}"
    )
    session.console.say(
        f"  Assets:    {', '.join(session.survey.connected_assets) or '(none)'}"
    )

    session.console.say(
        session.voice.say(
            "Have you reviewed this assessment and are you ready to proceed?"
        )
    )
    if prompt_yes_no(session.console, "Proceed? (Yes/No): "):
        session.log("decision", node=3, choice="Proceed")
        return 4

    field_choice = prompt_choice(
        session.console,
        "Which field needs correction? (1-9, or X to abort): ",
        list(_REVIEWABLE_FIELDS) + ["X"],
    )
    if field_choice == "X":
        session.console.say(
            "Please return to the survey, update the data, and re-submit. "
            "Closing flow."
        )
        session.log("guardrail", node=3, reason="data_incorrect_aborted")
        return None

    field, label = _REVIEWABLE_FIELDS[field_choice]
    new_value = session.console.ask(f"New value for {label}: ")
    session.repo.update_survey_field(
        session.trigger.survey_id, session.trigger.workspace_id, field, new_value
    )
    setattr(session.survey, field, new_value)
    session.log("update", node=3, field=field, value=new_value)
    return 3  # re-review


_RACI_FIELDS = {
    "R": ("responsible", "Responsible"),
    "A": ("accountable", "Accountable"),
    "C": ("consulted", "Consulted"),
    "I": ("informed", "Informed"),
}


def node_4_stakeholder_review(session: Session) -> Optional[int]:
    raci = session.survey.raci
    session.console.say("\n[Node 4: Stakeholder Review]")
    session.console.say(f"  R - Responsible: {raci.responsible or '(unassigned)'}")
    session.console.say(f"  A - Accountable: {raci.accountable or '(unassigned)'}")
    session.console.say(f"  C - Consulted:   {raci.consulted or '(unassigned)'}")
    session.console.say(f"  I - Informed:    {raci.informed or '(unassigned)'}")
    session.console.say(
        session.voice.say(
            "This risk is assigned to the Responsible stakeholder. "
            "Are these stakeholders correct?"
        )
    )
    if not prompt_yes_no(session.console, "Stakeholders correct? (Yes/No): "):
        which = prompt_choice(
            session.console,
            "Which role to update? (R/A/C/I, or X to abort): ",
            list(_RACI_FIELDS) + ["X"],
        )
        if which == "X":
            session.console.say(
                "Please update stakeholders in the survey settings and re-submit. "
                "Closing flow."
            )
            session.log("guardrail", node=4, reason="raci_incorrect_aborted")
            return None
        attr, label = _RACI_FIELDS[which]
        new_value = session.console.ask(f"New {label}: ")
        setattr(raci, attr, new_value)
        session.repo.update_survey_field(
            session.trigger.survey_id,
            session.trigger.workspace_id,
            "raci",
            raci,
        )
        session.log("update", node=4, role=label, value=new_value)
        return 4  # re-review

    session.console.say(
        "Decide your path: (A) Monitor or (B) Address the redundancy."
    )
    choice = prompt_choice(session.console, "Your choice (A/B): ", ["A", "B"])
    session.log("decision", node=4, choice=choice)
    return 5 if choice == "A" else 7


# ---------------------------------------------------------------------------
# Phase 3: Monitoring flow
# ---------------------------------------------------------------------------


_INTERVAL_BY_INPUT: dict[str, ReviewInterval] = {
    "3": "quarterly",
    "6": "biyearly",
    "12": "yearly",
    "1": "monthly",
}


def node_5_frequency_selection(session: Session) -> Optional[int]:
    session.console.say("\n[Node 5: Frequency Selection]")
    session.console.say(
        "How often should we re-check this risk? "
        "Options: 1 (monthly), 3 (quarterly), 6 (bi-yearly), 12 (yearly)."
    )
    raw = prompt_choice(
        session.console, "Months between reviews: ", list(_INTERVAL_BY_INPUT)
    )
    interval = _INTERVAL_BY_INPUT[raw]

    default_owner = session.survey.raci.responsible or "(unassigned)"
    session.console.say(
        f"The Responsible stakeholder ({default_owner}) will own this monitoring "
        f"task by default."
    )
    override = prompt_optional(
        session.console,
        "Press Enter to accept, or type a different owner: ",
    )
    owner = override or default_owner

    notes = prompt_optional(
        session.console, "Optional notes for the monitoring record: "
    )
    session.monitoring = MonitoringPlan(
        review_interval=interval, owner=owner, notes=notes
    )
    session.log(
        "monitoring",
        node=5,
        interval=interval,
        owner=owner,
    )
    return 6


def node_6_monitoring_recap(session: Session) -> Optional[int]:
    plan = session.monitoring
    assert plan is not None, "Node 6 requires a monitoring plan"
    session.console.say("\n[Node 6: Monitoring Recap]")
    session.console.say(
        f"You've completed the monitoring flow. Risk assigned to {plan.owner}; "
        f"reminder cadence: {plan.review_interval}."
    )
    session.repo.update_dashboard_status(
        session.trigger.survey_id, session.trigger.workspace_id, "Monitoring"
    )
    session.journey_status = "Monitoring"
    session.log("dashboard", status="Monitoring")
    return 11


# ---------------------------------------------------------------------------
# Phase 4: Intervention strategies
# ---------------------------------------------------------------------------


def node_7_intervention_strategy(session: Session) -> Optional[int]:
    session.console.say("\n[Node 7: Intervention Strategy]")
    session.console.say(
        session.voice.say(
            "Based on the criticality and stakeholder review, decide which "
            "intervention is most appropriate. This action will be tracked."
        )
    )
    session.console.say("(A) Mitigate — implement a fix to reduce impact.")
    session.console.say("(B) Transfer — shift responsibility (insurance / SLA / outsourcing).")
    session.console.say("(C) Avoid — decommission the cause entirely.")
    session.console.say("(D) Accept & Monitor — document and watch.")
    choice = prompt_choice(
        session.console, "Your choice (A/B/C/D): ", ["A", "B", "C", "D"]
    )
    session.log("decision", node=7, choice=choice)
    return {"A": 8, "B": 9, "C": 10, "D": 5}[choice]


# ---------------------------------------------------------------------------
# Phase 5: Action planning
# ---------------------------------------------------------------------------


_MITIGATE_ACTIONS = {
    "A": "Schedule periodic access & credential reviews",
    "B": "Add automated health-check or heartbeat monitoring",
    "C": "Create a documented runbook for failover procedures",
    "D": "Set up alerting for configuration drift or downtime",
    "E": "Establish a regular backup verification schedule",
}


def node_8_mitigate(session: Session) -> Optional[int]:
    session.console.say("\n[Node 8: Mitigate Action Plan]")
    session.console.say(
        session.voice.say(
            "You're mitigating this redundancy. The biggest risk for an "
            "essential-but-rare backup is decay — outdated keys, forgotten "
            "processes. What's the single, highest-impact check you can put "
            "in place to keep it sharp?"
        )
    )
    for key, label in _MITIGATE_ACTIONS.items():
        session.console.say(f"  ({key}) {label}")
    session.console.say("  (X) Other — describe your own")
    choice = prompt_choice(
        session.console,
        "Your choice (A/B/C/D/E/X): ",
        list(_MITIGATE_ACTIONS) + ["X"],
    )
    if choice == "X":
        action = session.console.ask("Describe your mitigation check: ")
    else:
        action = _MITIGATE_ACTIONS[choice]
    session.intervention = InterventionPlan(strategy="Mitigate", action=action)
    session.journey_status = "Resolved"
    session.log("intervention", strategy="Mitigate", action=action)
    return 11


_TRANSFER_ACTIONS = {
    "A": "Purchase insurance coverage",
    "B": "Upgrade to premium SLA tier",
    "C": "Outsource to managed service provider",
    "D": "Contract a third-party DR partner",
}


def node_9_transfer(session: Session) -> Optional[int]:
    session.console.say("\n[Node 9: Transfer Action Plan]")
    session.console.say(
        session.voice.say(
            "You're transferring this redundancy. Common patterns: insurance, "
            "premium SLA tier, or outsourcing to a specialized vendor. "
            "Who is better positioned to absorb this risk?"
        )
    )
    for key, label in _TRANSFER_ACTIONS.items():
        session.console.say(f"  ({key}) {label}")
    session.console.say("  (X) Other — describe your own")
    choice = prompt_choice(
        session.console,
        "Your choice (A/B/C/D/X): ",
        list(_TRANSFER_ACTIONS) + ["X"],
    )
    if choice == "X":
        action = session.console.ask("Describe your risk transfer plan: ")
    else:
        action = _TRANSFER_ACTIONS[choice]
    session.intervention = InterventionPlan(strategy="Transfer", action=action)
    session.journey_status = "Resolved"
    session.log("intervention", strategy="Transfer", action=action)
    return 11


_AVOID_PLANS = {
    "A": "Gradual phase-out with migration to alternative",
    "B": "Immediate shutdown and removal",
    "C": "Consolidate into another existing resource",
    "D": "Archive and disable access",
}


def node_10_avoid(session: Session) -> Optional[int]:
    session.console.say("\n[Node 10: Avoid / Decommission]")
    session.console.say(
        session.voice.say(
            "Decommissioning permanently retires the asset, workflow, or team. "
            "Which approach fits best?"
        )
    )
    for key, label in _AVOID_PLANS.items():
        session.console.say(f"  ({key}) {label}")
    session.console.say("  (X) Other — describe your own")
    choice = prompt_choice(
        session.console,
        "Your choice (A/B/C/D/X): ",
        list(_AVOID_PLANS) + ["X"],
    )
    if choice == "X":
        plan = session.console.ask("Describe your decommissioning plan: ")
    else:
        plan = _AVOID_PLANS[choice]

    target_date = session.console.ask("Target completion date: ")
    plan = f"{plan} — target: {target_date}"

    complete = prompt_yes_no(
        session.console, "Is decommissioning 100% complete now? (Yes/No): "
    )
    session.intervention = InterventionPlan(
        strategy="Avoid", action=plan, completed=complete
    )
    if complete:
        session.journey_status = "Resolved"
        session.log("intervention", strategy="Avoid", completed=True)
        return 11

    session.console.say(
        "Marked 'Monitoring: Action Pending'. Moving to monitoring flow."
    )
    session.log("intervention", strategy="Avoid", completed=False)
    return 5


# ---------------------------------------------------------------------------
# Phase 6: Finalization
# ---------------------------------------------------------------------------


def _build_audit_comment(session: Session) -> Optional[str]:
    parts: list[str] = []
    if session.intervention:
        parts.append(f"Strategy: {session.intervention.strategy}")
        if session.intervention.action:
            parts.append(session.intervention.action)
    if session.monitoring:
        parts.append(
            f"Monitoring: {session.monitoring.review_interval} "
            f"(owner: {session.monitoring.owner})"
        )
        if session.monitoring.notes:
            parts.append(f"Notes: {session.monitoring.notes}")
    return " | ".join(parts) if parts else None


def node_11_archive(session: Session) -> Optional[int]:
    session.console.say("\n[Node 11: Archive]")
    if session.journey_status == "Pending":
        # straight Yes-link path treats the redundancy as resolved
        session.journey_status = "Resolved"

    try:
        session.repo.update_dashboard_status(
            session.trigger.survey_id,
            session.trigger.workspace_id,
            session.journey_status,
        )
    except Exception as exc:
        session.console.say(f"Warning: could not update dashboard: {exc}")
        session.log("error", node=11, reason=str(exc))

    audit = session.to_audit()
    audit_comment = _build_audit_comment(session)
    if audit_comment:
        session.log("audit_comment", comment=audit_comment)

    try:
        session.repo.write_audit_log(audit)
    except Exception as exc:
        session.console.say(f"Warning: could not write audit log: {exc}")
        session.log("error", node=11, reason=str(exc))

    session.console.say(
        f"Audit log committed. Investor dashboard status: {session.journey_status}."
    )
    if audit_comment:
        session.console.say(f"Summary: {audit_comment}")
    session.console.say("--- Session complete ---")
    return None


REDUNDANCY_NODES: dict[int, Node] = {
    1: node_1_intent,
    2: node_2_workflow_connection,
    3: node_3_data_review,
    4: node_4_stakeholder_review,
    5: node_5_frequency_selection,
    6: node_6_monitoring_recap,
    7: node_7_intervention_strategy,
    8: node_8_mitigate,
    9: node_9_transfer,
    10: node_10_avoid,
    11: node_11_archive,
}

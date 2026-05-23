"""Generic state-machine engine.

A `Node` is a function that mutates the `Session` and returns the next node id
(or `None` to end the session). The engine simply dispatches.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from mangrove_copilot.agent import Voice
from mangrove_copilot.console import Console
from mangrove_copilot.db.base import MangroveRepo
from mangrove_copilot.models import (
    AuditEntry,
    DependencyImpact,
    InterventionPlan,
    JourneyStatus,
    MonitoringPlan,
    SurveyData,
    TriggerPayload,
)


@dataclass
class Session:
    trigger: TriggerPayload
    survey: SurveyData
    repo: MangroveRepo
    console: Console
    voice: Voice
    journey_status: JourneyStatus = "Pending"
    monitoring: Optional[MonitoringPlan] = None
    intervention: Optional[InterventionPlan] = None
    dependency_impact: Optional[DependencyImpact] = None
    transcript: list[dict[str, Any]] = field(default_factory=list)
    resilience_score: Optional[int] = None

    def log(self, kind: str, **fields: Any) -> None:
        self.transcript.append({"kind": kind, **fields})

    def to_audit(self) -> AuditEntry:
        return AuditEntry(
            survey_id=self.trigger.survey_id,
            workspace_id=self.trigger.workspace_id,
            category=self.trigger.category,
            journey_status=self.journey_status,
            monitoring=self.monitoring,
            intervention=self.intervention,
            dependency_impact=self.dependency_impact,
            transcript=self.transcript,
            resilience_score=self.resilience_score,
        )


Node = Callable[[Session], Optional[int]]


def run_tree(session: Session, nodes: dict[int, Node], start: int = 1, max_hops: int = 50) -> Session:
    current: Optional[int] = start
    for _ in range(max_hops):
        if current is None:
            break
        if current not in nodes:
            raise RuntimeError(f"Decision tree has no handler for node {current}")
        session.log("enter_node", node=current)
        current = nodes[current](session)
    else:
        raise RuntimeError(
            f"Decision tree exceeded {max_hops} hops — possible infinite loop"
        )
    return session

"""Pydantic models for trigger payloads, survey data, and audit records."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


Category = Literal["Redundancy", "Dependency"]
RecoveryTime = Literal[
    "Immediately",
    "0-1 Hr",
    "1-3 Hrs",
    "3-6 Hrs",
    "6-12 Hrs",
    "12-18 Hrs",
    "18-24 Hrs",
    "24-72 Hrs",
    "3-7 Days",
    "> 1 Week",
]
YesNo = Literal["Yes", "No"]
ReviewInterval = Literal["monthly", "quarterly", "biyearly", "yearly"]
InterventionStrategy = Literal["Mitigate", "Transfer", "Avoid", "Accept"]
JourneyStatus = Literal["Pending", "Monitoring", "Resolved"]


class TriggerPayload(BaseModel):
    """Inbound parameters from the UI / Foundry trigger."""

    survey_id: str = Field(alias="SurveyID")
    workspace_id: int = Field(alias="WorkspaceID")
    category: Category = Field(alias="Category")

    model_config = {"populate_by_name": True}


class RACI(BaseModel):
    responsible: Optional[str] = None
    accountable: Optional[str] = None
    consulted: Optional[str] = None
    informed: Optional[str] = None


class SurveyData(BaseModel):
    """Mangrove DB record for a single survey entry."""

    survey_id: str
    workspace_id: int
    name: str
    category: Category

    # Criticality
    recovery_time: RecoveryTime = "24-72 Hrs"
    country_impact: YesNo = "No"
    company_critical: YesNo = "No"
    customer_time_critical: YesNo = "No"

    # Readiness
    customer_data: YesNo = "No"
    employee_data: YesNo = "No"
    proprietary_info: YesNo = "No"
    financial_data: YesNo = "No"
    backed_up: YesNo = "No"

    # Stakeholders
    raci: RACI = Field(default_factory=RACI)

    # Linkage
    workflow: Optional[str] = None
    regulated: YesNo = "No"

    # Free-form connections shown in Node 3
    connected_workflows: list[str] = Field(default_factory=list)
    connected_services: list[str] = Field(default_factory=list)
    connected_assets: list[str] = Field(default_factory=list)


class MonitoringPlan(BaseModel):
    review_interval: ReviewInterval
    owner: str  # Responsible RACI by default; user may override
    notes: Optional[str] = None


class InterventionPlan(BaseModel):
    strategy: InterventionStrategy
    action: Optional[str] = None  # mitigate description / transfer entity / avoid confirmation
    completed: bool = False  # only meaningful for Avoid


class DependencyImpact(BaseModel):
    """Node 3 step-2 multi-dimension impact assessment for the dependency tree."""

    probability: int = Field(ge=1, le=10)
    reputational: int = Field(ge=1, le=10)
    financial: int = Field(ge=1, le=10)
    regulatory: int = Field(ge=1, le=10)
    security: int = Field(ge=1, le=10)
    third_party: int = Field(ge=1, le=10)
    resource: int = Field(ge=1, le=10)


class AuditEntry(BaseModel):
    survey_id: str
    workspace_id: int
    category: Category
    journey_status: JourneyStatus
    monitoring: Optional[MonitoringPlan] = None
    intervention: Optional[InterventionPlan] = None
    dependency_impact: Optional[DependencyImpact] = None
    transcript: list[dict[str, Any]] = Field(default_factory=list)
    completed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    resilience_score: Optional[int] = None

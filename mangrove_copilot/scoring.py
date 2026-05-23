"""Single canonical resilience scoring function.

Implements the weighted logic from the spec:

Criticality (max 56):
  Recovery_Time bucket  -> 0..20
  Country impact        -> 12 if Yes
  Company critical      -> 12 if Yes
  Customer time-crit    -> 12 if Yes

Readiness (max 44):
  Customer data         -> 15 if Yes
  Employee data         -> 15 if Yes
  Proprietary info      ->  8 if Yes
  Financial data        ->  4 if Yes
  Backed up             ->  2 if Yes

Final score is clipped to 0..100.
"""
from __future__ import annotations

from mangrove_copilot.models import SurveyData

_RECOVERY_TIME_POINTS = {
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


def calculate_resilience_score(data: SurveyData) -> int:
    score = _RECOVERY_TIME_POINTS.get(data.recovery_time, 0)
    if data.country_impact == "Yes":
        score += 12
    if data.company_critical == "Yes":
        score += 12
    if data.customer_time_critical == "Yes":
        score += 12
    if data.customer_data == "Yes":
        score += 15
    if data.employee_data == "Yes":
        score += 15
    if data.proprietary_info == "Yes":
        score += 8
    if data.financial_data == "Yes":
        score += 4
    if data.backed_up == "Yes":
        score += 2
    return max(0, min(100, score))

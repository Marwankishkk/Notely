from dataclasses import dataclass

from models.subscriptions.subscriptions import Plan


@dataclass(frozen=True)
class PlanLimits:
    notes_per_day: int | None
    max_audio_seconds: int | None
    summaries_per_day: int | None


PLAN_LIMITS: dict[str, PlanLimits] = {
    Plan.BASIC.value: PlanLimits(
        notes_per_day=10,
        max_audio_seconds=60,
        summaries_per_day=1,
    ),
    Plan.PRO.value: PlanLimits(
        notes_per_day=None,
        max_audio_seconds=600,
        summaries_per_day=None,
    ),
}


def get_plan_limits(plan: str) -> PlanLimits:
    return PLAN_LIMITS.get(plan, PLAN_LIMITS[Plan.BASIC.value])

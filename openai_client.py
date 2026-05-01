"""
openai_client.py — точка входа для бота.

Сохраняет старый интерфейс (AgentResult + run_agent) для совместимости с bot.py,
но внутри делегирует выполнение пайплайну.
"""

from dataclasses import dataclass

from pipeline.models import ResumeData, ExperienceItem, EducationItem, GapReport
from pipeline.runner import run_pipeline


__all__ = ["ExperienceItem", "EducationItem", "ResumeData", "GapReport", "AgentResult", "run_agent"]


@dataclass
class AgentResult:
    score: float
    score_reasoning: str
    resume: ResumeData
    gap_report: GapReport


async def run_agent(
    grade: str,
    direction: str,
    resume_text: str,
    vacancy_text: str,
    extra_prefs: dict,
) -> AgentResult:
    result = await run_pipeline(
        grade=grade,
        direction=direction,
        resume_text=resume_text,
        vacancy_text=vacancy_text,
        extra_prefs=extra_prefs,
    )
    return AgentResult(
        score=result.score,
        score_reasoning=result.score_reasoning,
        resume=result.resume,
        gap_report=result.gap_report,
    )

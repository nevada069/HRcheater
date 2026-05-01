from dataclasses import dataclass, field


# ── Базовые блоки резюме ───────────────────────────────────────────────────────

@dataclass
class ExperienceItem:
    company: str
    role: str
    start: str
    end: str
    description: str


@dataclass
class EducationItem:
    institution: str
    degree: str
    year: str


@dataclass
class ResumeData:
    name: str
    contacts: str
    summary: str
    experience: list[ExperienceItem]
    skills: list[str]
    education: list[EducationItem]


# ── Шаг 1: извлечение фактов из резюме ────────────────────────────────────────

@dataclass
class ExtractedResume:
    name: str
    contacts: str
    summary: str
    skills: list[str]
    experience: list[ExperienceItem]
    education: list[EducationItem]


# ── Шаг 2: анализ вакансии ────────────────────────────────────────────────────

@dataclass
class VacancyAnalysis:
    must_have: list[str]
    nice_to_have: list[str]
    keywords: list[str]          # ключевые слова для ATS
    seniority_signals: list[str] # сигналы грейда из текста вакансии
    role_essence: str            # суть роли в 1-2 предложениях


# ── Шаг 4: gap analysis ───────────────────────────────────────────────────────

@dataclass
class GapReport:
    strengths: list[str]     # есть у кандидата И нужно вакансии
    gaps: list[str]          # нужно вакансии, нет у кандидата
    reframeable: list[str]   # есть у кандидата, можно переформулировать


# ── Финальный результат пайплайна ─────────────────────────────────────────────

@dataclass
class PipelineResult:
    score: float
    score_reasoning: str
    resume: ResumeData
    gap_report: GapReport

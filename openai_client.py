import json
from dataclasses import dataclass
from typing import Optional
from openai import AsyncOpenAI
from config import OPENAI_API_KEY
from prompts import build_system_prompt

client = AsyncOpenAI(api_key=OPENAI_API_KEY)


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


@dataclass
class AgentResult:
    score: float
    score_reasoning: str
    resume: ResumeData


async def run_agent(
    grade: str,
    direction: str,
    resume_text: str,
    vacancy_text: str,
    extra_prefs: dict,
) -> AgentResult:
    prompt = build_system_prompt(
        grade=grade,
        direction=direction,
        resume_text=resume_text,
        vacancy_text=vacancy_text,
        extra_prefs=extra_prefs,
    )

    response = await client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        response_format={"type": "json_object"},
    )

    raw = response.choices[0].message.content
    data = json.loads(raw)

    resume_raw = data["resume"]
    experience = [
        ExperienceItem(
            company=e["company"],
            role=e["role"],
            start=e["start"],
            end=e["end"],
            description=e["description"],
        )
        for e in resume_raw.get("experience", [])
    ]
    education = [
        EducationItem(
            institution=e["institution"],
            degree=e["degree"],
            year=e["year"],
        )
        for e in resume_raw.get("education", [])
    ]

    return AgentResult(
        score=float(data["score"]),
        score_reasoning=data["score_reasoning"],
        resume=ResumeData(
            name=resume_raw["name"],
            contacts=resume_raw["contacts"],
            summary=resume_raw["summary"],
            experience=experience,
            skills=resume_raw.get("skills", []),
            education=education,
        ),
    )

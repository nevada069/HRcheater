import pdfplumber
import docx
from config import RESUME_MAX_CHARS, VACANCY_MAX_CHARS


class TextTooLongError(Exception):
    pass


def extract_from_pdf(file_path: str) -> str:
    with pdfplumber.open(file_path) as pdf:
        pages = [page.extract_text() or "" for page in pdf.pages]
    text = "\n".join(pages).strip()
    if not text:
        raise ValueError("Не удалось извлечь текст из PDF. Возможно, файл содержит только изображения (скан).")
    return text


def extract_from_docx(file_path: str) -> str:
    doc = docx.Document(file_path)
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    text = "\n".join(paragraphs).strip()
    if not text:
        raise ValueError("Не удалось извлечь текст из DOCX. Файл пустой.")
    return text


def prepare_resume_text(text: str) -> str:
    text = text.strip()
    if len(text) > RESUME_MAX_CHARS:
        raise TextTooLongError(
            f"Резюме слишком длинное ({len(text)} символов). "
            f"Максимум — {RESUME_MAX_CHARS} символов. "
            "Пожалуйста, сократите текст и попробуйте снова."
        )
    return text


def prepare_vacancy_text(text: str) -> str:
    text = text.strip()
    if len(text) > VACANCY_MAX_CHARS:
        raise TextTooLongError(
            f"Описание вакансии слишком длинное ({len(text)} символов). "
            f"Максимум — {VACANCY_MAX_CHARS} символов. "
            "Пожалуйста, сократите текст и попробуйте снова."
        )
    return text

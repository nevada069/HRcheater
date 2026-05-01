import asyncio
import os
import tempfile
import logging

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    FSInputFile,
)

from config import TELEGRAM_BOT_TOKEN
from parser import (
    extract_from_pdf,
    extract_from_docx,
    prepare_resume_text,
    prepare_vacancy_text,
    TextTooLongError,
)
from openai_client import run_agent
from pdf_generator import generate_pdf
from prompts import GRADE_INSTRUCTIONS, DIRECTION_INSTRUCTIONS
from hh_parser import fetch_vacancy, extract_vacancy_id, HHParseError
from resume_parser import fetch_resume_from_url, is_url, ResumeParseError

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())


# ── FSM States ────────────────────────────────────────────────────────────────

class Form(StatesGroup):
    upload_resume = State()
    upload_vacancy = State()
    q_direction = State()
    q_grade = State()
    processing = State()


# ── Keyboard helpers ──────────────────────────────────────────────────────────

def make_keyboard(options: list[str]) -> InlineKeyboardMarkup:
    buttons = [[InlineKeyboardButton(text=o, callback_data=o)] for o in options]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


DIRECTIONS = list(DIRECTION_INSTRUCTIONS.keys())
GRADES = list(GRADE_INSTRUCTIONS.keys())


# ── Handlers ──────────────────────────────────────────────────────────────────

@dp.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(Form.upload_resume)
    await message.answer(
        "Привет! Я помогу адаптировать твоё резюме под вакансию.\n\n"
        "Шаг 1 из 4. Отправь резюме одним из способов:\n"
        "• Файл PDF или DOCX\n"
        "• Ссылка с hh.ru (hh.ru/resume/...)\n"
        "• Ссылка на публичную страницу (портфолио и т.д.)\n"
        "• Просто текст"
    )


# Step 1 — Resume upload
@dp.message(Form.upload_resume)
async def handle_resume(message: Message, state: FSMContext):
    resume_text = None
    from_url = False

    if message.document:
        file = message.document
        suffix = os.path.splitext(file.file_name or "")[1].lower()

        if suffix not in (".pdf", ".docx"):
            await message.answer("Поддерживаются только PDF и DOCX. Попробуй ещё раз.")
            return

        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            await bot.download(file, destination=tmp.name)
            tmp_path = tmp.name

        try:
            if suffix == ".pdf":
                resume_text = extract_from_pdf(tmp_path)
            else:
                resume_text = extract_from_docx(tmp_path)
        except ValueError as e:
            await message.answer(str(e))
            return
        finally:
            os.unlink(tmp_path)

    elif message.text:
        raw = message.text.strip()
        if is_url(raw):
            await message.answer("Загружаю резюме по ссылке...")
            try:
                resume_text = await fetch_resume_from_url(raw)
            except ResumeParseError as e:
                await message.answer(str(e))
                return
            from_url = True
        else:
            resume_text = raw
            from_url = False
    else:
        await message.answer("Пожалуйста, отправь файл, ссылку или текст резюме.")
        return

    try:
        resume_text = prepare_resume_text(resume_text, from_url=from_url)
    except TextTooLongError as e:
        await message.answer(str(e))
        return

    await state.update_data(resume_text=resume_text)
    await state.set_state(Form.upload_vacancy)
    await message.answer(
        "Шаг 2 из 4. Отправь вакансию — текстом или ссылкой с hh.ru.\n\n"
        "Пример: https://hh.ru/vacancy/12345678"
    )


# Step 2 — Vacancy
@dp.message(Form.upload_vacancy)
async def handle_vacancy(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("Пожалуйста, отправь текст вакансии или ссылку с hh.ru.")
        return

    raw_text = message.text.strip()

    vacancy_from_url = False
    if extract_vacancy_id(raw_text):
        await message.answer("Получаю вакансию с hh.ru...")
        try:
            raw_text = await fetch_vacancy(raw_text)
        except HHParseError as e:
            await message.answer(f"Не удалось загрузить вакансию: {e}\n\nПопробуй скопировать текст вручную.")
            return
        vacancy_from_url = True

    try:
        vacancy_text = prepare_vacancy_text(raw_text, from_url=vacancy_from_url)
    except TextTooLongError as e:
        await message.answer(str(e))
        return

    await state.update_data(vacancy_text=vacancy_text)
    await state.set_state(Form.q_direction)
    await message.answer(
        "Шаг 3 из 4. Выбери направление:",
        reply_markup=make_keyboard(DIRECTIONS),
    )


# Step 3 — Direction
@dp.callback_query(Form.q_direction)
async def handle_direction(call: CallbackQuery, state: FSMContext):
    await call.answer()
    await state.update_data(direction=call.data)
    await state.set_state(Form.q_grade)
    await call.message.answer(
        "Шаг 4 из 4. Выбери целевой грейд:",
        reply_markup=make_keyboard(GRADES),
    )


# Step 4 — Grade → сразу запуск
@dp.callback_query(Form.q_grade)
async def handle_grade(call: CallbackQuery, state: FSMContext):
    await call.answer()
    await state.update_data(grade=call.data)
    await state.set_state(Form.processing)

    data = await state.get_data()
    await call.message.answer("Анализирую и адаптирую резюме... Это займёт ~15 секунд.")

    try:
        result = await run_agent(
            grade=data["grade"],
            direction=data["direction"],
            resume_text=data["resume_text"],
            vacancy_text=data["vacancy_text"],
            extra_prefs={},
        )
    except Exception as e:
        logging.exception("LLM error")
        await call.message.answer(f"Ошибка при обращении к модели: {e}\nПопробуй ещё раз — /start")
        await state.clear()
        return

    # Score
    score_msg = (
        f"Оценка соответствия: {result.score}/10\n\n"
        f"{result.score_reasoning}"
    )
    await call.message.answer(score_msg)

    # Gap report
    gap = result.gap_report
    gap_parts = []

    if gap.strengths:
        lines = "\n".join(f"  ✅ {s}" for s in gap.strengths)
        gap_parts.append(f"*Что совпадает с вакансией:*\n{lines}")

    if gap.gaps:
        lines = "\n".join(f"  ❌ {g}" for g in gap.gaps)
        gap_parts.append(f"*Чего не хватает:*\n{lines}")

    if gap.reframeable:
        lines = "\n".join(f"  🔄 {r}" for r in gap.reframeable)
        gap_parts.append(f"*Можно переформулировать под вакансию:*\n{lines}")

    if gap_parts:
        await call.message.answer(
            "📋 *Анализ соответствия:*\n\n" + "\n\n".join(gap_parts),
            parse_mode="Markdown",
        )

    # PDF
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        pdf_path = tmp.name

    try:
        generate_pdf(result.resume, pdf_path)
        pdf_file = FSInputFile(pdf_path, filename="resume_adapted.pdf")
        await call.message.answer_document(pdf_file, caption="Адаптированное резюме")
    except Exception as e:
        logging.exception("PDF generation error")
        await call.message.answer(f"Ошибка при генерации PDF: {e}")
    finally:
        os.unlink(pdf_path)

    await state.clear()
    await call.message.answer("Готово! Чтобы начать заново — /start")


# ── Entry point ───────────────────────────────────────────────────────────────

async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

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

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())


# ── FSM States ────────────────────────────────────────────────────────────────

class Form(StatesGroup):
    upload_resume = State()
    upload_vacancy = State()
    q_direction = State()
    q_grade = State()
    q_stack = State()
    q_company_size = State()
    q_role = State()
    q_country = State()
    processing = State()


# ── Keyboard helpers ──────────────────────────────────────────────────────────

def make_keyboard(options: list[str], skip: bool = False) -> InlineKeyboardMarkup:
    buttons = [[InlineKeyboardButton(text=o, callback_data=o)] for o in options]
    if skip:
        buttons.append([InlineKeyboardButton(text="Пропустить", callback_data="__skip__")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


DIRECTIONS = list(DIRECTION_INSTRUCTIONS.keys())
GRADES = list(GRADE_INSTRUCTIONS.keys())

STACKS = [
    "Python", "JavaScript / TypeScript", "Java", "Go", "C# / .NET",
    "Swift / iOS", "Kotlin / Android", "PHP", "Ruby", "Rust", "Другой",
]
COMPANY_SIZES = ["Стартап (до 50)", "Средняя (50–500)", "Корпорация (500+)", "Без разницы"]
ROLES = ["Разработчик (IC)", "Тимлид", "Архитектор", "Без разницы"]
COUNTRIES = ["Россия", "СНГ", "Европа", "США / Канада", "Без разницы"]


# ── Handlers ──────────────────────────────────────────────────────────────────

@dp.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(Form.upload_resume)
    await message.answer(
        "Привет! Я помогу адаптировать твоё резюме под вакансию.\n\n"
        "Шаг 1 из 8. Отправь резюме — файлом (PDF или DOCX) или текстом."
    )


# Step 1 — Resume upload
@dp.message(Form.upload_resume)
async def handle_resume(message: Message, state: FSMContext):
    resume_text = None

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
        resume_text = message.text
    else:
        await message.answer("Пожалуйста, отправь файл или текст резюме.")
        return

    try:
        resume_text = prepare_resume_text(resume_text)
    except TextTooLongError as e:
        await message.answer(str(e))
        return

    await state.update_data(resume_text=resume_text)
    await state.set_state(Form.upload_vacancy)
    await message.answer("Шаг 2 из 8. Теперь отправь текст вакансии.")


# Step 2 — Vacancy
@dp.message(Form.upload_vacancy)
async def handle_vacancy(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("Пожалуйста, отправь текст вакансии.")
        return

    try:
        vacancy_text = prepare_vacancy_text(message.text)
    except TextTooLongError as e:
        await message.answer(str(e))
        return

    await state.update_data(vacancy_text=vacancy_text)
    await state.set_state(Form.q_direction)
    await message.answer(
        "Шаг 3 из 8. Выбери направление:",
        reply_markup=make_keyboard(DIRECTIONS),
    )


# Step 3 — Direction
@dp.callback_query(Form.q_direction)
async def handle_direction(call: CallbackQuery, state: FSMContext):
    await call.answer()
    await state.update_data(direction=call.data)
    await state.set_state(Form.q_grade)
    await call.message.answer(
        "Шаг 4 из 8. Выбери грейд:",
        reply_markup=make_keyboard(GRADES),
    )


# Step 4 — Grade
@dp.callback_query(Form.q_grade)
async def handle_grade(call: CallbackQuery, state: FSMContext):
    await call.answer()
    await state.update_data(grade=call.data)
    await state.set_state(Form.q_stack)
    await call.message.answer(
        "Шаг 5 из 8. Желаемый стек технологий:",
        reply_markup=make_keyboard(STACKS, skip=True),
    )


# Step 5 — Stack (optional)
@dp.callback_query(Form.q_stack)
async def handle_stack(call: CallbackQuery, state: FSMContext):
    await call.answer()
    value = None if call.data == "__skip__" else call.data
    await state.update_data(stack=value)
    await state.set_state(Form.q_company_size)
    await call.message.answer(
        "Шаг 6 из 8. Размер компании:",
        reply_markup=make_keyboard(COMPANY_SIZES, skip=True),
    )


# Step 6 — Company size (optional)
@dp.callback_query(Form.q_company_size)
async def handle_company_size(call: CallbackQuery, state: FSMContext):
    await call.answer()
    value = None if call.data == "__skip__" else call.data
    await state.update_data(company_size=value)
    await state.set_state(Form.q_role)
    await call.message.answer(
        "Шаг 7 из 8. Желаемая роль:",
        reply_markup=make_keyboard(ROLES, skip=True),
    )


# Step 7 — Role (optional)
@dp.callback_query(Form.q_role)
async def handle_role(call: CallbackQuery, state: FSMContext):
    await call.answer()
    value = None if call.data == "__skip__" else call.data
    await state.update_data(role=value)
    await state.set_state(Form.q_country)
    await call.message.answer(
        "Шаг 8 из 8. Целевой рынок:",
        reply_markup=make_keyboard(COUNTRIES, skip=True),
    )


# Step 8 — Country (optional) → trigger processing
@dp.callback_query(Form.q_country)
async def handle_country(call: CallbackQuery, state: FSMContext):
    await call.answer()
    value = None if call.data == "__skip__" else call.data
    await state.update_data(country=value)
    await state.set_state(Form.processing)

    data = await state.get_data()
    await call.message.answer("Генерирую резюме... Это займёт около 30 секунд.")

    extra_prefs = {
        "stack": data.get("stack"),
        "company_size": data.get("company_size"),
        "role": data.get("role"),
        "country": data.get("country"),
    }

    try:
        result = await run_agent(
            grade=data["grade"],
            direction=data["direction"],
            resume_text=data["resume_text"],
            vacancy_text=data["vacancy_text"],
            extra_prefs=extra_prefs,
        )
    except Exception as e:
        logging.exception("LLM error")
        await call.message.answer(f"Ошибка при обращении к модели: {e}\nПопробуй ещё раз — /start")
        await state.clear()
        return

    # Send score
    score_msg = (
        f"Оценка соответствия: {result.score}/10\n\n"
        f"{result.score_reasoning}"
    )
    await call.message.answer(score_msg)

    # Generate and send PDF
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

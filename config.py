import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
FONT_PATH = os.getenv("FONT_PATH", "DejaVuSans.ttf")
FONT_BOLD_PATH = os.getenv("FONT_BOLD_PATH", "DejaVuSans-Bold.ttf")
RESUME_MAX_CHARS = int(os.getenv("RESUME_MAX_CHARS", 4000))
VACANCY_MAX_CHARS = int(os.getenv("VACANCY_MAX_CHARS", 4000))

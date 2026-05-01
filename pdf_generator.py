import os
import random
from fpdf import FPDF
from config import FONT_PATH, FONT_BOLD_PATH
from openai_client import ResumeData

# ── Палитры (accent, accent_light, divider) ───────────────────────────────────
_PALETTES = [
    {"name": "Navy",    "accent": (31,  73,  125), "light": (235, 241, 250), "divider": (180, 195, 215)},
    {"name": "Forest",  "accent": (34,  85,  56),  "light": (236, 245, 239), "divider": (170, 205, 180)},
    {"name": "Slate",   "accent": (55,  71,  90),  "light": (238, 241, 245), "divider": (180, 190, 205)},
    {"name": "Plum",    "accent": (90,  50,  115),  "light": (243, 238, 250), "divider": (200, 180, 220)},
    {"name": "Rust",    "accent": (140, 60,  40),  "light": (250, 241, 238), "divider": (215, 185, 175)},
    {"name": "Teal",    "accent": (25,  105, 110), "light": (234, 246, 247), "divider": (165, 210, 213)},
    {"name": "Graphite","accent": (50,  50,  50),  "light": (242, 242, 242), "divider": (190, 190, 190)},
    {"name": "Indigo",  "accent": (55,  60,  145), "light": (237, 238, 252), "divider": (175, 178, 225)},
]

def _pick_palette() -> dict:
    return random.choice(_PALETTES)

# Глобальные переменные палитры — переназначаются при каждой генерации
ACCENT       = (31, 73, 125)
ACCENT_LIGHT = (235, 241, 250)
DIVIDER      = (180, 195, 215)
TEXT_DARK    = (30, 30, 30)
TEXT_MUTED   = (100, 100, 110)
WHITE        = (255, 255, 255)

# ── Геометрия страницы ────────────────────────────────────────────────────────
PAGE_W       = 210
PAGE_H       = 297
MARGIN       = 0
HEADER_H     = 34         # было 42
SIDEBAR_W    = 58         # было 62
SIDEBAR_X    = 0
MAIN_X       = SIDEBAR_W + 6   # было +8
MAIN_W       = PAGE_W - MAIN_X - 8   # было -10
PAD          = 5          # было 7


class ResumePDF(FPDF):
    def __init__(self):
        super().__init__()
        self.set_margins(0, 0, 0)
        self.set_auto_page_break(auto=True, margin=12)

        font_path = FONT_PATH
        font_bold = FONT_BOLD_PATH
        if not os.path.exists(font_path):
            font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
        if not os.path.exists(font_bold):
            font_bold = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

        self.add_font("CV", "",  font_path)
        self.add_font("CV", "B", font_bold)

    # ── helpers ───────────────────────────────────────────────────────────────

    def _rgb(self, color: tuple):
        return color

    def set_text(self, color=TEXT_DARK, size=10, bold=False):
        self.set_text_color(*color)
        self.set_font("CV", "B" if bold else "", size)

    def _divider(self, x, y, w, color=DIVIDER):
        self.set_draw_color(*color)
        self.set_line_width(0.3)
        self.line(x, y, x + w, y)

    def sidebar_section(self, title: str):
        """Заголовок раздела в сайдбаре."""
        self.set_text(ACCENT, 8, bold=True)
        y = self.get_y() + 3
        self.set_xy(SIDEBAR_X + PAD, y)
        self.cell(SIDEBAR_W - PAD * 2, 5, title.upper(), ln=True)
        self._divider(SIDEBAR_X + PAD, self.get_y(), SIDEBAR_W - PAD * 2, ACCENT)
        self.ln(2)

    def main_section(self, title: str):
        """Заголовок раздела в основной колонке."""
        y = self.get_y() + 4
        self.set_xy(MAIN_X, y)
        self.set_text(ACCENT, 10, bold=True)
        self.cell(MAIN_W, 6, title.upper(), ln=False)
        self.ln(1)
        self._divider(MAIN_X, self.get_y(), MAIN_W, ACCENT)
        self.ln(3)


def generate_pdf(resume: ResumeData, output_path: str):
    global ACCENT, ACCENT_LIGHT, DIVIDER
    palette = _pick_palette()
    ACCENT, ACCENT_LIGHT, DIVIDER = palette["accent"], palette["light"], palette["divider"]

    pdf = ResumePDF()
    pdf.add_page()

    # ══════════════════════════════════════════════════════════════════════════
    # ХЕДЕР — цветная полоса на всю ширину
    # ══════════════════════════════════════════════════════════════════════════
    pdf.set_fill_color(*ACCENT)
    pdf.rect(0, 0, PAGE_W, HEADER_H, "F")

    # Имя
    pdf.set_xy(MAIN_X, 8)
    pdf.set_text(WHITE, 17, bold=True)
    pdf.cell(MAIN_W, 9, resume.name, ln=True)

    # Контакты под именем
    pdf.set_xy(MAIN_X, 19)
    pdf.set_text(WHITE, 8)
    pdf.cell(MAIN_W, 5, resume.contacts, ln=True)

    # ══════════════════════════════════════════════════════════════════════════
    # ФОН САЙДБАРА
    # ══════════════════════════════════════════════════════════════════════════
    sidebar_content_h = PAGE_H - HEADER_H
    pdf.set_fill_color(*ACCENT_LIGHT)
    pdf.rect(SIDEBAR_X, HEADER_H, SIDEBAR_W, sidebar_content_h, "F")

    # ══════════════════════════════════════════════════════════════════════════
    # САЙДБАР — навыки
    # ══════════════════════════════════════════════════════════════════════════
    pdf.set_xy(SIDEBAR_X + PAD, HEADER_H + 5)

    pdf.sidebar_section("Навыки")
    for skill in resume.skills:
        pdf.set_xy(SIDEBAR_X + PAD, pdf.get_y())
        badge_w = SIDEBAR_W - PAD * 2
        badge_h = 5.0          # было 5.5
        bx = SIDEBAR_X + PAD
        by = pdf.get_y()
        pdf.set_fill_color(220, 230, 245)
        pdf.rect(bx, by, badge_w, badge_h, "F")
        pdf.set_text(ACCENT, 7.5)   # было 8
        pdf.set_xy(bx + 2, by + 0.6)
        pdf.cell(badge_w - 4, badge_h - 1.2, skill, ln=True)
        pdf.ln(0.5)                 # было 1

    # Образование в сайдбаре
    if resume.education:
        pdf.ln(1)
        pdf.set_xy(SIDEBAR_X + PAD, pdf.get_y())
        pdf.sidebar_section("Образование")
        for edu in resume.education:
            pdf.set_xy(SIDEBAR_X + PAD, pdf.get_y())
            pdf.set_text(TEXT_DARK, 7.5, bold=True)   # было 8
            pdf.multi_cell(SIDEBAR_W - PAD * 2, 4, edu.institution)
            pdf.set_xy(SIDEBAR_X + PAD, pdf.get_y())
            pdf.set_text(TEXT_MUTED, 7)                # было 7.5
            pdf.multi_cell(SIDEBAR_W - PAD * 2, 3.8, edu.degree)
            pdf.set_xy(SIDEBAR_X + PAD, pdf.get_y())
            pdf.set_text(ACCENT, 7, bold=True)
            pdf.cell(SIDEBAR_W - PAD * 2, 3.8, edu.year, ln=True)
            pdf.ln(1.5)                                # было 2

    # ══════════════════════════════════════════════════════════════════════════
    # ОСНОВНАЯ КОЛОНКА — summary + опыт
    # ══════════════════════════════════════════════════════════════════════════
    pdf.set_xy(MAIN_X, HEADER_H + 4)

    # О себе
    if resume.summary:
        pdf.main_section("О себе")
        pdf.set_xy(MAIN_X, pdf.get_y())
        pdf.set_text(TEXT_DARK, 8.5)       # было 9
        pdf.multi_cell(MAIN_W, 4.5, resume.summary)   # было 5
        pdf.ln(1)                          # было 2

    # Опыт работы
    if resume.experience:
        pdf.set_xy(MAIN_X, pdf.get_y())
        pdf.main_section("Опыт работы")

        for i, exp in enumerate(resume.experience):
            pdf.set_xy(MAIN_X, pdf.get_y())
            pdf.set_text(TEXT_DARK, 9, bold=True)      # было 9.5
            pdf.cell(MAIN_W, 5, exp.role, ln=False)    # было 5.5
            pdf.ln(5)

            pdf.set_xy(MAIN_X, pdf.get_y())
            pdf.set_text(ACCENT, 8)                    # было 8.5
            pdf.cell(MAIN_W * 0.55, 4, exp.company, ln=False)  # было 4.5
            pdf.set_text(TEXT_MUTED, 7.5)              # было 8
            pdf.cell(MAIN_W * 0.45, 4, f"{exp.start} – {exp.end}", ln=True, align="R")

            pdf.set_xy(MAIN_X, pdf.get_y() + 0.5)     # было +1
            pdf.set_text(TEXT_DARK, 8)                 # было 8.5
            pdf.multi_cell(MAIN_W, 4.3, exp.description)  # было 4.8

            if i < len(resume.experience) - 1:
                pdf.ln(0.5)                            # было 1
                pdf._divider(MAIN_X, pdf.get_y(), MAIN_W, DIVIDER)
                pdf.ln(2.5)                            # было 3
            else:
                pdf.ln(1)                              # было 2

    pdf.output(output_path)

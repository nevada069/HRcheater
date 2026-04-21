import os
from fpdf import FPDF
from config import FONT_PATH, FONT_BOLD_PATH
from openai_client import ResumeData


class ResumePDF(FPDF):
    def __init__(self):
        super().__init__()
        self.set_margins(20, 20, 20)
        self.set_auto_page_break(auto=True, margin=20)

        font_path = FONT_PATH
        font_bold_path = FONT_BOLD_PATH

        # Fallback to system DejaVu on Linux
        if not os.path.exists(font_path):
            font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
        if not os.path.exists(font_bold_path):
            font_bold_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

        self.add_font("DejaVu", "", font_path)
        self.add_font("DejaVu", "B", font_bold_path)

    def section_title(self, text: str):
        self.set_font("DejaVu", "B", 11)
        self.set_fill_color(240, 240, 240)
        self.cell(0, 8, text.upper(), fill=True, ln=True)
        self.ln(1)

    def body_text(self, text: str, size: int = 10):
        self.set_font("DejaVu", "", size)
        self.multi_cell(0, 6, text)

    def bold_text(self, text: str, size: int = 10):
        self.set_font("DejaVu", "B", size)
        self.multi_cell(0, 6, text)


def generate_pdf(resume: ResumeData, output_path: str):
    pdf = ResumePDF()
    pdf.add_page()

    # Name
    pdf.set_font("DejaVu", "B", 16)
    pdf.cell(0, 10, resume.name, ln=True, align="C")
    pdf.ln(1)

    # Contacts
    pdf.set_font("DejaVu", "", 9)
    pdf.cell(0, 6, resume.contacts, ln=True, align="C")
    pdf.ln(4)

    # Summary
    pdf.section_title("О себе")
    pdf.body_text(resume.summary)
    pdf.ln(4)

    # Experience
    pdf.section_title("Опыт работы")
    for exp in resume.experience:
        pdf.set_font("DejaVu", "B", 10)
        pdf.cell(0, 6, f"{exp.role} — {exp.company}", ln=True)
        pdf.set_font("DejaVu", "", 9)
        pdf.cell(0, 5, f"{exp.start} – {exp.end}", ln=True)
        pdf.set_font("DejaVu", "", 10)
        pdf.multi_cell(0, 6, exp.description)
        pdf.ln(3)

    # Skills
    pdf.section_title("Навыки")
    skills_text = "  •  ".join(resume.skills)
    pdf.body_text(skills_text)
    pdf.ln(4)

    # Education
    pdf.section_title("Образование")
    for edu in resume.education:
        pdf.set_font("DejaVu", "B", 10)
        pdf.cell(0, 6, edu.institution, ln=True)
        pdf.set_font("DejaVu", "", 10)
        pdf.cell(0, 5, f"{edu.degree}, {edu.year}", ln=True)
        pdf.ln(2)

    pdf.output(output_path)

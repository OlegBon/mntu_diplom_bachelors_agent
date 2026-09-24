"""Server-side PDF rendering for the public, allow-listed diamond passport."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from typing import Mapping, Sequence
from zoneinfo import ZoneInfo

import qrcode
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

from .schemas import PublicPassportView

PAGE_WIDTH, PAGE_HEIGHT = A4
MARGIN = 42
FONT_REGULAR = "DiamondPassportRegular"
FONT_BOLD = "DiamondPassportBold"
_FONT_DIRECTORY = Path(__file__).resolve().parent / "assets" / "fonts"

ORIGIN_LABELS = {
    "natural": "Природний",
    "lab_grown": "Лабораторно вирощений",
    "unknown": "Не визначено",
    "other": "Інше",
}
TREATMENT_LABELS = {
    "not_assessed": "Не оцінено",
    "none_detected": "Не виявлено",
    "disclosed": "Заявлено",
    "confirmed": "Підтверджено",
}
IDENTIFICATION_LABELS = {
    "preliminary": "Попередній",
    "confirmed": "Підтверджено",
    "inconclusive": "Невизначено",
}

MEDIA_LABELS = {
    "stone_photo": "Фото каменю",
    "plotting_diagram": "Схема огранювання",
}


@dataclass(frozen=True)
class PublicPassportPdfMedia:
    """Already-authorized public image bytes for one on-demand PDF."""

    asset_type: str
    content: bytes


def _register_fonts() -> None:
    """Register bundled Unicode fonts without a dependency on the host system."""
    if FONT_REGULAR not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont(FONT_REGULAR, str(_FONT_DIRECTORY / "DejaVuSans.ttf")))
        pdfmetrics.registerFont(TTFont(FONT_BOLD, str(_FONT_DIRECTORY / "DejaVuSans-Bold.ttf")))


def _format_date(value) -> str:
    return value.strftime("%d.%m.%Y") if value else "—"


def _grade_label(grade_labels: Mapping[tuple[str, int], str], category: str, value: int | None) -> str:
    return grade_labels.get((category, value), "—") if value is not None else "—"


def _draw_label_value(document: canvas.Canvas, x: float, y: float, label: str, value: str) -> float:
    document.setFillColor(colors.HexColor("#64748b"))
    document.setFont(FONT_REGULAR, 8.5)
    document.drawString(x, y, label)
    document.setFillColor(colors.HexColor("#0f172a"))
    document.setFont(FONT_BOLD, 10.5)
    document.drawString(x, y - 14, value)
    return y - 38


def _draw_media_page(document: canvas.Canvas, media: PublicPassportPdfMedia) -> bool:
    """Draw a single proportional public image page; skip unreadable image bytes."""
    label = MEDIA_LABELS.get(media.asset_type)
    if label is None:
        return False
    try:
        image = ImageReader(BytesIO(media.content))
        image_width, image_height = image.getSize()
    except Exception:  # ImageReader normalizes decoder-specific errors.
        return False
    if image_width <= 0 or image_height <= 0:
        return False

    document.setFillColor(colors.HexColor("#2563eb"))
    document.rect(0, PAGE_HEIGHT - 12, PAGE_WIDTH, 12, fill=1, stroke=0)
    document.setFillColor(colors.HexColor("#0f172a"))
    document.setFont(FONT_BOLD, 18)
    document.drawString(MARGIN, PAGE_HEIGHT - 52, "Зображення каменю")
    document.setFont(FONT_REGULAR, 10)
    document.setFillColor(colors.HexColor("#64748b"))
    document.drawString(MARGIN, PAGE_HEIGHT - 70, label)

    max_width = PAGE_WIDTH - (MARGIN * 2)
    max_height = PAGE_HEIGHT - 178
    scale = min(max_width / image_width, max_height / image_height)
    draw_width = image_width * scale
    draw_height = image_height * scale
    image_x = (PAGE_WIDTH - draw_width) / 2
    image_y = 86 + (max_height - draw_height) / 2
    document.drawImage(image, image_x, image_y, draw_width, draw_height, preserveAspectRatio=True, mask="auto")
    document.setFillColor(colors.HexColor("#64748b"))
    document.setFont(FONT_REGULAR, 7.5)
    document.drawCentredString(PAGE_WIDTH / 2, 48, "Матеріал доступний у чинному публічному паспорті на момент формування PDF.")
    document.showPage()
    return True


def build_public_passport_pdf(
    passport: PublicPassportView,
    public_url: str,
    grade_labels: Mapping[tuple[str, int], str],
    public_media: Sequence[PublicPassportPdfMedia] = (),
) -> bytes:
    """Render one public passport PDF from the explicit anonymous projection only."""
    _register_fonts()
    output = BytesIO()
    document = canvas.Canvas(output, pagesize=A4, pageCompression=1)
    document.setTitle(f"Публічний паспорт {passport.report_id}")
    document.setAuthor("Diamant ID")
    document.setSubject("Публічний паспорт діаманта")

    document.setFillColor(colors.HexColor("#2563eb"))
    document.rect(0, PAGE_HEIGHT - 12, PAGE_WIDTH, 12, fill=1, stroke=0)
    document.setFillColor(colors.HexColor("#0f172a"))
    document.setFont(FONT_BOLD, 22)
    document.drawString(MARGIN, PAGE_HEIGHT - 58, "Публічний паспорт")
    document.setFillColor(colors.HexColor("#64748b"))
    document.setFont(FONT_REGULAR, 10)
    document.drawString(MARGIN, PAGE_HEIGHT - 76, "Diamant ID · перевіряйте чинність за кодом, посиланням або QR")

    card_top = PAGE_HEIGHT - 102
    document.setStrokeColor(colors.HexColor("#e2e8f0"))
    document.setFillColor(colors.white)
    document.roundRect(MARGIN, card_top - 106, PAGE_WIDTH - MARGIN * 2, 106, 0, fill=1, stroke=1)
    document.setFillColor(colors.HexColor("#64748b"))
    document.setFont(FONT_REGULAR, 9)
    document.drawString(MARGIN + 18, card_top - 25, "Номер звіту")
    document.setFillColor(colors.HexColor("#0f172a"))
    document.setFont(FONT_BOLD, 18)
    document.drawString(MARGIN + 18, card_top - 47, passport.report_id)
    document.setFillColor(colors.HexColor("#64748b"))
    document.setFont(FONT_REGULAR, 9)
    document.drawString(MARGIN + 18, card_top - 69, f"Дата видачі: {_format_date(passport.issued_at)}")
    document.drawString(MARGIN + 18, card_top - 86, f"Дата дослідження: {_format_date(passport.examination_date)}")

    qr_image = qrcode.make(public_url).get_image()
    document.drawImage(ImageReader(qr_image), PAGE_WIDTH - MARGIN - 86, card_top - 91, 72, 72, mask="auto")
    document.setFont(FONT_REGULAR, 7.5)
    document.drawRightString(PAGE_WIDTH - MARGIN - 14, card_top - 99, "Скануйте для перевірки")

    section_top = card_top - 136
    document.setFillColor(colors.HexColor("#0f172a"))
    document.setFont(FONT_BOLD, 13)
    document.drawString(MARGIN, section_top, "Характеристики каменю")
    left_x = MARGIN
    right_x = PAGE_WIDTH / 2 + 12
    y = section_top - 24
    _draw_label_value(document, left_x, y, "Форма", passport.shape)
    _draw_label_value(document, right_x, y, "Вага", f"{passport.carat_weight} ct")
    y -= 38
    _draw_label_value(document, left_x, y, "Колір", _grade_label(grade_labels, "color", passport.color_grade))
    _draw_label_value(document, right_x, y, "Чистота", _grade_label(grade_labels, "clarity", passport.clarity_grade))
    y -= 38
    dimensions = " × ".join(str(value) if value is not None else "—" for value in (
        passport.measurements_length,
        passport.measurements_width,
        passport.measurements_depth,
    ))
    _draw_label_value(document, left_x, y, "Розміри", f"{dimensions} mm")
    _draw_label_value(document, right_x, y, "Походження", ORIGIN_LABELS.get(str(passport.origin), "—"))

    grades_top = section_top - 148
    document.setStrokeColor(colors.HexColor("#e2e8f0"))
    document.line(MARGIN, grades_top + 20, PAGE_WIDTH - MARGIN, grades_top + 20)
    document.setFillColor(colors.HexColor("#0f172a"))
    document.setFont(FONT_BOLD, 13)
    document.drawString(MARGIN, grades_top, "Оцінки та ідентифікація")
    y = grades_top - 24
    _draw_label_value(document, left_x, y, "Системний Proportions", _grade_label(grade_labels, "proportions", passport.system_proportions_grade))
    _draw_label_value(document, right_x, y, "Системний Final Cut", _grade_label(grade_labels, "cut", passport.system_cut_grade))
    y -= 38
    _draw_label_value(document, left_x, y, "Підтверджений Proportions", _grade_label(grade_labels, "proportions", passport.expert_proportions_grade))
    _draw_label_value(document, right_x, y, "Підсумковий Final Cut", _grade_label(grade_labels, "cut", passport.expert_cut_grade))
    y -= 38
    _draw_label_value(document, left_x, y, "Ознаки обробки", TREATMENT_LABELS.get(str(passport.treatment_status), "—"))
    _draw_label_value(document, right_x, y, "Рівень підтвердження", IDENTIFICATION_LABELS.get(str(passport.identification_status), "—"))

    footer_top = 98
    document.setStrokeColor(colors.HexColor("#e2e8f0"))
    document.line(MARGIN, footer_top + 42, PAGE_WIDTH - MARGIN, footer_top + 42)
    document.setFillColor(colors.HexColor("#0f172a"))
    document.setFont(FONT_BOLD, 9)
    document.drawString(MARGIN, footer_top + 24, "Код публічного паспорта")
    document.setFont(FONT_REGULAR, 8.5)
    document.drawString(MARGIN, footer_top + 10, passport.public_id)
    document.setFillColor(colors.HexColor("#64748b"))
    document.setFont(FONT_REGULAR, 7.5)
    document.drawString(MARGIN, footer_top - 7, public_url)
    generated_at = datetime.now(timezone.utc).astimezone(ZoneInfo("Europe/Kyiv")).strftime("%d.%m.%Y %H:%M")
    document.drawString(MARGIN, 62, f"Сформовано: {generated_at} (Europe/Kyiv)")
    document.drawString(MARGIN, 48, "PDF містить лише публічно доступні дані. Перевіряйте стан за кодом, посиланням або QR.")
    document.showPage()
    ordered_media = sorted(public_media, key=lambda item: (item.asset_type != "stone_photo", item.asset_type))
    for media in ordered_media:
        _draw_media_page(document, media)
    document.save()
    return output.getvalue()

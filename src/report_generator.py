import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    BaseDocTemplate,
    PageTemplate,
    Frame,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    HRFlowable,
)
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REPORTS_DIR = PROJECT_ROOT / "reports"


# ============================================================
# PAGE CONFIGURATION
# ============================================================

# A4 page

PAGE_WIDTH, PAGE_HEIGHT = A4

LEFT_MARGIN = 18 * mm
RIGHT_MARGIN = 18 * mm
TOP_MARGIN = 22 * mm
BOTTOM_MARGIN = 18 * mm


# ============================================================
# FONTS
# ============================================================

def register_fonts():
    """
    Use Inter when available.
    Otherwise fall back to standard Helvetica fonts.
    """

    windows_fonts = Path("C:/Windows/Fonts")

    regular = windows_fonts / "Inter-Regular.ttf"
    bold = windows_fonts / "Inter-Bold.ttf"

    if regular.exists() and bold.exists():

        pdfmetrics.registerFont(
            TTFont(
                "Inter",
                str(regular)
            )
        )

        pdfmetrics.registerFont(
            TTFont(
                "Inter-Bold",
                str(bold)
            )
        )

        return "Inter", "Inter-Bold"

    return "Helvetica", "Helvetica-Bold"


BODY_FONT, BOLD_FONT = register_fonts()


# ============================================================
# COLOR THEME
# ============================================================

# Professional financial-report theme

NAVY = colors.HexColor("#0B1F33")
BLUE = colors.HexColor("#1769AA")
LIGHT_BLUE = colors.HexColor("#EAF3F8")

DARK_TEXT = colors.HexColor("#243447")
MUTED_TEXT = colors.HexColor("#66788A")

LIGHT_GREY = colors.HexColor("#F5F7F9")
MID_GREY = colors.HexColor("#D5DDE5")

WHITE = colors.white


# ============================================================
# STYLES
# ============================================================

styles = getSampleStyleSheet()


# ------------------------------------------------------------
# Main report title
# ------------------------------------------------------------

TITLE_STYLE = ParagraphStyle(
    "ReportTitle",
    fontName=BOLD_FONT,
    fontSize=24,
    leading=30,
    textColor=NAVY,
    alignment=TA_LEFT,
    spaceAfter=10,
)


# ------------------------------------------------------------
# Subtitle
# ------------------------------------------------------------

SUBTITLE_STYLE = ParagraphStyle(
    "ReportSubtitle",
    fontName=BODY_FONT,
    fontSize=11.5,
    leading=16,
    textColor=MUTED_TEXT,
    spaceAfter=22,
)


# ------------------------------------------------------------
# Major section heading
# ------------------------------------------------------------

H1_STYLE = ParagraphStyle(
    "H1",
    fontName=BOLD_FONT,
    fontSize=18,
    leading=23,
    textColor=NAVY,
    spaceBefore=20,
    spaceAfter=11,
)


# ------------------------------------------------------------
# Subheading
# ------------------------------------------------------------

H2_STYLE = ParagraphStyle(
    "H2",
    fontName=BOLD_FONT,
    fontSize=14,
    leading=19,
    textColor=BLUE,
    spaceBefore=16,
    spaceAfter=9,
)


# ------------------------------------------------------------
# Smaller subheading
# ------------------------------------------------------------

H3_STYLE = ParagraphStyle(
    "H3",
    fontName=BOLD_FONT,
    fontSize=11.5,
    leading=16,
    textColor=DARK_TEXT,
    spaceBefore=12,
    spaceAfter=6,
)


# ------------------------------------------------------------
# Normal body text
# ------------------------------------------------------------

BODY_STYLE = ParagraphStyle(
    "Body",
    fontName=BODY_FONT,
    fontSize=10,
    leading=16,
    textColor=DARK_TEXT,
    spaceAfter=10,
)


# ------------------------------------------------------------
# Small text
# ------------------------------------------------------------

SMALL_STYLE = ParagraphStyle(
    "Small",
    fontName=BODY_FONT,
    fontSize=8,
    leading=11,
    textColor=MUTED_TEXT,
)


# ------------------------------------------------------------
# Bullet points
# ------------------------------------------------------------

BULLET_STYLE = ParagraphStyle(
    "Bullet",
    fontName=BODY_FONT,
    fontSize=9.5,
    leading=15,
    leftIndent=14,
    firstLineIndent=-8,
    textColor=DARK_TEXT,
    spaceAfter=6,
)


# ------------------------------------------------------------
# Callout
# ------------------------------------------------------------

CALLOUT_STYLE = ParagraphStyle(
    "Callout",
    fontName=BODY_FONT,
    fontSize=9.5,
    leading=15,
    textColor=DARK_TEXT,
)


# ------------------------------------------------------------
# Table header
# ------------------------------------------------------------

TABLE_HEADER_STYLE = ParagraphStyle(
    "TableHeader",
    fontName=BOLD_FONT,
    fontSize=8,
    leading=11,
    textColor=WHITE,
)


# ------------------------------------------------------------
# Table body
# ------------------------------------------------------------

TABLE_BODY_STYLE = ParagraphStyle(
    "TableBody",
    fontName=BODY_FONT,
    fontSize=8,
    leading=11,
    textColor=DARK_TEXT,
)


# ------------------------------------------------------------
# Cover styles
# ------------------------------------------------------------

COVER_SMALL_STYLE = ParagraphStyle(
    "CoverSmall",
    fontName=BOLD_FONT,
    fontSize=10,
    leading=13,
    textColor=BLUE,
)


COVER_TITLE_STYLE = ParagraphStyle(
    "CoverTitle",
    fontName=BOLD_FONT,
    fontSize=28,
    leading=33,
    textColor=NAVY,
)


COVER_REPORT_STYLE = ParagraphStyle(
    "CoverReport",
    fontName=BODY_FONT,
    fontSize=13,
    leading=17,
    textColor=MUTED_TEXT,
)


COVER_ACTUAL_TITLE_STYLE = ParagraphStyle(
    "CoverActualTitle",
    fontName=BOLD_FONT,
    fontSize=12,
    leading=16,
    textColor=DARK_TEXT,
)


COVER_ACTUAL_SUBTITLE_STYLE = ParagraphStyle(
    "CoverActualSubtitle",
    fontName=BODY_FONT,
    fontSize=9,
    leading=13,
    textColor=MUTED_TEXT,
)


COVER_COVERAGE_STYLE = ParagraphStyle(
    "CoverCoverage",
    fontName=BOLD_FONT,
    fontSize=7,
    leading=9,
    textColor=MUTED_TEXT,
)


# ============================================================
# TEXT HELPERS
# ============================================================

def escape_xml(text):
    """
    Escape characters used by ReportLab's XML markup.
    """

    text = str(text)

    text = text.replace(
        "&",
        "&amp;"
    )

    text = text.replace(
        "<",
        "&lt;"
    )

    text = text.replace(
        ">",
        "&gt;"
    )

    return text


def markdown_to_reportlab(text):
    """
    Convert basic Markdown formatting into ReportLab markup.
    """

    text = escape_xml(text)

    # Markdown links
    text = re.sub(
        r"\[([^\]]+)\]\(([^)]+)\)",
        r'<link href="\2" color="#1769AA">\1</link>',
        text,
    )

    # Bold
    text = re.sub(
        r"\*\*(.+?)\*\*",
        r"<b>\1</b>",
        text,
    )

    # Italic
    text = re.sub(
        r"(?<!\*)\*([^*]+)\*(?!\*)",
        r"<i>\1</i>",
        text,
    )

    return text


def clean_markdown_line(line):
    """
    Remove unnecessary Markdown-only syntax.
    """

    line = line.strip()

    if re.fullmatch(
        r"[-*_]{3,}",
        line,
    ):
        return ""

    return line


# ============================================================
# TABLE HELPERS
# ============================================================

def is_table_separator(line):
    """
    Check whether a Markdown row is a table separator.
    """

    cells = [
        cell.strip()
        for cell in line.strip().strip("|").split("|")
    ]

    if not cells:
        return False

    return all(
        re.fullmatch(
            r":?-+:?",
            cell
        )
        for cell in cells
    )


def parse_table(lines, start_index):
    """
    Parse a Markdown table starting at start_index.
    """

    if start_index >= len(lines):
        return None, start_index

    header = lines[start_index]

    if "|" not in header:
        return None, start_index

    if start_index + 1 >= len(lines):
        return None, start_index

    separator = lines[start_index + 1]

    if not is_table_separator(separator):
        return None, start_index

    def split_row(row):

        return [
            cell.strip()
            for cell in row.strip().strip("|").split("|")
        ]

    rows = []

    rows.append(
        split_row(header)
    )

    index = start_index + 2

    while index < len(lines):

        line = lines[index].strip()

        if not line or "|" not in line:
            break

        rows.append(
            split_row(line)
        )

        index += 1

    return rows, index


# ============================================================
# TABLE RENDERING
# ============================================================

def make_table(data):
    """
    Convert Markdown table data into a clean A4 table.
    """

    if not data:
        return None

    column_count = max(
        len(row)
        for row in data
    )

    normalized = []

    for row in data:

        row = list(row)

        while len(row) < column_count:
            row.append("")

        normalized.append(
            row[:column_count]
        )

    formatted = []

    for row_index, row in enumerate(normalized):

        formatted_row = []

        for cell in row:

            cell = markdown_to_reportlab(
                cell
            )

            if row_index == 0:

                style = TABLE_HEADER_STYLE

            else:

                style = TABLE_BODY_STYLE

            formatted_row.append(
                Paragraph(
                    cell,
                    style,
                )
            )

        formatted.append(
            formatted_row
        )

    available_width = (
        PAGE_WIDTH
        - LEFT_MARGIN
        - RIGHT_MARGIN
    )

    col_width = (
        available_width
        / column_count
    )

    table = Table(
        formatted,
        colWidths=[
            col_width
        ] * column_count,
        repeatRows=1,
        hAlign="LEFT",
    )

    table.setStyle(
        TableStyle(
            [

                # Header
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    NAVY,
                ),

                (
                    "TEXTCOLOR",
                    (0, 0),
                    (-1, 0),
                    WHITE,
                ),

                # Alternating rows
                (
                    "ROWBACKGROUNDS",
                    (0, 1),
                    (-1, -1),
                    [
                        WHITE,
                        LIGHT_GREY,
                    ],
                ),

                # Borders
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.35,
                    MID_GREY,
                ),

                # Alignment
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP",
                ),

                # More breathing room
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    7,
                ),

                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    7,
                ),

                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    7,
                ),

                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    7,
                ),
            ]
        )
    )

    return table


# ============================================================
# CALLOUT BOX
# ============================================================

def make_callout(text):
    """
    Create a simple highlighted information box.
    """

    paragraph = Paragraph(
        markdown_to_reportlab(text),
        CALLOUT_STYLE,
    )

    table = Table(
        [[paragraph]],
        colWidths=[
            PAGE_WIDTH
            - LEFT_MARGIN
            - RIGHT_MARGIN
        ],
    )

    table.setStyle(
        TableStyle(
            [

                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, -1),
                    LIGHT_BLUE,
                ),

                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.7,
                    BLUE,
                ),

                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    10,
                ),

                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    10,
                ),

                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    9,
                ),

                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    9,
                ),
            ]
        )
    )

    return table


# ============================================================
# HEADER AND FOOTER
# ============================================================

def draw_header_footer(canvas, doc):
    """
    Draw a simple professional header and footer.
    """

    canvas.saveState()

    page_number = canvas.getPageNumber()

    # --------------------------------------------------------
    # Header line
    # --------------------------------------------------------

    canvas.setStrokeColor(
        MID_GREY
    )

    canvas.setLineWidth(
        0.5
    )

    canvas.line(
        LEFT_MARGIN,
        PAGE_HEIGHT - 13 * mm,
        PAGE_WIDTH - RIGHT_MARGIN,
        PAGE_HEIGHT - 13 * mm,
    )

    # --------------------------------------------------------
    # Header left
    # --------------------------------------------------------

    canvas.setFont(
        BOLD_FONT,
        7.5,
    )

    canvas.setFillColor(
        NAVY
    )

    canvas.drawString(
        LEFT_MARGIN,
        PAGE_HEIGHT - 10 * mm,
        "GLOBAL FINANCIAL MARKET INTELLIGENCE",
    )

    # --------------------------------------------------------
    # Header right
    # --------------------------------------------------------

    canvas.setFont(
        BODY_FONT,
        7,
    )

    canvas.setFillColor(
        MUTED_TEXT
    )

    canvas.drawRightString(
        PAGE_WIDTH - RIGHT_MARGIN,
        PAGE_HEIGHT - 10 * mm,
        "Morning Market Report",
    )

    # --------------------------------------------------------
    # Footer line
    # --------------------------------------------------------

    canvas.setStrokeColor(
        MID_GREY
    )

    canvas.line(
        LEFT_MARGIN,
        11 * mm,
        PAGE_WIDTH - RIGHT_MARGIN,
        11 * mm,
    )

    # --------------------------------------------------------
    # Footer left
    # --------------------------------------------------------

    canvas.setFont(
        BODY_FONT,
        7,
    )

    canvas.setFillColor(
        MUTED_TEXT
    )

    canvas.drawString(
        LEFT_MARGIN,
        7 * mm,
        "Financial Market Intelligence",
    )

    # --------------------------------------------------------
    # Footer right
    # --------------------------------------------------------

    canvas.drawRightString(
        PAGE_WIDTH - RIGHT_MARGIN,
        7 * mm,
        f"Page {page_number}",
    )

    canvas.restoreState()


# ============================================================
# COVER PAGE
# ============================================================

def make_cover_page(title, subtitle):
    """
    Create a clean professional A4 cover page.
    """

    elements = []

    # Large top whitespace

    elements.append(
        Spacer(
            1,
            48 * mm,
        )
    )

    # Small title

    elements.append(
        Paragraph(
            "GLOBAL FINANCIAL",
            COVER_SMALL_STYLE,
        )
    )

    elements.append(
        Spacer(
            1,
            5 * mm,
        )
    )

    # Main title

    elements.append(
        Paragraph(
            "MARKET INTELLIGENCE",
            COVER_TITLE_STYLE,
        )
    )

    elements.append(
        Spacer(
            1,
            5 * mm,
        )
    )

    # Report type

    elements.append(
        Paragraph(
            "MORNING MARKET REPORT",
            COVER_REPORT_STYLE,
        )
    )

    elements.append(
        Spacer(
            1,
            18 * mm,
        )
    )

    # Divider

    elements.append(
        HRFlowable(
            width="100%",
            thickness=1.2,
            color=BLUE,
            spaceAfter=8 * mm,
        )
    )

    # Actual report title

    elements.append(
        Paragraph(
            markdown_to_reportlab(
                title
            ),
            COVER_ACTUAL_TITLE_STYLE,
        )
    )

    elements.append(
        Spacer(
            1,
            3 * mm,
        )
    )

    # Actual subtitle

    elements.append(
        Paragraph(
            markdown_to_reportlab(
                subtitle
            ),
            COVER_ACTUAL_SUBTITLE_STYLE,
        )
    )

    # Bottom whitespace

    elements.append(
        Spacer(
            1,
            75 * mm,
        )
    )

    # Bottom divider

    elements.append(
        HRFlowable(
            width="100%",
            thickness=0.5,
            color=MID_GREY,
            spaceAfter=5 * mm,
        )
    )

    # Coverage

    elements.append(
        Paragraph(
            "GLOBAL MARKETS  •  INDIA  •  MACRO  •  COMMODITIES  •  TECHNOLOGY",
            COVER_COVERAGE_STYLE,
        )
    )

    elements.append(
        Spacer(
            1,
            3 * mm,
        )
    )

    elements.append(
        Paragraph(
            "Prepared for the next trading session",
            SMALL_STYLE,
        )
    )

    # New page

    elements.append(
        PageBreak()
    )

    return elements


# ============================================================
# MARKDOWN → PDF ELEMENTS
# ============================================================

def markdown_to_flowables(markdown_text):
    """
    Convert the Markdown report into ReportLab elements.
    """

    lines = markdown_text.splitlines()

    elements = []

    index = 0

    first_heading_seen = False

    while index < len(lines):

        line = lines[index].strip()

        # ----------------------------------------------------
        # Empty line
        # ----------------------------------------------------

        if not line:

            elements.append(
                Spacer(
                    1,
                    2.5 * mm,
                )
            )

            index += 1
            continue

        # ----------------------------------------------------
        # Table
        # ----------------------------------------------------

        table_data, next_index = parse_table(
            lines,
            index,
        )

        if table_data is not None:

            table = make_table(
                table_data
            )

            if table:

                elements.append(
                    Spacer(
                        1,
                        3 * mm,
                    )
                )

                elements.append(
                    table
                )

                elements.append(
                    Spacer(
                        1,
                        6 * mm,
                    )
                )

            index = next_index

            continue

        # ----------------------------------------------------
        # H1
        # ----------------------------------------------------

        if line.startswith("# ") and not line.startswith("## "):

            title = line[2:].strip()

            # First H1 is already displayed on cover

            if not first_heading_seen:

                first_heading_seen = True

                index += 1

                continue

            elements.append(
                Paragraph(
                    markdown_to_reportlab(
                        title
                    ),
                    H1_STYLE,
                )
            )

            elements.append(
                HRFlowable(
                    width="100%",
                    thickness=0.5,
                    color=MID_GREY,
                    spaceAfter=7,
                )
            )

            index += 1

            continue

        # ----------------------------------------------------
        # H2
        # ----------------------------------------------------

        if line.startswith("## "):

            title = line[3:].strip()

            elements.append(
                Paragraph(
                    markdown_to_reportlab(
                        title
                    ),
                    H1_STYLE,
                )
            )

            index += 1

            continue

        # ----------------------------------------------------
        # H3
        # ----------------------------------------------------

        if line.startswith("### "):

            title = line[4:].strip()

            elements.append(
                Paragraph(
                    markdown_to_reportlab(
                        title
                    ),
                    H2_STYLE,
                )
            )

            index += 1

            continue

        # ----------------------------------------------------
        # H4
        # ----------------------------------------------------

        if line.startswith("#### "):

            title = line[5:].strip()

            elements.append(
                Paragraph(
                    markdown_to_reportlab(
                        title
                    ),
                    H3_STYLE,
                )
            )

            index += 1

            continue

        # ----------------------------------------------------
        # Blockquote
        # ----------------------------------------------------

        if line.startswith(">"):

            quote = line.lstrip(
                "> "
            ).strip()

            elements.append(
                make_callout(
                    quote
                )
            )

            elements.append(
                Spacer(
                    1,
                    4 * mm,
                )
            )

            index += 1

            continue

        # ----------------------------------------------------
        # Bullet list
        # ----------------------------------------------------

        if re.match(
            r"^[-*]\s+",
            line,
        ):

            content = re.sub(
                r"^[-*]\s+",
                "",
                line,
            )

            elements.append(
                Paragraph(
                    "• "
                    + markdown_to_reportlab(
                        content
                    ),
                    BULLET_STYLE,
                )
            )

            index += 1

            continue

        # ----------------------------------------------------
        # Numbered list
        # ----------------------------------------------------

        numbered_match = re.match(
            r"^(\d+)\.\s+(.*)",
            line,
        )

        if numbered_match:

            number = numbered_match.group(1)

            content = numbered_match.group(2)

            elements.append(
                Paragraph(
                    f"<b>{number}.</b> "
                    + markdown_to_reportlab(
                        content
                    ),
                    BULLET_STYLE,
                )
            )

            index += 1

            continue

        # ----------------------------------------------------
        # Horizontal rule
        # ----------------------------------------------------

        if re.fullmatch(
            r"[-*_]{3,}",
            line,
        ):

            elements.append(
                HRFlowable(
                    width="100%",
                    thickness=0.5,
                    color=MID_GREY,
                    spaceBefore=4,
                    spaceAfter=7,
                )
            )

            index += 1

            continue

        # ----------------------------------------------------
        # Normal paragraph
        # ----------------------------------------------------

        paragraph = markdown_to_reportlab(
            clean_markdown_line(
                line
            )
        )

        if paragraph:

            elements.append(
                Paragraph(
                    paragraph,
                    BODY_STYLE,
                )
            )

        index += 1

    return elements


# ============================================================
# TITLE EXTRACTION
# ============================================================

def extract_title(markdown_text):
    """
    Extract the first Markdown H1.
    """

    for line in markdown_text.splitlines():

        if line.startswith("# "):

            return line[2:].strip()

    return (
        "Global Financial Market Intelligence Report"
    )


def extract_subtitle(markdown_text):
    """
    Extract the first bold line after the title.
    """

    lines = markdown_text.splitlines()

    title_found = False

    for line in lines:

        line = line.strip()

        if line.startswith("# "):

            title_found = True

            continue

        if (
            title_found
            and line.startswith("**")
        ):

            return line.strip(
                "* "
            )

    return (
        "Morning Report for the Next Trading Session"
    )


# ============================================================
# PDF GENERATION
# ============================================================

def generate_pdf(
    markdown_file,
    output_file=None,
):
    """
    Generate an A4 PDF from a Markdown report.
    """

    markdown_file = Path(
        markdown_file
    )

    if not markdown_file.exists():

        raise FileNotFoundError(
            f"Markdown report not found: {markdown_file}"
        )

    # --------------------------------------------------------
    # Read Markdown
    # --------------------------------------------------------

    with open(
        markdown_file,
        "r",
        encoding="utf-8",
    ) as file:

        markdown_text = file.read()

    # --------------------------------------------------------
    # Default output path
    # --------------------------------------------------------

    if output_file is None:

        output_file = (
            REPORTS_DIR
            / f"{markdown_file.stem}.pdf"
        )

    output_file = Path(
        output_file
    )

    output_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    # --------------------------------------------------------
    # Extract title
    # --------------------------------------------------------

    title = extract_title(
        markdown_text
    )

    subtitle = extract_subtitle(
        markdown_text
    )

    # --------------------------------------------------------
    # Main frame
    # --------------------------------------------------------

    frame = Frame(
        LEFT_MARGIN,
        BOTTOM_MARGIN,
        PAGE_WIDTH
        - LEFT_MARGIN
        - RIGHT_MARGIN,
        PAGE_HEIGHT
        - TOP_MARGIN
        - BOTTOM_MARGIN,
        id="normal",
    )

    # --------------------------------------------------------
    # A4 document
    # --------------------------------------------------------

    document = BaseDocTemplate(
        str(output_file),
        pagesize=A4,
        leftMargin=LEFT_MARGIN,
        rightMargin=RIGHT_MARGIN,
        topMargin=TOP_MARGIN,
        bottomMargin=BOTTOM_MARGIN,
        title=title,
        author="Financial Market Intelligence Agent",
    )

    # --------------------------------------------------------
    # Page template
    # --------------------------------------------------------

    document.addPageTemplates(
        [
            PageTemplate(
                id="main",
                frames=frame,
                onPage=draw_header_footer,
            )
        ]
    )

    # --------------------------------------------------------
    # Build report
    # --------------------------------------------------------

    elements = []

    # Cover page

    elements.extend(
        make_cover_page(
            title,
            subtitle,
        )
    )

    # Main report

    elements.extend(
        markdown_to_flowables(
            markdown_text
        )
    )

    # Generate PDF

    document.build(
        elements
    )

    return output_file


# ============================================================
# MAIN
# ============================================================

def main():
    """
    Automatically convert the latest morning Markdown
    report in /reports into PDF.
    """

    # Find all morning reports

    markdown_files = sorted(
        REPORTS_DIR.glob(
            "morning_report_*.md"
        ),
        key=lambda file: file.stat().st_mtime,
        reverse=True,
    )

    # No reports found

    if not markdown_files:

        print(
            "No morning_report_*.md file found in reports/"
        )

        return

    # Select latest report

    markdown_file = markdown_files[0]

    print(
        f"Using latest report:\n"
        f"{markdown_file.name}"
    )

    # Generate PDF

    output_file = generate_pdf(
        markdown_file
    )

    print(
        f"\nPDF generated successfully:\n"
        f"{output_file}"
    )


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    main()
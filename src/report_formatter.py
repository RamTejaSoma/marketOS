import os
from pathlib import Path
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI


load_dotenv()

GEMINI_MODEL = os.getenv("GEMINI_MODEL_NEWS")

if not GEMINI_MODEL:
    raise ValueError("GEMINI_MODEL not found in .env")


# ---------------------------------------------------------
# LLM
# ---------------------------------------------------------

formatter_llm = ChatGoogleGenerativeAI(
    model=GEMINI_MODEL
)


# ---------------------------------------------------------
# Formatting Prompt
# ---------------------------------------------------------
FORMATTER_SYSTEM_PROMPT = """
You are a professional financial report formatter.

Your task is ONLY to format the supplied financial market
intelligence report for professional PDF generation.

IMPORTANT:
The input report is already complete.

DO NOT summarize it.
DO NOT shorten it.
DO NOT remove information.
DO NOT omit any analysis, explanation, numbers, events, or sources.
DO NOT add new information.
DO NOT change facts or numerical values.

Preserve ALL information from the input.

Your job is only to improve its presentation and organization.

You may:

1. Organize content into clear sections and subsections.
2. Improve Markdown heading hierarchy.
3. Convert information that is naturally tabular into Markdown tables.
4. Use bullet points where they improve readability.
5. Separate important conclusions or takeaways visually.
6. Improve spacing and readability.
7. Remove only accidental formatting problems or exact duplicate text.
8. Keep source URLs and source information intact.

Tables should be used for information such as:
- market indices
- sectors
- stocks
- futures
- ETFs
- forex
- commodities
- macro indicators
- comparable market statistics

Do NOT force narrative analysis into tables.

The final document should look like a professional institutional
financial market intelligence report.

The original report may contain sections with different names.
Preserve the existing information and organize it naturally.
Do not force content into sections where it does not belong.

CRITICAL RULE:

Every meaningful piece of information in the input must appear
in the output.

Think of your task as:

"FORMAT THE DOCUMENT, DO NOT EDIT THE CONTENT."

Return ONLY the formatted Markdown document.
"""

# ---------------------------------------------------------
# Prompt
# ---------------------------------------------------------

formatter_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", FORMATTER_SYSTEM_PROMPT),
        (
            "human",
            """
Format the following report without removing any information:

{raw_report}
"""
        ),
    ]
)


# ---------------------------------------------------------
# Formatter Chain
# ---------------------------------------------------------

formatter_chain = formatter_prompt | formatter_llm


# ---------------------------------------------------------
# Public Function
# ---------------------------------------------------------

def format_report(raw_report: str) -> str:
    """
    Convert the raw agent-generated report into
    professionally structured Markdown.
    """

    response = formatter_chain.invoke(
        {
            "raw_report": raw_report
        }
    )

    content = response.content

    if isinstance(content, list):
        return "\n".join(
            block["text"]
            for block in content
            if block.get("type") == "text"
        )

    return content


if __name__ == "__main__":

    test_file = (
        Path(__file__).resolve().parent.parent
        / "reports"
        / "morning_report_2026-09-11.md"
    )

    with open(test_file, "r", encoding="utf-8") as f:
        raw_report = f.read()

    formatted_report = format_report(raw_report)

    output_file = (
        Path(__file__).resolve().parent.parent
        / "reports"
        / "formatted_report_2026-09-11.md"
    )

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(formatted_report)

    print(f"Formatted report saved to: {output_file}")
from pathlib import Path
from datetime import datetime
import importlib


PROJECT_ROOT = Path(__file__).resolve().parent
REPORTS_DIR = PROJECT_ROOT / "reports"


def main():
    print("\n" + "=" * 70)
    print("MORNING MARKET REPORT PIPELINE")
    print("=" * 70)

    # ---------------------------------------------------------
    # 1. Collect fresh market data
    # ---------------------------------------------------------
    print("\n[1/4] Running market data pipeline...")
    from src.market_data import run_market_pipeline

    run_market_pipeline()
    print("✓ Market data pipeline completed.")

    # ---------------------------------------------------------
    # 2. Collect and process fresh news
    # ---------------------------------------------------------
    print("\n[2/4] Running news pipeline...")
    from src.news_pipeline import run_news_pipeline

    run_news_pipeline()
    print("✓ News pipeline completed.")

    # ---------------------------------------------------------
    # 3. Generate the Markdown report with the agent
    #
    # IMPORTANT:
    # agent.py loads market_data.json and news_data.json
    # during import, so it is imported only AFTER the two
    # pipelines above have completed.
    # ---------------------------------------------------------
    print("\n[3/4] Generating morning report...")

    agent_module = importlib.import_module("src.agent")
    agent_module.main()

    report_date = datetime.now().strftime("%Y-%m-%d")
    markdown_file = REPORTS_DIR / f"morning_report_{report_date}.md"

    if not markdown_file.exists():
        raise FileNotFoundError(
            f"Agent completed, but Markdown report was not found:\n"
            f"{markdown_file}"
        )

    print(f"✓ Markdown report created: {markdown_file}")

    # ---------------------------------------------------------
    # 4. Convert Markdown report to PDF
    # ---------------------------------------------------------
    print("\n[4/4] Generating PDF...")

    generator_module = importlib.import_module("src.report_generator")
    generator_module.generate_pdf(markdown_file)

    pdf_file = markdown_file.with_suffix(".pdf")

    if not pdf_file.exists():
        print("⚠ PDF generator completed, but the expected PDF path was not found.")
        print("  Check the output path used by report_generator.py.")
    else:
        print(f"✓ PDF report created: {pdf_file}")

    print("\n" + "=" * 70)
    print("PIPELINE COMPLETED SUCCESSFULLY")
    print("=" * 70)
    print(f"Markdown: {markdown_file}")
    if pdf_file.exists():
        print(f"PDF:      {pdf_file}")
    print("=" * 70)


if __name__ == "__main__":
    main()

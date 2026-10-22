import json
import os
import re
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from urllib.parse import urlparse, urlunparse

import pandas as pd
import requests
import trafilatura
import yfinance as yf
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from typing import Literal

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate


# ============================================================
# CONFIGURATION
# ============================================================

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_FILE = DATA_DIR / "news_data.json"

COUNT_PER_QUERY = 10
QUERY_DELAY_SECONDS = 1
RECENT_NEWS_HOURS = 24
MAX_ARTICLES_PER_CATEGORY = 5


# ============================================================
# NEWS QUERIES
# ============================================================

NEWS_QUERIES = {

    "financial": [
        "stock market",
        "financial markets",
        "Wall Street",
        "stocks"
    ],

    "geopolitical": [
        "geopolitics",
        "US China",
        "Middle East",
        "tariffs"
    ],

    "monetary": [
        "Federal Reserve",
        "interest rates",
        "central banks",
        "monetary policy"
    ],

    "technology": [
        "technology",
        "artificial intelligence",
        "semiconductors",
        "AI chips"
    ],

    "economic": [
        "US economy",
        "inflation",
        "economic data",
        "economic releases"
    ],

    "commodities": [
        "oil prices",
        "gold prices",
        "crude oil",
        "commodity markets"
    ]
}


# ============================================================
# 1. NORMALIZE SEARCH ARTICLE
# ============================================================

def normalize_search_news(article, query, category):

    timestamp = article.get("providerPublishTime")

    published_at = None

    if timestamp:
        published_at = datetime.fromtimestamp(
            timestamp,
            tz=timezone.utc
        ).isoformat()

    return {
        "id": article.get("uuid"),
        "source": "yfinance",
        "source_type": "search",

        "query": query,
        "category": category,

        "title": article.get("title"),
        "publisher": article.get("publisher"),

        "url": article.get("link"),
        "published_at": published_at,

        "content_type": article.get("type"),

        "related_tickers": article.get(
            "relatedTickers",
            []
        )
    }


# ============================================================
# 2. COLLECT NEWS FOR ONE QUERY
# ============================================================

def collect_search_news(
    query,
    category,
    count=10
):

    try:

        search = yf.Search(
            query,
            news_count=count
        )

        articles = []

        for article in search.news:

            normalized = normalize_search_news(
                article=article,
                query=query,
                category=category
            )

            articles.append(normalized)

        return articles

    except Exception as e:

        print(
            f"Error for query '{query}': {e}"
        )

        return []


# ============================================================
# 3. COLLECT ALL NEWS
# ============================================================

def collect_all_news(
    queries,
    count_per_query=5,
    delay=1
):

    all_articles = []

    for category, category_queries in queries.items():

        print("\n" + "=" * 80)
        print(
            f"CATEGORY: {category.upper()}"
        )
        print("=" * 80)

        for query in category_queries:

            print(
                f"\nSearching: {query}"
            )

            articles = collect_search_news(
                query=query,
                category=category,
                count=count_per_query
            )

            print(
                f"Found: {len(articles)}"
            )

            all_articles.extend(articles)

            time.sleep(delay)

    return all_articles


# ============================================================
# 4. NORMALIZE URL
# ============================================================

def normalize_url(url):

    if not url:
        return None

    parsed = urlparse(url)

    clean = parsed._replace(
        query="",
        fragment=""
    )

    return urlunparse(clean)


# ============================================================
# 5. PREPARE LLM INPUT
# ============================================================

def prepare_llm_input(category_df):

    records = []

    for _, row in category_df.iterrows():

        records.append({
            "article_id": row["id"],
            "query": row["query"],
            "title": row["title"]
        })

    return records


# ============================================================
# 6. LLM STRUCTURED OUTPUT
# ============================================================

class ArticleDecision(BaseModel):

    article_id: str = Field(
        description="Original article ID. Must remain exactly unchanged."
    )

    keep: bool = Field(
        description="Whether the article should proceed to article text extraction."
    )

    importance: Literal["high", "medium", "low"] = Field(
        description="Importance of the article for the daily global financial market report."
    )

    score: int = Field(
        description="Market relevance score from 0 to 100."
    )

    reason: str = Field(
        description="Short explanation for the decision."
    )


class ArticleFilterResult(BaseModel):

    decisions: list[ArticleDecision]


# ============================================================
# 7. CREATE NEWS FILTER LLM
# ============================================================

SYSTEM_PROMPT = """
You are a market intelligence news filtering system.

Your task is to evaluate news article titles and determine which articles
are important enough to proceed to article text extraction for a daily
global financial market report.

Evaluate each article using:
- article title
- search query
- category

KEEP an article when it has meaningful potential relevance to:
- Global financial markets
- Equity markets
- Bond and interest-rate markets
- Currencies and FX
- Commodities
- Central banks and monetary policy
- Inflation, employment, GDP and other major economic indicators
- Major geopolitical developments with financial or economic implications
- Trade restrictions, tariffs and international economic policy
- Major technology developments with meaningful market implications
- Major company developments that could materially affect markets or
  important sectors

REJECT articles that are primarily:
- Promotional or advertising content
- Entertainment or lifestyle content
- Minor/local business announcements
- Generic opinion with little actionable information
- Historical/background content with little current relevance
- Very narrow company or industry news with insignificant broader
  market impact
- Clearly unrelated to the category or financial markets

Important rules:
- Do not select an article merely because it contains financial keywords.
- Focus on potential impact on investors, markets, economic conditions,
  monetary policy, geopolitical risk, or major sectors.
- Prefer avoiding false negatives. If an article could reasonably contain
  important market information, lean toward KEEP.
- Do not assume facts that are not present in the title.
- Evaluate every article independently.
- Return a decision for EVERY article.
- Do not omit any article.

For each article:
- keep: true or false
- importance: high, medium, or low
- score: 0 to 100
- reason: concise explanation

The article_id must be returned exactly as provided.
"""


def create_filter_chain():

    model_name = os.getenv("GEMINI_MODEL_NEWS")

    if not model_name:
        raise ValueError(
            "GEMINI_MODEL not found in .env. "
            "Set it to the Gemini model that is currently working for your project."
        )

    llm = ChatGoogleGenerativeAI(
        model=model_name,
        temperature=0
    )

    structured_llm = llm.with_structured_output(
        ArticleFilterResult
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),

        ("human", """
Evaluate the following {category} news articles.

Articles:

{articles}
""")
    ])

    return prompt | structured_llm


# ============================================================
# 8. FILTER ONE CATEGORY
# ============================================================

def filter_category(
    category,
    category_articles,
    chain
):

    articles_json = json.dumps(
        category_articles,
        ensure_ascii=False,
        indent=2
    )

    result = chain.invoke({
        "category": category,
        "articles": articles_json
    })

    decision_df = pd.DataFrame([
        decision.model_dump()
        for decision in result.decisions
    ])

    decision_df["category"] = category

    return decision_df


# ============================================================
# 9. FILTER ALL CATEGORIES
# ============================================================

def filter_all_categories(df, chain):

    category_inputs = {}

    for category, group in df.groupby("category"):

        category_inputs[category] = prepare_llm_input(
            group
        )

    all_decisions = {}

    for category, articles in category_inputs.items():

        print(
            f"Processing: {category} "
            f"({len(articles)} articles)"
        )

        decisions = filter_category(
            category,
            articles,
            chain
        )

        all_decisions[category] = decisions

        print(
            f"Received: {len(decisions)} decisions"
        )

        print("-" * 50)

    all_decisions_df = pd.concat(
        all_decisions.values(),
        ignore_index=True
    )

    selected_decisions = (
        all_decisions_df[
            all_decisions_df["keep"] == True
        ]
        .sort_values(
            ["category", "score"],
            ascending=[True, False]
        )
        .groupby("category")
        .head(MAX_ARTICLES_PER_CATEGORY)
        .reset_index(drop=True)
    )

    selected_ids = selected_decisions[
        "article_id"
    ].tolist()

    return df[
        df["id"].isin(selected_ids)
    ].copy()


# ============================================================
# 10. FILTER RECENT NEWS
# ============================================================

def filter_recent_news(
    df,
    hours=24
):

    df = df.copy()

    df["published_dt"] = pd.to_datetime(
        df["published_at"],
        utc=True,
        errors="coerce"
    )

    now = datetime.now(timezone.utc)

    cutoff = now - timedelta(
        hours=hours
    )

    df = df[
        df["published_dt"] >= cutoff
    ].copy()

    df = df.sort_values(
        "published_dt",
        ascending=False
    )

    df = df.reset_index(
        drop=True
    )

    return df


# ============================================================
# 11. ARTICLE EXTRACTION CONFIGURATION
# ============================================================

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/140.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


# ============================================================
# 12. ARTICLE TEXT EXTRACTION
# ============================================================

def extract_article_text(url):

    if not url:

        return {
            "text": None,
            "status": "failed",
            "method": None
        }

    try:

        response = requests.get(
            url,
            headers=HEADERS,
            timeout=20
        )

        if response.status_code != 200:

            return {
                "text": None,
                "status": "failed",
                "method": None
            }

        html = response.text

        soup = BeautifulSoup(
            html,
            "html.parser"
        )

        # ----------------------------------------------------
        # PRIMARY — Trafilatura
        # ----------------------------------------------------

        text = trafilatura.extract(
            html,
            include_comments=False,
            include_tables=False,
            favor_precision=True
        )

        if text:

            text = re.sub(
                r"\s+",
                " ",
                text
            ).strip()

            if len(text) >= 800:

                return {
                    "text": text,
                    "status": "full",
                    "method": "trafilatura"
                }

        # ----------------------------------------------------
        # FALLBACK — Yahoo body-wrap
        # ----------------------------------------------------

        article_div = soup.find(
            "div",
            class_=lambda x: x and "body-wrap" in x
        )

        if article_div:

            paragraphs = article_div.find_all("p")

            body_text = "\n".join(
                p.get_text(" ", strip=True)
                for p in paragraphs
                if p.get_text(strip=True)
            ).strip()

            body_text = re.sub(
                r"\n{3,}",
                "\n\n",
                body_text
            )

            if len(body_text) >= 800:

                return {
                    "text": body_text,
                    "status": "full",
                    "method": "body-wrap"
                }

            elif len(body_text) >= 150:

                return {
                    "text": body_text,
                    "status": "partial",
                    "method": "body-wrap"
                }

        # ----------------------------------------------------
        # Trafilatura produced short text
        # ----------------------------------------------------

        if text:

            return {
                "text": text,
                "status": "partial",
                "method": "trafilatura"
            }

        # ----------------------------------------------------
        # Meta description fallback
        # ----------------------------------------------------

        meta = soup.find(
            "meta",
            attrs={"name": "description"}
        )

        if meta:

            description = meta.get(
                "content"
            )

            if description:

                description = description.strip()

                if len(description) >= 50:

                    return {
                        "text": description,
                        "status": "partial",
                        "method": "meta_description"
                    }

        return {
            "text": None,
            "status": "failed",
            "method": None
        }

    except Exception:

        return {
            "text": None,
            "status": "failed",
            "method": None
        }


# ============================================================
# 13. EXTRACT ALL ARTICLE TEXT
# ============================================================

def extract_all_article_text(df):

    article_texts = []
    extraction_statuses = []
    extraction_methods = []

    for i, url in enumerate(df["url"]):

        print(
            f"[{i + 1}/{len(df)}] "
            f"Extracting: "
            f"{df.iloc[i]['title'][:70]}..."
        )

        result = extract_article_text(
            url
        )

        article_texts.append(
            result["text"]
        )

        extraction_statuses.append(
            result["status"]
        )

        extraction_methods.append(
            result["method"]
        )

    df = df.copy()

    df["article_text"] = article_texts
    df["extraction_status"] = extraction_statuses
    df["extraction_method"] = extraction_methods

    return df


# ============================================================
# 14. REMOVE FAILED EXTRACTIONS
# ============================================================

def keep_successful_extractions(df):

    news_df = df[
        df["extraction_status"].isin(
            ["full", "partial"]
        )
    ].copy()

    return news_df.reset_index(
        drop=True
    )


# ============================================================
# 15. SAVE NEWS DATA
# ============================================================

def save_news_data(
    news_df,
    output_file=OUTPUT_FILE
):

    output_file.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    news_data = news_df.to_dict(
        orient="records"
    )

    with open(
        output_file,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            news_data,
            f,
            indent=2,
            ensure_ascii=False,
            default=str
        )

    print(
        f"Saved {len(news_data)} articles"
    )

    print(
        f"Output: {output_file}"
    )


# ============================================================
# 16. COMPLETE NEWS PIPELINE
# ============================================================

def run_news_pipeline():

    # --------------------------------------------------------
    # Collect
    # --------------------------------------------------------

    raw_news = collect_all_news(
        NEWS_QUERIES,
        count_per_query=COUNT_PER_QUERY,
        delay=QUERY_DELAY_SECONDS
    )

    print(
        "\nTotal raw articles:",
        len(raw_news)
    )

    if not raw_news:

        print("No news articles collected.")

        save_news_data(
            pd.DataFrame()
        )

        return pd.DataFrame()

    df = pd.DataFrame(
        raw_news
    )

    # --------------------------------------------------------
    # Normalize URLs
    # --------------------------------------------------------

    df["normalized_url"] = df[
        "url"
    ].apply(normalize_url)

    print(
        "Articles before deduplication:",
        len(df)
    )

    # --------------------------------------------------------
    # Deduplicate
    # --------------------------------------------------------

    df = df.drop_duplicates(
        subset=["normalized_url"],
        keep="first"
    ).reset_index(
        drop=True
    )

    print(
        "Articles after deduplication:",
        len(df)
    )

    print(
        "Duplicates removed:",
        len(raw_news) - len(df)
    )

    # --------------------------------------------------------
    # LLM filtering
    # --------------------------------------------------------

    chain = create_filter_chain()

    df = filter_all_categories(
        df,
        chain
    )

    print(
        "\nArticles after LLM filtering:",
        len(df)
    )

    # --------------------------------------------------------
    # Recent-news filtering
    # --------------------------------------------------------

    print(
        "Before recent-news filtering:",
        len(df)
    )

    df = filter_recent_news(
        df,
        hours=RECENT_NEWS_HOURS
    )

    print(
        "After recent-news filtering:",
        len(df)
    )

    # --------------------------------------------------------
    # Article text extraction
    # --------------------------------------------------------

    df = extract_all_article_text(
        df
    )

    print(
        "\nExtraction Status:"
    )

    print(
        df["extraction_status"].value_counts()
    )

    print(
        "\nExtraction Method:"
    )

    print(
        df["extraction_method"].value_counts()
    )

    # --------------------------------------------------------
    # Remove failed extractions
    # --------------------------------------------------------

    news_df = keep_successful_extractions(
        df
    )

    print(
        "\nArticles entering next stage:",
        len(news_df)
    )

    print(
        "\nCategories:"
    )

    print(
        news_df["category"].value_counts()
    )

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    save_news_data(
        news_df
    )

    return news_df


# ============================================================
# SCRIPT ENTRY POINT
# ============================================================

if __name__ == "__main__":

    run_news_pipeline()

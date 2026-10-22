# MarketOS — Financial Market Intelligence Agent

MarketOS is an AI-powered financial market intelligence system designed to collect global market data, aggregate financial and geopolitical news, and generate a structured morning market report.

The project combines Python-based data pipelines with a LangChain-powered AI agent and a React dashboard to make market analysis easier to explore.

## Overview

MarketOS collects information from multiple financial data sources, processes relevant news articles, and uses an LLM-powered agent to generate a consolidated market intelligence report.

The long-term goal is to build an interactive financial research assistant that can analyze market conditions, explain significant movements, and answer follow-up questions using collected market information.

## Features

- **Global Market Monitoring** — Track major global indices, sector performance, US futures, stocks, ETFs, forex, commodities, and macroeconomic indicators.
- **Financial News Aggregation** — Collect financial, geopolitical, monetary, technology, economic, and commodity-related news.
- **Article Extraction** — Extract readable article content from news URLs for downstream analysis.
- **AI-Powered Market Analysis** — Use a LangChain agent and an LLM to analyze collected market data and news.
- **Morning Market Reports** — Generate structured reports summarizing important market developments.
- **PDF Report Generation** — Convert generated Markdown reports into PDF documents.
- **React Dashboard** — Browse generated reports and access the report-generation workflow through a web interface.
- **Report Archive** — Access previously generated reports from the dashboard.

## Technology Stack

| Component | Technologies |
|---|---|
| Frontend | React.js, Vite, CSS |
| Backend | Node.js, Express.js |
| AI Agent | Python, LangChain |
| LLM Integration | Google Gemini API |
| Market Data | yfinance and configured financial data APIs |
| News Processing | Python, Requests, BeautifulSoup, Trafilatura |
| Report Generation | Markdown, ReportLab |
| Version Control | Git, GitHub |

## Architecture

```text
                    ┌─────────────────────────┐
                    │     React Dashboard     │
                    │  Reports / PDF / Archive│
                    └────────────┬────────────┘
                                 │ HTTP API
                    ┌────────────▼────────────┐
                    │    Node.js + Express    │
                    │       Backend API       │
                    └────────────┬────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │     Python Pipeline     │
                    └────────────┬────────────┘
                                 │
              ┌──────────────────┼──────────────────┐
              │                  │                  │
    ┌─────────▼────────┐ ┌───────▼────────┐ ┌──────▼─────────┐
    │  Market Data     │ │  News Pipeline │ │  Report Tools  │
    │  Collection      │ │  & Extraction  │ │  PDF Generation│
    └─────────┬────────┘ └───────┬────────┘ └──────┬─────────┘
              │                  │                  │
              └──────────────────┼──────────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │   Market Data + News    │
                    │       JSON Files        │
                    └────────────┬────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │     LangChain Agent     │
                    │  Gemini + Custom Tools  │
                    └────────────┬────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │   Morning Market Report │
                    │      Markdown + PDF     │
                    └─────────────────────────┘
```

## Project Structure

```text
marketOS/
│
├── backend/
│   ├── server.js
│   ├── package.json
│   └── .env.example
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   └── styles.css
│   ├── vite.config.js
│   ├── package.json
│   └── .env.example
│
├── src/
│   ├── agent.py
│   ├── market_data.py
│   ├── news_pipeline.py
│   ├── report_formatter.py
│   ├── report_generator.py
│   └── ...
│
├── fonts/
│   └── NotoSansTelugu-Regular.ttf
│
├── run.py
├── requirements.txt
├── .gitignore
└── README.md
```

Generated files and local development artifacts, such as `.env`, `.venv`, `node_modules`, `data`, and `reports`, are excluded from version control where configured in `.gitignore`.

## Getting Started

### Prerequisites

Install the following before running the project:

- Python 3.10 or a compatible version supported by the dependencies
- Node.js and npm
- Git
- A Google Gemini API key
- API keys for any external data providers configured in your environment

### 1. Clone the Repository

```bash
git clone https://github.com/RamTejaSoma/marketOS.git
cd marketOS
```

### 2. Set Up the Python Environment

Create a virtual environment in the project root:

```bash
python -m venv .venv
```

Activate it on Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install the Python dependencies:

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Configure the API keys and other settings required by your implementation.

For example, the Python pipeline may require a Gemini API key:

```env
GEMINI_API_KEY=your_gemini_api_key
```

If your code uses additional API keys, configure those as well.

For the backend and frontend, use the respective `.env.example` files as a reference and create local environment files with the variables required by your implementation.

**Important:** Never commit real API keys, passwords, or other secrets to GitHub.

### 4. Run the Python Pipeline

From the project root, activate the virtual environment and run:

```bash
python run.py
```

The pipeline orchestrates the configured market data collection, news aggregation, AI report generation, and report output stages.

Generated data and reports are stored in the configured local output directories.

### 5. Start the Backend

Open a terminal:

```bash
cd backend
npm install
```

Start the server using the script defined in `backend/package.json`. For example, if a `dev` script is configured:

```bash
npm run dev
```

### 6. Start the Frontend

Open another terminal:

```bash
cd frontend
npm install
```

Start the Vite development server using the script defined in `frontend/package.json`. For example:

```bash
npm run dev
```

Open the local URL printed by Vite in your terminal.

> **Note:** The frontend, backend, and Python pipeline are separate processes. Their environment variables, API URLs, and run commands must match your local configuration.

## Report Contents

The morning market report is intended to consolidate information such as:

- Major global index movements
- Sector-level performance
- US futures and international market indicators
- Volatility and Treasury yield movements
- Forex and commodity developments
- Financial and geopolitical news
- Economic and monetary developments
- Important market events and potential risks

The exact sections depend on the data collected and the report-generation prompt.

## Development Roadmap

- [x] Market data collection pipeline
- [x] Financial news aggregation and article extraction
- [x] LangChain agent integration
- [x] Markdown report generation
- [x] PDF report generation
- [x] React dashboard foundation
- [x] Node.js and Express backend foundation
- [ ] Improve source coverage and data reliability
- [ ] Enhance report analysis and source attribution
- [ ] Add richer multi-turn conversations over collected market data
- [ ] Improve historical report comparison and visualization
- [ ] Add more robust scheduling, logging, and error handling

*The roadmap reflects the intended development direction and may change as the project evolves.*

## Security

- Store API keys in local environment variables.
- Keep `.env` files out of version control.
- Do not expose private API credentials in frontend code.
- Validate backend inputs and handle external API failures.
- Treat generated market analysis as informational research, not guaranteed financial advice.

## Disclaimer

MarketOS is a software and research project intended for financial market intelligence and educational purposes. Its reports may contain incomplete, delayed, or inaccurate information. They should not be treated as personalized investment advice or as a guarantee of future market performance.

## Author

Developed as a project exploring financial data pipelines, AI agents, LLM tool calling, and market intelligence automation.

## Repository

[GitHub — MarketOS](https://github.com/RamTejaSoma/marketOS)

# LLM Feeder

A specialized web crawler designed to turn documentation sites into a single, clean Markdown file - perfect for feeding context to LLMs like ChatGPT, Claude, or Gemini.

## Why use this?
When building with AI, you often need "the whole docs" in your prompt context. Copy-pasting page by page is tedious. Context Crawler automates this by:
1.  **Crawling** an entire documentation section (e.g., `docs.example.com/v2`).
2.  **Cleaning** the noise (navbars, footers, ads).
3.  **Consolidating** everything into one `docs.md` file you can drop straight into your AI context window.

## Features
- **Smart Scoping**: Stays within the documentation path you specify.
- **LLM-Ready Output**: Strips HTML clutter to save token usage.
- **Playwright Powered**: Handles modern React/Vue/SPA documentation sites effortlessly.

## Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd context-crawler
    ```

2.  **Set up a virtual environment (Recommended):**
    ```bash
    # Windows
    python -m venv venv
    .\venv\Scripts\activate

    # macOS/Linux
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r scraper_tool/requirements.txt
    ```

4.  **Install Playwright browsers:**
    ```bash
    playwright install
    ```

## Usage

Generate your context file with a single command:

```bash
python scraper_tool/scraper.py --url https://docs.example.com/guide --output context.md
```

### Options
- `--url`: The starting URL (e.g., the introduction page of the docs).
- `--output`: The output file name (Default: `docs.md`).

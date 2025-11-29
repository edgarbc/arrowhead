# Arrowhead 🏹

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://python.org)
[![UV](https://img.shields.io/badge/UV-Fast%20Python%20Package%20Manager-orange.svg)](https://docs.astral.sh/uv/)
[![Ollama](https://img.shields.io/badge/Ollama-Local%20LLMs-green.svg)](https://ollama.ai)
[![CI](https://github.com/edgarbc/arrowhead/actions/workflows/ci.yml/badge.svg)](https://github.com/edgarbc/arrowhead/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> **TL;DR:** Arrowhead is an LLM-powered CLI tool that automatically summarizes your Obsidian journal entries by hashtag. Point it at your vault, specify a hashtag like `#meeting` or `#work`, and get weekly summaries powered by local LLMs (Ollama) or cloud APIs (OpenAI).

---

## 🎯 Problem Statement

Keeping weekly retrospectives and summaries up-to-date is tedious. If you use Obsidian for daily journaling with hashtags to categorize entries (e.g., `#meeting`, `#work`, `#learning`), you probably spend time manually reviewing and consolidating notes at the end of each week.

**Arrowhead solves this** by automatically scanning your vault, filtering entries by hashtag and date range, and generating well-structured summaries using LLMs—all while keeping your data private with local models.

## 🎯 Overview

Arrowhead is a CLI tool that automates the repetitive task of creating weekly summaries from your Obsidian vault. It scans your journal entries, filters by hashtags and date ranges, and generates consolidated summaries using local LLMs via Ollama.

![Arrowhead Demo](docs/screenshot-placeholder.png)
<!-- Screenshot placeholder - see docs/SCREENSHOT_README.md for instructions -->

### ✨ Features

- **🔍 Smart Vault Scanning** - Discovers markdown files while excluding Obsidian-specific directories
- **🏷️ Hashtag Filtering** - Filter entries by specific hashtags (e.g., `#meeting`, `#work`)
- **📅 Date Range Support** - Focus on specific weeks or date ranges
- **🤖 Local LLM Integration** - Uses Ollama for cost-effective, privacy-focused summarization
- **☁️ Cloud API Support** - Optional OpenAI integration for cloud-based summarization
- **📦 Intelligent Batching** - Groups entries efficiently to respect token limits
- **📝 Structured Output** - Generates well-formatted summaries with metadata
- **💻 Chat with your notes** - Chat with your summaries using retrieval-augmented generation
- **⚡ Fast & Lightweight** - Built with UV for rapid development and deployment
- **🧪 CI-Ready Demo** - Includes deterministic offline summarizer for testing

## 🚀 Quick Start

### Prerequisites

- **Python 3.12+**
- **UV** (Fast Python package manager) - [Install UV](https://docs.astral.sh/uv/getting-started/installation/)
- **Ollama** (Local LLM runtime) - [Install Ollama](https://ollama.ai)

### Installation

```bash
# Clone the repository
git clone https://github.com/edgarbc/arrowhead.git
cd arrowhead

# Install dependencies with UV
uv sync

# Install in development mode
uv pip install -e .
```

### Configure Local LLM (Ollama)

```bash
# Install Ollama (macOS)
brew install ollama

# Or download from https://ollama.ai

# Start Ollama service
ollama serve

# Pull a model (llama2 recommended for summarization)
ollama pull llama2

# Verify it's working
ollama list
```

### Environment Variables

```bash
# Optional: Configure Ollama endpoint (default: http://localhost:11434)
export OLLAMA_HOST="http://localhost:11434"
export OLLAMA_MODEL="llama2"

# Optional: For OpenAI integration
export OPENAI_API_KEY="your-api-key-here"
export OPENAI_MODEL="gpt-3.5-turbo"
```

### Run the Demo (No LLM Required)

```bash
# Install demo dependencies
pip install -r requirements.txt

# Download NLTK data
python -c "import nltk; nltk.download('punkt'); nltk.download('punkt_tab')"

# Run the demo (uses deterministic TextRank summarizer)
python demo/run_summary_demo.py
```

**Expected Output:**
```
============================================================
Arrowhead Demo - Obsidian Note Summarizer
============================================================

📄 Reading sample note...
   Loaded 1758 characters from sample_note.md

------------------------------------------------------------
📝 Original Note Preview (first 500 chars):
------------------------------------------------------------
# Daily Journal - 2024-12-02

## Morning Standup #meeting
...

------------------------------------------------------------
🎯 Generating Summary (using TextRank algorithm)...
------------------------------------------------------------

📋 Summary:

Had a productive morning standup with the team.
The team agreed that we need to prioritize the dashboard work...
Key takeaway: Understanding trade-offs between consistency...

============================================================
✅ Demo completed successfully!
============================================================
```

### Testing

The project has both unit tests and integration tests. Integration tests require a local Ollama instance running.

```bash
# Run smoke tests (no external dependencies)
python -m pytest tests/smoke_test.py -v

# Run all unit tests (no external dependencies)
uv run pytest tests/ -v -m "not integration"

# Run integration tests (requires Ollama)
uv run pytest tests/ -v --run-integration

# Run all tests including integration tests
uv run pytest tests/ -v --run-integration

# Run a specific test file
uv run pytest tests/test_scanner.py -v

# Run integration tests with specific model
uv run pytest tests/test_summarizer_integration.py -v --run-integration
```


### Basic Usage

```bash
# Generate a weekly summary for #meeting entries
arrowhead summarize /path/to/obsidian/vault --hashtag meeting

# Specify a custom date range
arrowhead summarize /path/to/vault --hashtag work \
  --week-start 2024-01-15 --week-end 2024-01-21

# Use a different LLM model
arrowhead summarize /path/to/vault --hashtag project \
  --model llama2:7b

# Chat with your summaries using RAG
arrowhead chat --summaries Summaries/

# Scan vault to see what would be processed
arrowhead scan /path/to/vault --hashtag meeting

```




## 📦 Project Structure

```bash
arrowhead/
├── README.md                # Project overview and setup instructions
├── pyproject.toml           # Dependency management
├── requirements.txt         # Demo/CI dependencies
├── src/
│   └── arrowhead/
│       ├── __init__.py      # Package initialization
│       ├── cli.py           # Entry point and CLI definitions
│       ├── scanner.py       # Vault scanning and file discovery
│       ├── parser.py        # Markdown parsing and hashtag filtering
│       ├── batcher.py       # Entry batching logic
│       ├── summarizer.py    # LLM prompt construction and API calls
│       ├── writer.py        # Summary aggregation and note writing
│       ├── utils.py         # Helper functions (date parsing, logging)
│       └── rag.py           # RAG system for chatting with summaries
├── demo/                    # Demo files for portfolio/CI
│   ├── sample_note.md       # Sample Obsidian note for demo
│   └── run_summary_demo.py  # Deterministic demo summarizer
├── tests/                   # Unit and integration tests
│   ├── conftest.py          # Pytest configuration
│   ├── smoke_test.py        # CI smoke tests
│   ├── test_scanner.py
│   ├── test_batcher.py
│   ├── test_summarizer.py
│   └── ...
├── examples/                # Sample vault and usage examples
│   └── journal/
│       └── 2024-12-02.md    # Example journal entry
├── .github/
│   └── workflows/
│       └── ci.yml           # GitHub Actions CI workflow
└── .gitignore               # Ignore venv, __pycache__, etc.
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**Made with ❤️ for the Obsidian community**
# Arrowhead 🏹

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![UV](https://img.shields.io/badge/UV-Fast%20Python%20Package%20Manager-orange.svg)](https://docs.astral.sh/uv/)
[![Ollama](https://img.shields.io/badge/Ollama-Local%20LLMs-green.svg)](https://ollama.ai)
[![DSPy](https://img.shields.io/badge/DSPy-Declarative%20LLM%20Programming-purple.svg)](https://github.com/stanfordnlp/dspy-ai)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-Passing-brightgreen.svg)](https://github.com/yourusername/arrowhead/actions)

> **Obsidian Weekly Hashtag Summarizer** - Automate weekly retrospectives by summarizing journal entries tagged with specific hashtags using local LLMs.

## 🎯 Overview

Arrowhead is a CLI tool that automates the repetitive task of creating weekly summaries from your Obsidian vault. It scans your journal entries, filters by hashtags and date ranges, and generates consolidated summaries using local LLMs via Ollama.

### ✨ Features

- **🔍 Smart Vault Scanning** - Discovers markdown files while excluding Obsidian-specific directories
- **��️ Hashtag Filtering** - Filter entries by specific hashtags (e.g., `#meeting`, `#work`)
- **📅 Date Range Support** - Focus on specific weeks or date ranges
- **🤖 Local LLM Integration** - Uses Ollama for cost-effective, privacy-focused summarization
- **📦 Intelligent Batching** - Groups entries efficiently to respect token limits
- **📝 Structured Output** - Generates well-formatted summaries with metadata
- **💻 Chat with your notes** - RAG system to chat with your notes.

## 🚀 Quick Start

### Prerequisites

- **Python 3.8+**
- **UV** (Fast Python package manager)
- **Ollama** (Local LLM runtime)

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/arrowhead.git
cd arrowhead

# Install dependencies with UV
uv sync

# Install in development mode
uv pip install -e .
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

# Dry run to see what would be processed
arrowhead summarize /path/to/vault --hashtag meeting --dry-run
```

## 📦 Project Structure

```bash
arrowhead/
├── README.md                # Project overview and setup instructions
├── pyproject.toml           # Dependency management (or setup.py)
├── src/
├── src/
│   └── arrowhead/
│       ├── __init__.py      # Core package
│       ├── cli.py           # Entry point and CLI definitions
│       ├── scanner.py       # Vault scanning and file discovery
│       ├── parser.py        # Markdown parsing and hashtag filtering
│       ├── batcher.py       # Entry batching logic
│       ├── summarizer.py    # LLM prompt construction and API calls
│       └── writer.py        # Summary aggregation and note writing
│       └── utils.py         # Helper functions (date parsing, logging)
├── tests/                   # Unit and integration tests
│   ├── test_scanner.py
│   ├── test_parser.py
│   ├── test_batcher.py
│   ├── test_summarizer.py
│   └── test_writer.py
├── examples/                # Sample vault and usage examples
│   └── journal/
│       ├── 2024-12-02.md   # Example journal entry markdown file
│       └── 2024-12-03.md
├── Summaries/               # Output folder for generated summaries
├── docs/                    # Additional documentation
│   └── usage.md             # Usage guide and FAQs
└── .gitignore               # Ignore venv, __pycache__, etc.

```
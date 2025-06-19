# arrowhead

```
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
│   └── sample_vault/
│       ├── day1.md
│       └── day2.md
├── Summaries/               # Output folder for generated summaries
├── docs/                    # Additional documentation
│   └── usage.md             # Usage guide and FAQs
└── .gitignore               # Ignore venv, __pycache__, etc.

```
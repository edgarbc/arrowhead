"""
Arrowhead - Obsidian Weekly Hashtag Summarizer

A CLI tool to automate weekly retrospectives by summarizing Obsidian journal entries
tagged with specific hashtags using LLM integration.
"""

__version__ = "0.1.0"
__author__ = "Edgar Bermudez"
__email__ = "edgar@gmail.com"

from .cli import app

__all__ = ["app"]
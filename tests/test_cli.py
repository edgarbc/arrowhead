# tests/test_cli.py
"""
Tests for CLI functionality.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from typer.testing import CliRunner
from datetime import datetime, timedelta
from pendulum import DateTime

from arrowhead.cli import app
from arrowhead.scanner import VaultScanner, ScanResult
from arrowhead.parser import EntryParser, JournalEntry
from arrowhead.batcher import EntryBatcher
from arrowhead.summarizer import LLMSummarizer, SummarizationResponse
from arrowhead.writer import SummaryWriter
from arrowhead.rag import SummaryRAG


class TestCLI:
    """Test CLI functionality."""
    
    @pytest.fixture
    def runner(self):
        """Create a CLI runner for testing."""
        return CliRunner()
    
    @pytest.fixture
    def mock_vault_path(self, tmp_path):
        """Create a mock vault directory."""
        vault = tmp_path / "test_vault"
        vault.mkdir()

        # create journal directory
        journal_dir = vault / "journal"
        journal_dir.mkdir()

        # create summaries directory
        summaries_dir = vault / "summaries"
        summaries_dir.mkdir()
        
        # create test markdown files
        (journal_dir / "2024-01-15.md").write_text("# Meeting Notes\nHad a #meeting with the team.")
        (journal_dir / "2024-01-16.md").write_text("# Follow-up\nFollowed up on #meeting action items.")
        (journal_dir / "2024-01-17.md").write_text("# Other Notes\nSome other notes without hashtags.")
        
        return vault
    
    @pytest.fixture
    def mock_entries(self):
        """Create mock journal entries."""
        return [
            JournalEntry(
                file_path=Path("test1.md"),
                title="Meeting Notes",
                content="Had a #meeting with the team about Q1 planning.",
                date=DateTime(2024, 1, 15),
                hashtags={"meeting"},
                frontmatter={},
                raw_content=""
            ),
            JournalEntry(
                file_path=Path("test2.md"),
                title="Follow-up",
                content="Followed up on #meeting action items.",
                date=DateTime(2024, 1, 16),
                hashtags={"meeting"},
                frontmatter={},
                raw_content=""
            )
        ]
    
    @pytest.fixture
    def mock_scan_result(self, mock_vault_path):
        """Create a mock scan result."""
        return ScanResult(
            vault_path=mock_vault_path,
            markdown_files=[
                mock_vault_path / "journal" / "2024-01-15.md",
                mock_vault_path / "journal" / "2024-01-16.md",
                mock_vault_path / "journal" / "2024-01-17.md"
            ],
            total_files=3,
            excluded_dirs=set(),
            scan_time_ms=100.0
        )
    
    @pytest.fixture
    def mock_summarization_response(self):
        """Create a mock summarization response."""
        return SummarizationResponse(
            content="Summary of meeting notes and follow-ups.",
            model="llama2:7b",
            request_time=2.5,
            tokens_used=150
        )

    def test_scan_command_basic(self, runner, mock_vault_path):
        """Test basic scan command functionality."""
        with patch('arrowhead.cli.VaultScanner') as mock_scanner_class:
            mock_scanner = Mock()
            mock_scanner.scan.return_value = ScanResult(
                vault_path=mock_vault_path,
                markdown_files=[mock_vault_path / "test.md"],
                total_files=1,
                excluded_dirs=set(),
                scan_time_ms=50.0
            )
            mock_scanner_class.return_value = mock_scanner
            
            result = runner.invoke(app, ["scan", str(mock_vault_path)])
            
            assert result.exit_code == 0
            assert "Vault:" in result.stdout
            assert "Found 1 markdown files" in result.stdout
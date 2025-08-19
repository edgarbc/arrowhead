
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

        # Create journal directory
        journal_dir = vault / "journal"
        journal_dir.mkdir()

        # Create summaries directory
        summaries_dir = vault / "Summaries"
        summaries_dir.mkdir()
        
        # Create test markdown files
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

    def test_scan_command_with_hashtag(self, runner, mock_vault_path):
        """Test scan command with hashtag filtering."""
        with patch('arrowhead.cli.VaultScanner') as mock_scanner_class, \
             patch('arrowhead.cli.EntryParser') as mock_parser_class:
            
            mock_scanner = Mock()
            mock_scanner.scan.return_value = ScanResult(
                vault_path=mock_vault_path,
                markdown_files=[mock_vault_path / "test.md"],
                total_files=1,
                excluded_dirs=set(),
                scan_time_ms=50.0
            )
            mock_scanner_class.return_value = mock_scanner
            
            mock_parser = Mock()
            mock_parser.parse_files.return_value = [
                JournalEntry(
                    file_path=Path("test.md"),
                    title="Test",
                    content="Test content",
                    date=DateTime(2024, 1, 15),
                    hashtags={"meeting"},
                    frontmatter={},
                    raw_content=""
                )
            ]
            mock_parser_class.return_value = mock_parser
            
            result = runner.invoke(app, ["scan", str(mock_vault_path), "--hashtag", "meeting"])
            
            assert result.exit_code == 0
            assert "Found 1 entries with #meeting" in result.stdout

    def test_scan_command_invalid_path(self, runner):
        """Test scan command with invalid vault path."""
        result = runner.invoke(app, ["scan", "/nonexistent/path"])
        
        assert result.exit_code != 0
        assert "Error" in result.stdout

    @patch('arrowhead.cli.VaultScanner')
    @patch('arrowhead.cli.EntryParser')
    @patch('arrowhead.cli.EntryBatcher')
    @patch('arrowhead.cli.LLMSummarizer')
    @patch('arrowhead.cli.SummaryWriter')
    @patch('arrowhead.cli.setup_logging')
    @patch('arrowhead.cli.parse_date_range')
    def test_summarize_command_basic(self, mock_parse_date, mock_setup_logging, 
                                   mock_writer_class, mock_summarizer_class, 
                                   mock_batcher_class, mock_parser_class, mock_scanner_class,
                                   runner, mock_vault_path, mock_entries, mock_summarization_response):
        """Test basic summarize command functionality."""
        # Setup mocks
        mock_setup_logging.return_value = None
        mock_parse_date.return_value = (DateTime(2024, 1, 15), DateTime(2024, 1, 16))
        
        mock_scanner = Mock()
        mock_scanner.scan.return_value = ScanResult(
            vault_path=mock_vault_path,
            markdown_files=[mock_vault_path / "test.md"],
            total_files=1,
            excluded_dirs=set(),
            scan_time_ms=50.0
        )
        mock_scanner_class.return_value = mock_scanner
        
        mock_parser = Mock()
        mock_parser.parse_files.return_value = mock_entries
        mock_parser_class.return_value = mock_parser
        
        mock_batcher = Mock()
        mock_batcher.create_batches.return_value = [mock_entries]
        mock_batcher_class.return_value = mock_batcher
        
        mock_summarizer = Mock()
        mock_summarizer.summarize_batch.return_value = mock_summarization_response
        mock_summarizer_class.return_value = mock_summarizer
        
        mock_writer = Mock()
        mock_writer.write_summary.return_value = mock_vault_path / "Summaries" / "summary.md"
        mock_writer_class.return_value = mock_writer
        
        result = runner.invoke(app, ["summarize", str(mock_vault_path), "--hashtag", "meeting"])
        
        assert result.exit_code == 0
        assert "summary written to" in result.stdout.lower()

    def test_summarize_command_no_entries(self, runner, mock_vault_path):
        """Test summarize command when no entries are found."""
        with patch('arrowhead.cli.VaultScanner') as mock_scanner_class, \
             patch('arrowhead.cli.EntryParser') as mock_parser_class, \
             patch('arrowhead.cli.setup_logging'), \
             patch('arrowhead.cli.parse_date_range'):
            
            mock_scanner = Mock()
            mock_scanner.scan.return_value = ScanResult(
                vault_path=mock_vault_path,
                markdown_files=[mock_vault_path / "test.md"],
                total_files=1,
                excluded_dirs=set(),
                scan_time_ms=50.0
            )
            mock_scanner_class.return_value = mock_scanner
            
            mock_parser = Mock()
            mock_parser.parse_files.return_value = []  # No entries found
            mock_parser_class.return_value = mock_parser
            
            result = runner.invoke(app, ["summarize", str(mock_vault_path), "--hashtag", "meeting"])
            
            assert result.exit_code == 0
            assert "No entries found" in result.stdout

    def test_summarize_command_with_date_range(self, runner, mock_vault_path):
        """Test summarize command with date range."""
        with patch('arrowhead.cli.VaultScanner') as mock_scanner_class, \
             patch('arrowhead.cli.EntryParser') as mock_parser_class, \
             patch('arrowhead.cli.EntryBatcher') as mock_batcher_class, \
             patch('arrowhead.cli.LLMSummarizer') as mock_summarizer_class, \
             patch('arrowhead.cli.SummaryWriter') as mock_writer_class, \
             patch('arrowhead.cli.setup_logging'), \
             patch('arrowhead.cli.parse_date_range') as mock_parse_date:
            
            mock_parse_date.return_value = (DateTime(2024, 1, 15), DateTime(2024, 1, 21))
            
            # Setup mocks
            mock_scanner = Mock()
            mock_scanner.scan.return_value = ScanResult(
                vault_path=mock_vault_path,
                markdown_files=[mock_vault_path / "test.md"],
                total_files=1,
                excluded_dirs=set(),
                scan_time_ms=50.0
            )
            mock_scanner_class.return_value = mock_scanner
            
            mock_parser = Mock()
            mock_parser.parse_files.return_value = []
            mock_parser_class.return_value = mock_parser
            
            mock_batcher = Mock()
            mock_batcher.create_batches.return_value = []
            mock_batcher_class.return_value = mock_batcher
            
            mock_summarizer = Mock()
            mock_summarizer_class.return_value = mock_summarizer
            
            mock_writer = Mock()
            mock_writer_class.return_value = mock_writer
            
            result = runner.invoke(app, [
                "summarize", str(mock_vault_path), 
                "--hashtag", "meeting",
                "--week-start", "2024-01-15",
                "--week-end", "2024-01-21"
            ])
            
            assert result.exit_code == 0
            mock_parse_date.assert_called_with("2024-01-15", "2024-01-21")

    def test_summarize_command_with_custom_model(self, runner, mock_vault_path):
        """Test summarize command with custom model."""
        with patch('arrowhead.cli.VaultScanner') as mock_scanner_class, \
             patch('arrowhead.cli.EntryParser') as mock_parser_class, \
             patch('arrowhead.cli.EntryBatcher') as mock_batcher_class, \
             patch('arrowhead.cli.LLMSummarizer') as mock_summarizer_class, \
             patch('arrowhead.cli.SummaryWriter') as mock_writer_class, \
             patch('arrowhead.cli.setup_logging'), \
             patch('arrowhead.cli.parse_date_range'):
            
            # Setup mocks
            mock_scanner = Mock()
            mock_scanner.scan.return_value = ScanResult(
                vault_path=mock_vault_path,
                markdown_files=[mock_vault_path / "test.md"],
                total_files=1,
                excluded_dirs=set(),
                scan_time_ms=50.0
            )
            mock_scanner_class.return_value = mock_scanner
            
            mock_parser = Mock()
            mock_parser.parse_files.return_value = []
            mock_parser_class.return_value = mock_parser
            
            mock_batcher = Mock()
            mock_batcher.create_batches.return_value = []
            mock_batcher_class.return_value = mock_batcher
            
            mock_summarizer = Mock()
            mock_summarizer_class.return_value = mock_summarizer
            
            mock_writer = Mock()
            mock_writer_class.return_value = mock_writer
            
            result = runner.invoke(app, [
                "summarize", str(mock_vault_path), 
                "--hashtag", "meeting",
                "--model", "mistral:7b"
            ])
            
            assert result.exit_code == 0
            # Verify the correct model was used
            mock_summarizer_class.assert_called_with("mistral:7b")

    def test_summarize_command_with_custom_output(self, runner, mock_vault_path):
        """Test summarize command with custom output directory."""
        with patch('arrowhead.cli.VaultScanner') as mock_scanner_class, \
             patch('arrowhead.cli.EntryParser') as mock_parser_class, \
             patch('arrowhead.cli.EntryBatcher') as mock_batcher_class, \
             patch('arrowhead.cli.LLMSummarizer') as mock_summarizer_class, \
             patch('arrowhead.cli.SummaryWriter') as mock_writer_class, \
             patch('arrowhead.cli.setup_logging'), \
             patch('arrowhead.cli.parse_date_range'):
            
            # Setup mocks
            mock_scanner = Mock()
            mock_scanner.scan.return_value = ScanResult(
                vault_path=mock_vault_path,
                markdown_files=[mock_vault_path / "test.md"],
                total_files=1,
                excluded_dirs=set(),
                scan_time_ms=50.0
            )
            mock_scanner_class.return_value = mock_scanner
            
            mock_parser = Mock()
            mock_parser.parse_files.return_value = []
            mock_parser_class.return_value = mock_parser
            
            mock_batcher = Mock()
            mock_batcher.create_batches.return_value = []
            mock_batcher_class.return_value = mock_batcher
            
            mock_summarizer = Mock()
            mock_summarizer_class.return_value = mock_summarizer
            
            mock_writer = Mock()
            mock_writer_class.return_value = mock_writer
            
            custom_output = mock_vault_path / "custom_output"
            result = runner.invoke(app, [
                "summarize", str(mock_vault_path), 
                "--hashtag", "meeting",
                "--output-dir", str(custom_output)
            ])
            
            assert result.exit_code == 0
            # Verify the correct output directory was used
            mock_writer_class.assert_called_with(custom_output)

    def test_summarize_command_error_handling(self, runner, mock_vault_path):
        """Test summarize command error handling."""
        with patch('arrowhead.cli.VaultScanner') as mock_scanner_class, \
             patch('arrowhead.cli.setup_logging'):
            mock_scanner = Mock()
            mock_scanner.scan.side_effect = Exception("Test error")
            mock_scanner_class.return_value = mock_scanner
            
            result = runner.invoke(app, ["summarize", str(mock_vault_path), "--hashtag", "meeting"])
            
            assert result.exit_code == 1
            assert "Error:" in result.stdout

    @patch('arrowhead.cli.SummaryRAG')
    def test_chat_command_basic(self, mock_rag_class, runner, tmp_path):
        """Test basic chat command functionality."""
        mock_rag = Mock()
        mock_rag.chat.return_value = "This is a test response."
        mock_rag_class.return_value = mock_rag
        
        summaries_dir = tmp_path / "summaries"
        summaries_dir.mkdir()
        
        # Mock input to simulate user typing 'quit'
        with patch('builtins.input', return_value='quit'):
            result = runner.invoke(app, ["chat", "--summaries", str(summaries_dir)])
        
        assert result.exit_code == 0
        assert "Chat with your summaries" in result.stdout

    def test_chat_command_no_summaries_dir(self, runner):
        """Test chat command without specifying summaries directory."""
        result = runner.invoke(app, ["chat"])
        
        assert result.exit_code == 1
        assert "Error: Please specify --summaries directory" in result.stdout

    def test_chat_command_invalid_summaries_dir(self, runner):
        """Test chat command with invalid summaries directory."""
        result = runner.invoke(app, ["chat", "--summaries", "/nonexistent/path"])
        
        assert result.exit_code == 1
        assert "Error:" in result.stdout

    @patch('arrowhead.cli.SummaryRAG')
    def test_chat_command_with_custom_model(self, mock_rag_class, runner, tmp_path):
        """Test chat command with custom model."""
        mock_rag = Mock()
        mock_rag.chat.return_value = "Test response"
        mock_rag_class.return_value = mock_rag
        
        summaries_dir = tmp_path / "summaries"
        summaries_dir.mkdir()
        
        with patch('builtins.input', return_value='quit'):
            result = runner.invoke(app, [
                "chat", 
                "--summaries", str(summaries_dir),
                "--model", "mistral:7b"
            ])
        
        assert result.exit_code == 0
        # Verify the correct model was used
        mock_rag_class.assert_called_with(summaries_dir, "mistral:7b")

    def test_help_command(self, runner):
        """Test help command."""
        result = runner.invoke(app, ["--help"])
        
        assert result.exit_code == 0
        assert "Obsidian Weekly Hashtag Summarizer" in result.stdout

    def test_summarize_help(self, runner):
        """Test summarize command help."""
        result = runner.invoke(app, ["summarize", "--help"])
        
        assert result.exit_code == 0
        assert "Generate a weekly summary" in result.stdout

    def test_scan_help(self, runner):
        """Test scan command help."""
        result = runner.invoke(app, ["scan", "--help"])
        
        assert result.exit_code == 0
        assert "Scan vault and show available entries" in result.stdout

    def test_chat_help(self, runner):
        """Test chat command help."""
        result = runner.invoke(app, ["chat", "--help"])
        
        assert result.exit_code == 0
        assert "Chat with your summaries using RAG" in result.stdout


class TestCLIIntegration:
    """Integration tests for CLI with real components."""
    
    @pytest.fixture
    def runner(self):
        return CliRunner()
    
    @pytest.fixture
    def real_vault_path(self, tmp_path):
        """Create a real vault with test files."""
        vault = tmp_path / "real_vault"
        vault.mkdir()
        
        # Create .obsidian directory to make it a real vault
        (vault / ".obsidian").mkdir()
        
        # Create test journal entries
        journal_dir = vault / "journal"
        journal_dir.mkdir()
        
        (journal_dir / "2024-01-15.md").write_text("""
# Meeting Notes

Had a #meeting with the team about Q1 planning.

## Action Items
- [ ] Review budget
- [ ] Schedule follow-up
        """)
        
        (journal_dir / "2024-01-16.md").write_text("""
# Follow-up

Followed up on #meeting action items.

## Progress
- [x] Review budget
- [ ] Schedule follow-up
        """)
        
        (journal_dir / "2024-01-17.md").write_text("""
# Other Notes

Some other notes without hashtags.
        """)
        
        return vault

    @pytest.mark.integration
    def test_real_scan_command(self, runner, real_vault_path):
        """Test scan command with real vault."""
        result = runner.invoke(app, ["scan", str(real_vault_path)])
        
        assert result.exit_code == 0
        assert "Found" in result.stdout
        assert "markdown files" in result.stdout

    @pytest.mark.integration
    def test_real_scan_command_with_hashtag(self, runner, real_vault_path):
        """Test scan command with hashtag filtering on real vault."""
        result = runner.invoke(app, ["scan", str(real_vault_path), "--hashtag", "meeting"])
        
        assert result.exit_code == 0
        assert "Found" in result.stdout
        assert "entries with #meeting" in result.stdout

    @pytest.mark.integration
    @pytest.mark.skipif(True, reason="Requires Ollama integration")
    def test_real_summarize_command(self, runner, real_vault_path):
        """Test summarize command with real vault (requires Ollama)."""
        result = runner.invoke(app, [
            "summarize", str(real_vault_path), 
            "--hashtag", "meeting",
            "--week-start", "2024-01-15",
            "--week-end", "2024-01-16"
        ])
        
        assert result.exit_code == 0
        assert "summary written to" in result.stdout.lower()
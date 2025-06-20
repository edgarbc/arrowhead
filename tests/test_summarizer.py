"""
Tests for the LLMSummarizer functionality.
"""

import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
from datetime import datetime
from arrowhead.summarizer import LLMSummarizer, SummarizationRequest, SummarizationResponse
from arrowhead.parser import JournalEntry

class TestLLMSummarizer:
    """Test cases for LLMSummarizer."""
    
    def test_summarizer_initialization(self):
        """Test summarizer initialization."""
        summarizer = LLMSummarizer("llama2:7b")
        assert summarizer.model == "llama2:7b"
        assert summarizer.is_local_model is True
        
        summarizer = LLMSummarizer("gpt-4o-mini")
        assert summarizer.model == "gpt-4o-mini"
        assert summarizer.is_local_model is False
    
    def test_summarize_empty_batch(self):
        """Test summarizing an empty batch."""
        summarizer = LLMSummarizer("llama2:7b")
        response = summarizer.summarize_batch([], "meeting")
        
        assert response.content == "No entries to summarize."
        assert response.model == "llama2:7b"
        assert response.error is None
    
    def test_generate_prompt(self):
        """Test prompt generation."""
        summarizer = LLMSummarizer("llama2:7b")
        
        # Create test entries
        entries = [
            JournalEntry(
                file_path=Path("test1.md"),
                title="Test Entry 1",
                content="Had a #meeting with the team",
                date=datetime(2024, 1, 15),
                hashtags={"meeting"},
                frontmatter={},
                raw_content=""
            )
        ]
        
        request = SummarizationRequest(
            entries=entries,
            hashtag="meeting",
            start_date=datetime(2024, 1, 15),
            end_date=datetime(2024, 1, 21),
            batch_id=1,
            total_batches=1
        )
        
        prompt = summarizer._generate_prompt(request)
        
        assert "meeting" in prompt
        assert "2024-01-15 to 2024-01-21" in prompt
        assert "Test Entry 1" in prompt
        assert "Had a #meeting with the team" in prompt
    
    @patch('arrowhead.summarizer.httpx.Client')
    def test_call_ollama_success(self, mock_client):
        """Test successful Ollama API call."""
        # Mock the response
        mock_response = MagicMock()
        mock_response.json.return_value = {"response": "This is a test summary."}
        mock_response.raise_for_status.return_value = None
        
        mock_client_instance = MagicMock()
        mock_client_instance.post.return_value = mock_response
        mock_client.return_value.__enter__.return_value = mock_client_instance
        
        summarizer = LLMSummarizer("llama2:7b")
        response = summarizer._call_ollama("Test prompt")
        
        assert response == "This is a test summary."
        
        # Verify the API call
        mock_client_instance.post.assert_called_once()
        call_args = mock_client_instance.post.call_args
        assert call_args[0][0] == "http://localhost:11434/api/generate"
        
        payload = call_args[1]["json"]
        assert payload["model"] == "llama2:7b"
        assert payload["prompt"] == "Test prompt"
    
    @patch('arrowhead.summarizer.httpx.Client')
    def test_call_ollama_failure(self, mock_client):
        """Test Ollama API call failure."""
        mock_client_instance = MagicMock()
        mock_client_instance.post.side_effect = Exception("Connection failed")
        mock_client.return_value.__enter__.return_value = mock_client_instance
        
        summarizer = LLMSummarizer("llama2:7b")
        
        with pytest.raises(Exception, match="Connection failed"):
            summarizer._call_ollama("Test prompt")
    
    @patch('arrowhead.summarizer.openai.OpenAI')
    def test_call_openai_success(self, mock_openai):
        """Test successful OpenAI API call."""
        # Mock the response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "This is an OpenAI summary."
        
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            summarizer = LLMSummarizer("gpt-4o-mini")
            response = summarizer._call_openai("Test prompt")
            
            assert response == "This is an OpenAI summary."
    
    def test_format_entries(self):
        """Test entry formatting."""
        summarizer = LLMSummarizer("llama2:7b")
        
        entries = [
            JournalEntry(
                file_path=Path("test1.md"),
                title="Test Entry 1",
                content="Short content",
                date=datetime(2024, 1, 15),
                hashtags={"meeting"},
                frontmatter={},
                raw_content=""
            ),
            JournalEntry(
                file_path=Path("test2.md"),
                title="Test Entry 2",
                content="Another short content",
                date=None,
                hashtags={"meeting"},
                frontmatter={},
                raw_content=""
            )
        ]
        
        formatted = summarizer._format_entries(entries)
        
        assert "2024-01-15 - Test Entry 1" in formatted
        assert "Unknown date - Test Entry 2" in formatted
        assert "Short content" in formatted
        assert "Another short content" in formatted
        assert "---" in formatted  # Separator between entries
    
    def test_format_entries_truncation(self):
        """Test entry formatting with content truncation."""
        summarizer = LLMSummarizer("llama2:7b")
        
        # Create content longer than 1000 characters
        long_content = "A" * 1100
        
        entries = [
            JournalEntry(
                file_path=Path("test1.md"),
                title="Test Entry",
                content=long_content,
                date=datetime(2024, 1, 15),
                hashtags={"meeting"},
                frontmatter={},
                raw_content=""
            )
        ]
        
        formatted = summarizer._format_entries(entries)
        
        assert len(formatted) < len(long_content) + 100  # Should be truncated
        assert "[truncated]" in formatted
    
    @patch('arrowhead.summarizer.httpx.Client')
    def test_test_connection_success(self, mock_client):
        """Test successful connection test."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "models": [{"name": "llama2:7b", "size": 123456}]
        }
        mock_response.raise_for_status.return_value = None
        
        mock_client_instance = MagicMock()
        mock_client_instance.get.return_value = mock_response
        mock_client.return_value.__enter__.return_value = mock_client_instance
        
        summarizer = LLMSummarizer("llama2:7b")
        result = summarizer.test_connection()
        
        assert result is True
    
    @patch('arrowhead.summarizer.httpx.Client')
    def test_test_connection_model_not_found(self, mock_client):
        """Test connection test when model is not available."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "models": [{"name": "mistral:7b", "size": 123456}]
        }
        mock_response.raise_for_status.return_value = None
        
        mock_client_instance = MagicMock()
        mock_client_instance.get.return_value = mock_response
        mock_client.return_value.__enter__.return_value = mock_client_instance
        
        summarizer = LLMSummarizer("llama2:7b")
        result = summarizer.test_connection()
        
        assert result is False
    
    def test_get_model_info(self):
        """Test getting model information."""
        summarizer = LLMSummarizer("llama2:7b")
        info = summarizer.get_model_info()
        
        assert info["model"] == "llama2:7b"
        assert info["is_local"] is True
        assert info["host"] == "http://localhost:11434"
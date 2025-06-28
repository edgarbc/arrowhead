"""
Tests for the RAG functionality.
"""

import pytest
from pathlib import Path
from datetime import datetime
from arrowhead.rag import SummaryRAG, ChatMessage, SearchResult

class TestSummaryRAG:
    """Test cases for SummaryRAG."""
    
    def test_rag_initialization(self, tmp_path):
        """Test RAG system initialization."""
        # Create a summaries directory
        summaries_dir = tmp_path / "Summaries"
        summaries_dir.mkdir()
        
        rag = SummaryRAG(summaries_dir)
        assert rag.summaries_dir == summaries_dir
        assert rag.model == "llama2:7b"
        assert len(rag.chat_history) == 0
    
    def test_rag_invalid_directory(self):
        """Test RAG initialization with invalid directory."""
        with pytest.raises(ValueError, match="does not exist"):
            SummaryRAG(Path("/nonexistent/path"))
    
    def test_search_summaries(self, tmp_path):
        """Test searching through summaries."""
        # Create test summaries
        summaries_dir = tmp_path / "Summaries"
        summaries_dir.mkdir()
        
        # Create a test summary
        summary_content = """# Week Summary - #meeting (2024-01-15 to 2024-01-21)

## Monday, 2024-01-15
- Had a team meeting about project planning
- Discussed Q1 goals and objectives

## Tuesday, 2024-01-16
- Follow-up meeting on action items
- Reviewed project timeline
"""
        
        (summaries_dir / "Week-2024-01-15-meeting.md").write_text(summary_content)
        
        rag = SummaryRAG(summaries_dir)
        results = rag.search_summaries("project planning")
        
        assert len(results) == 1
        assert "project planning" in results[0].relevant_content.lower()
        assert results[0].hashtag == "meeting"
    
    def test_calculate_relevance(self, tmp_path):
        """Test relevance calculation."""
        summaries_dir = tmp_path / "Summaries"
        summaries_dir.mkdir()
        
        rag = SummaryRAG(summaries_dir)
        
        content = "Had a meeting about project planning and team goals."
        query = "project planning"
        
        score = rag._calculate_relevance(content, query)
        assert score > 0
        assert score <= 1.0
    
    def test_extract_metadata(self, tmp_path):
        """Test metadata extraction."""
        summaries_dir = tmp_path / "Summaries"
        summaries_dir.mkdir()
        
        rag = SummaryRAG(summaries_dir)
        
        # Test filename parsing
        metadata = rag._extract_metadata(
            Path("Week-2024-01-15-meeting.md"),
            "Test content"
        )
        
        assert metadata['hashtag'] == 'meeting'
        assert metadata['date'] == datetime(2024, 1, 15)
    
    def test_chat_basic(self, tmp_path):
        """Test basic chat functionality."""
        # Create test summaries
        summaries_dir = tmp_path / "Summaries"
        summaries_dir.mkdir()
        
        summary_content = """# Week Summary - #meeting

## Monday
- Had a team meeting about project planning
"""
        
        (summaries_dir / "test-summary.md").write_text(summary_content)
        
        rag = SummaryRAG(summaries_dir)
        
        # Mock the LLM call
        with pytest.MonkeyPatch().context() as m:
            m.setattr(rag.summarizer, '_call_ollama', lambda prompt: "Based on the summaries, there was a team meeting about project planning.")
            
            response = rag.chat("What meetings happened this week?")
            
            assert "team meeting" in response.lower()
            assert len(rag.chat_history) == 2  # user + assistant
    
    def test_chat_no_results(self, tmp_path):
        """Test chat when no relevant content is found."""
        summaries_dir = tmp_path / "Summaries"
        summaries_dir.mkdir()
        
        rag = SummaryRAG(summaries_dir)
        
        response = rag.chat("What meetings happened this week?")
        
        assert "couldn't find" in response.lower()
        assert len(rag.chat_history) == 2
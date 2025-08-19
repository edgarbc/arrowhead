"""
Integration tests for LLMSummarizer with real Ollama calls.
"""

import pytest
from pathlib import Path
from datetime import datetime
from pendulum import DateTime
from arrowhead.summarizer import LLMSummarizer
from arrowhead.parser import JournalEntry



def _ollama_available() -> bool:
    """Check if Ollama is available and running."""
    try:
        import httpx
        with httpx.Client(timeout=5.0) as client:
            response = client.get("http://localhost:11434/api/tags")
            return response.status_code == 200
    except Exception:
        return False

class TestLLMSummarizerIntegration:
    """Integration tests with real Ollama calls."""
    
    @pytest.mark.integration
    @pytest.mark.skipif(not _ollama_available(), reason="Ollama not available")
    def test_real_ollama_call(self):
        """Test actual call to Ollama API."""
        summarizer = LLMSummarizer("llama2:7b")
        
        # Test connection first
        assert summarizer.test_connection(), "Ollama connection failed"
        
        # Create a simple test prompt
        test_prompt = "Summarize this: Had a meeting with the team about project planning."
        
        # Make real API call
        response = summarizer._call_ollama(test_prompt)
        
        # Basic validation
        assert response is not None
        assert len(response) > 0
        assert isinstance(response, str)
        
        print(f"Ollama response: {response[:100]}...")
    
    @pytest.mark.integration
    @pytest.mark.skipif(not _ollama_available(), reason="Ollama not available")
    def test_summarize_batch_with_real_ollama(self):
        """Test full summarization pipeline with real Ollama."""
        # Create test entries
        entries = [
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
        
        summarizer = LLMSummarizer("llama2:7b")
        
        # Test connection
        if not summarizer.test_connection():
            pytest.skip("Ollama not available")
        
        # Make real summarization call
        response = summarizer.summarize_batch(
            entries=entries,
            hashtag="meeting",
            start_date=DateTime(2024, 1, 15),
            end_date=DateTime(2024, 1, 16)
        )
        
        # Validate response
        assert response.content is not None
        assert len(response.content) > 0
        assert response.model == "llama2:7b"
        assert response.error is None
        assert response.request_time > 0
        
        print(f"Summary: {response.content}")
    
    @pytest.mark.integration
    @pytest.mark.skipif(not _ollama_available(), reason="Ollama not available")
    def test_different_models(self):
        """Test with different available models."""
        summarizer = LLMSummarizer("llama2:7b")
        
        if not summarizer.test_connection():
            pytest.skip("Ollama not available")
        
        # Get model info
        model_info = summarizer.get_model_info()
        print(f"Model info: {model_info}")
        
        # Test with a simple prompt
        test_prompt = "Say hello in one sentence."
        response = summarizer._call_ollama(test_prompt)
        
        assert response is not None
        assert len(response) > 0
        print(f"Model response: {response}")


# Pytest configuration
def pytest_configure(config):
    """Add custom markers."""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )

def pytest_collection_modifyitems(config, items):
    """Skip integration tests by default unless --run-integration is passed."""
    if not config.getoption("--run-integration"):
        skip_integration = pytest.mark.skip(reason="need --run-integration option to run")
        for item in items:
            if "integration" in item.keywords:
                item.add_marker(skip_integration)
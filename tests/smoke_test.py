"""
Smoke test for the Arrowhead demo summarizer.

This test verifies that the demo script can:
1. Successfully read the sample note
2. Generate a non-empty summary
3. Run without external LLM dependencies (deterministic mode)

Run with:
    pytest tests/smoke_test.py -v
    
Or directly:
    python -m pytest tests/smoke_test.py -v
"""

import subprocess
import sys
from pathlib import Path


# Path to the demo directory
DEMO_DIR = Path(__file__).parent.parent / "demo"
DEMO_SCRIPT = DEMO_DIR / "run_summary_demo.py"
SAMPLE_NOTE = DEMO_DIR / "sample_note.md"


class TestSmokeTest:
    """Smoke tests for the demo summarizer."""
    
    def test_sample_note_exists(self):
        """Test that the sample note file exists."""
        assert SAMPLE_NOTE.exists(), f"Sample note not found: {SAMPLE_NOTE}"
    
    def test_sample_note_has_content(self):
        """Test that the sample note has content."""
        content = SAMPLE_NOTE.read_text()
        assert len(content) > 100, "Sample note should have meaningful content"
        assert "#" in content, "Sample note should contain hashtags"
    
    def test_demo_script_exists(self):
        """Test that the demo script exists."""
        assert DEMO_SCRIPT.exists(), f"Demo script not found: {DEMO_SCRIPT}"
    
    def test_demo_script_runs_successfully(self):
        """Test that the demo script runs without errors."""
        result = subprocess.run(
            [sys.executable, str(DEMO_SCRIPT)],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        assert result.returncode == 0, (
            f"Demo script failed with return code {result.returncode}.\n"
            f"stdout: {result.stdout}\n"
            f"stderr: {result.stderr}"
        )
    
    def test_demo_produces_output(self):
        """Test that the demo script produces non-empty output."""
        result = subprocess.run(
            [sys.executable, str(DEMO_SCRIPT)],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        assert result.stdout, "Demo script should produce output"
        assert len(result.stdout) > 100, "Demo output should be substantial"
    
    def test_demo_output_contains_summary(self):
        """Test that the demo output contains a summary section."""
        result = subprocess.run(
            [sys.executable, str(DEMO_SCRIPT)],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        # Check for expected output markers
        assert "Summary" in result.stdout, "Output should contain 'Summary'"
        assert "completed successfully" in result.stdout, (
            "Output should indicate successful completion"
        )
    
    def test_summarizer_module_imports(self):
        """Test that the summarizer module can be imported."""
        # Add demo directory to path temporarily
        sys.path.insert(0, str(DEMO_DIR))
        try:
            from run_summary_demo import (
                read_sample_note,
                textrank_summarize,
                fallback_summarize
            )
            
            # Test reading the sample note
            content = read_sample_note()
            assert len(content) > 0, "Should read non-empty content"
            
            # Test summarization functions
            summary = textrank_summarize(content, num_sentences=3)
            assert len(summary) > 0, "TextRank summary should not be empty"
            
            fallback = fallback_summarize(content, num_sentences=3)
            assert len(fallback) > 0, "Fallback summary should not be empty"
            
        finally:
            sys.path.remove(str(DEMO_DIR))
    
    def test_summarizer_deterministic(self):
        """Test that the summarizer produces consistent results."""
        sys.path.insert(0, str(DEMO_DIR))
        try:
            from run_summary_demo import read_sample_note, textrank_summarize
            
            content = read_sample_note()
            
            # Run summarization twice
            summary1 = textrank_summarize(content, num_sentences=3)
            summary2 = textrank_summarize(content, num_sentences=3)
            
            # Results should be identical (deterministic)
            assert summary1 == summary2, (
                "Summarizer should produce deterministic results"
            )
            
        finally:
            sys.path.remove(str(DEMO_DIR))


def test_smoke():
    """
    Main smoke test entry point.
    
    This is a simple test that can be run standalone to verify
    the demo is working correctly.
    """
    # Run the demo script
    result = subprocess.run(
        [sys.executable, str(DEMO_SCRIPT)],
        capture_output=True,
        text=True,
        timeout=60
    )
    
    # Assert non-empty output and successful execution
    assert result.returncode == 0, f"Demo failed: {result.stderr}"
    assert len(result.stdout) > 0, "Demo should produce output"
    
    print("✅ Smoke test passed!")


if __name__ == "__main__":
    # Allow running this file directly
    test_smoke()
    sys.exit(0)

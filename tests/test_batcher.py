"""
Tests for the EntryBatcher functionality.
"""

import pytest
from pathlib import Path
from datetime import datetime
from arrowhead.batcher import EntryBatcher, Batch
from arrowhead.parser import JournalEntry

class TestEntryBatcher:
    """Test cases for EntryBatcher."""
    
    def test_batcher_initialization(self):
        """Test batcher initialization."""
        batcher = EntryBatcher(max_batch_size=10, max_tokens_per_batch=2000)
        assert batcher.max_batch_size == 10
        assert batcher.max_tokens_per_batch == 2000
    
    def test_create_batches_empty(self):
        """Test creating batches with no entries."""
        batcher = EntryBatcher()
        batches = batcher.create_batches([])
        assert len(batches) == 0
    
    def test_create_batches_small(self):
        """Test creating batches with few entries."""
        entries = [
            JournalEntry(
                file_path=Path("test1.md"),
                title="Test 1",
                content="Short content",
                date=datetime(2024, 1, 15),
                hashtags={"meeting"},
                frontmatter={},
                raw_content=""
            ),
            JournalEntry(
                file_path=Path("test2.md"),
                title="Test 2",
                content="Another short content",
                date=datetime(2024, 1, 16),
                hashtags={"meeting"},
                frontmatter={},
                raw_content=""
            )
        ]
        
        batcher = EntryBatcher(max_batch_size=5)
        batches = batcher.create_batches(entries)
        
        assert len(batches) == 1
        assert len(batches[0].entries) == 2
        assert batches[0].batch_id == 1
    
    def test_create_batches_large(self):
        """Test creating batches with many entries."""
        # Create 25 entries
        entries = []
        for i in range(25):
            entries.append(JournalEntry(
                file_path=Path(f"test{i}.md"),
                title=f"Test {i}",
                content=f"Content for test {i}",
                date=datetime(2024, 1, 15 + i),
                hashtags={"meeting"},
                frontmatter={},
                raw_content=""
            ))
        
        batcher = EntryBatcher(max_batch_size=10)
        batches = batcher.create_batches(entries)
        
        assert len(batches) == 3  # 25 entries / 10 per batch = 3 batches
        assert len(batches[0].entries) == 10
        assert len(batches[1].entries) == 10
        assert len(batches[2].entries) == 5
    
    def test_create_batches_by_date(self):
        """Test creating batches grouped by date."""
        entries = []
        for i in range(14):  # 2 weeks of entries
            entries.append(JournalEntry(
                file_path=Path(f"test{i}.md"),
                title=f"Test {i}",
                content=f"Content for test {i}",
                date=datetime(2024, 1, 15 + i),
                hashtags={"meeting"},
                frontmatter={},
                raw_content=""
            ))
        
        batcher = EntryBatcher()
        batches = batcher.create_batches_by_date(entries, days_per_batch=7)
        
        assert len(batches) == 2  # 2 weeks = 2 batches
        assert len(batches[0].entries) == 7  # First week
        assert len(batches[1].entries) == 7  # Second week
    
    def test_estimate_entry_tokens(self):
        """Test token estimation for entries."""
        batcher = EntryBatcher()
        
        entry = JournalEntry(
            file_path=Path("test.md"),
            title="Test Title",
            content="This is a test content with some words.",
            date=datetime(2024, 1, 15),
            hashtags={"meeting"},
            frontmatter={},
            raw_content=""
        )
        
        tokens = batcher._estimate_entry_tokens(entry)
        assert tokens > 0
        assert isinstance(tokens, int)
    
    def test_validate_batch(self):
        """Test batch validation."""
        batcher = EntryBatcher(max_batch_size=5, max_tokens_per_batch=1000)
        
        # Create a valid batch
        entries = [JournalEntry(
            file_path=Path("test.md"),
            title="Test",
            content="Short content",
            date=datetime(2024, 1, 15),
            hashtags={"meeting"},
            frontmatter={},
            raw_content=""
        ) for _ in range(3)]
        
        batch = Batch(
            entries=entries,
            batch_id=1,
            total_batches=1,
            estimated_tokens=500,
            date_range=(datetime(2024, 1, 15), datetime(2024, 1, 15))
        )
        
        assert batcher.validate_batch(batch) is True
    
    def test_optimize_batch_size(self):
        """Test dynamic batch size optimization."""
        entries = [JournalEntry(
            file_path=Path("test.md"),
            title="Test",
            content="Short content",
            date=datetime(2024, 1, 15),
            hashtags={"meeting"},
            frontmatter={},
            raw_content=""
        ) for _ in range(10)]
        
        batcher = EntryBatcher()
        optimal_size = batcher.optimize_batch_size(entries, target_tokens=3000)
        
        assert optimal_size > 0
        assert optimal_size <= 50  # Should be within bounds
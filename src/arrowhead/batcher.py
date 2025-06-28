"""
Entry batching logic for efficient LLM processing.
"""

import logging
from typing import List, Iterator
from dataclasses import dataclass
from pathlib import Path

from .parser import JournalEntry
from .utils import estimate_tokens

logger = logging.getLogger(__name__)

@dataclass
class Batch:
    """Represents a batch of journal entries for LLM processing."""
    entries: List[JournalEntry]
    batch_id: int
    total_batches: int
    estimated_tokens: int
    date_range: tuple  # (start_date, end_date)

class EntryBatcher:
    """
    Handles batching of journal entries for efficient LLM processing.
    """
    
    def __init__(self, max_batch_size: int = 20, max_tokens_per_batch: int = 4000):
        """
        Initialize the batcher.
        
        Args:
            max_batch_size: Maximum number of entries per batch
            max_tokens_per_batch: Maximum tokens per batch (for cost control)
        """
        self.max_batch_size = max_batch_size
        self.max_tokens_per_batch = max_tokens_per_batch
        
        logger.info(f"Initialized batcher: max_size={max_batch_size}, max_tokens={max_tokens_per_batch}")
    
    def create_batches(self, entries: List[JournalEntry]) -> List[Batch]:
        """
        Create batches from a list of entries.
        
        Args:
            entries: List of journal entries to batch
            
        Returns:
            List of Batch objects
        """
        if not entries:
            logger.info("No entries to batch")
            return []
        
        # Sort entries by date for consistent batching
        sorted_entries = sorted(entries, key=lambda e: e.date or datetime.min)
        
        batches = []
        current_batch = []
        current_tokens = 0
        batch_id = 1
        
        for entry in sorted_entries:
            # Estimate tokens for this entry
            entry_tokens = self._estimate_entry_tokens(entry)
            
            # Check if adding this entry would exceed limits
            if (len(current_batch) >= self.max_batch_size or 
                current_tokens + entry_tokens > self.max_tokens_per_batch):
                
                # Create batch from current entries
                if current_batch:
                    batch = self._create_batch(current_batch, batch_id, len(entries))
                    batches.append(batch)
                    batch_id += 1
                    current_batch = []
                    current_tokens = 0
            
            # Add entry to current batch
            current_batch.append(entry)
            current_tokens += entry_tokens
        
        # Create final batch if there are remaining entries
        if current_batch:
            batch = self._create_batch(current_batch, batch_id, len(entries))
            batches.append(batch)
        
        logger.info(f"Created {len(batches)} batches from {len(entries)} entries")
        return batches
    
    def create_batches_by_date(self, entries: List[JournalEntry], 
                              days_per_batch: int = 7) -> List[Batch]:
        """
        Create batches grouped by date ranges.
        
        Args:
            entries: List of journal entries to batch
            days_per_batch: Number of days per batch
            
        Returns:
            List of Batch objects grouped by date
        """
        if not entries:
            return []
        
        # Sort entries by date
        sorted_entries = sorted(entries, key=lambda e: e.date or datetime.min)
        
        batches = []
        batch_id = 1
        
        # Group entries by date ranges
        current_batch = []
        current_start_date = None
        
        for entry in sorted_entries:
            if not entry.date:
                # Entries without date go to a separate batch
                if current_batch and current_start_date:
                    batch = self._create_batch(current_batch, batch_id, len(entries))
                    batches.append(batch)
                    batch_id += 1
                    current_batch = []
                    current_start_date = None
                
                current_batch.append(entry)
                continue
            
            # Check if this entry starts a new date range
            if (current_start_date is None or 
                (entry.date - current_start_date).days >= days_per_batch):
                
                # Create batch from current entries
                if current_batch:
                    batch = self._create_batch(current_batch, batch_id, len(entries))
                    batches.append(batch)
                    batch_id += 1
                    current_batch = []
                
                current_start_date = entry.date
            
            current_batch.append(entry)
        
        # Create final batch
        if current_batch:
            batch = self._create_batch(current_batch, batch_id, len(entries))
            batches.append(batch)
        
        logger.info(f"Created {len(batches)} date-based batches from {len(entries)} entries")
        return batches
    
    def _create_batch(self, entries: List[JournalEntry], batch_id: int, 
                     total_entries: int) -> Batch:
        """
        Create a Batch object from entries.
        
        Args:
            entries: List of entries for this batch
            batch_id: Batch number
            total_entries: Total number of entries being processed
            
        Returns:
            Batch object
        """
        # Calculate total tokens for this batch
        total_tokens = sum(self._estimate_entry_tokens(entry) for entry in entries)
        
        # Determine date range
        dates = [entry.date for entry in entries if entry.date]
        if dates:
            start_date = min(dates)
            end_date = max(dates)
        else:
            start_date = end_date = None
        
        return Batch(
            entries=entries,
            batch_id=batch_id,
            total_batches=total_entries // self.max_batch_size + 1,
            estimated_tokens=total_tokens,
            date_range=(start_date, end_date)
        )
    
    def _estimate_entry_tokens(self, entry: JournalEntry) -> int:
        """
        Estimate token count for a journal entry.
        
        Args:
            entry: Journal entry to estimate
            
        Returns:
            Estimated token count
        """
        # Combine title and content for token estimation
        text = f"{entry.title}\n{entry.content}"
        
        # Add some overhead for formatting and metadata
        base_tokens = estimate_tokens(text)
        overhead = 50  # Tokens for formatting, metadata, etc.
        
        return base_tokens + overhead
    
    def get_batch_summary(self, batch: Batch) -> str:
        """
        Get a summary of batch contents for logging/debugging.
        
        Args:
            batch: Batch to summarize
            
        Returns:
            Summary string
        """
        start_date, end_date = batch.date_range
        
        summary = f"Batch {batch.batch_id}/{batch.total_batches}: "
        summary += f"{len(batch.entries)} entries, "
        summary += f"~{batch.estimated_tokens} tokens"
        
        if start_date and end_date:
            if start_date == end_date:
                summary += f", date: {start_date.strftime('%Y-%m-%d')}"
            else:
                summary += f", dates: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
        
        return summary
    
    def validate_batch(self, batch: Batch) -> bool:
        """
        Validate that a batch is within limits.
        
        Args:
            batch: Batch to validate
            
        Returns:
            True if batch is valid
        """
        if len(batch.entries) > self.max_batch_size:
            logger.warning(f"Batch {batch.batch_id} exceeds size limit: {len(batch.entries)} > {self.max_batch_size}")
            return False
        
        if batch.estimated_tokens > self.max_tokens_per_batch:
            logger.warning(f"Batch {batch.batch_id} exceeds token limit: {batch.estimated_tokens} > {self.max_tokens_per_batch}")
            return False
        
        return True
    
    def optimize_batch_size(self, entries: List[JournalEntry], 
                           target_tokens: int = 3000) -> int:
        """
        Dynamically optimize batch size based on entry sizes.
        
        Args:
            entries: List of entries to analyze
            target_tokens: Target tokens per batch
            
        Returns:
            Optimized batch size
        """
        if not entries:
            return self.max_batch_size
        
        # Calculate average tokens per entry
        total_tokens = sum(self._estimate_entry_tokens(entry) for entry in entries)
        avg_tokens = total_tokens / len(entries)
        
        # Calculate optimal batch size
        optimal_size = max(1, int(target_tokens / avg_tokens))
        
        # Clamp to reasonable bounds
        optimal_size = max(5, min(optimal_size, 50))
        
        logger.info(f"Optimized batch size: {optimal_size} (avg tokens per entry: {avg_tokens:.1f})")
        return optimal_size
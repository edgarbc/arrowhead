"""
Summary aggregation and note writing functionality.
"""

import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import json

logger = logging.getLogger(__name__)

@dataclass
class SummaryMetadata:
    """Metadata for a generated summary."""
    title: str
    date: datetime
    model: str
    hashtag: str
    entries_processed: int
    generation_time: datetime
    batch_count: int
    total_tokens: Optional[int] = None

class SummaryWriter:
    """
    Handles writing consolidated summaries to files.
    """
    
    def __init__(self, output_dir: Path):
        """
        Initialize the summary writer.
        
        Args:
            output_dir: Directory to write summary files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Initialized summary writer with output dir: {output_dir}")
    
    def write_summary(self, batch_summaries: List[str], hashtag: str, 
                     start_date: datetime, end_date: datetime, 
                     model: str, entries_processed: int = 0,
                     batch_count: int = 0, total_tokens: Optional[int] = None) -> Path:
        """
        Write consolidated summary to file.
        
        Args:
            batch_summaries: List of summaries from each batch
            hashtag: Target hashtag
            start_date: Start of date range
            end_date: End of date range
            model: LLM model used
            entries_processed: Number of entries processed
            batch_count: Number of batches processed
            total_tokens: Total tokens used (if available)
            
        Returns:
            Path to the written summary file
        """
        # Generate filename
        filename = self._generate_filename(hashtag, start_date, end_date)
        file_path = self.output_dir / filename
        
        # Create metadata
        metadata = SummaryMetadata(
            title=f"Week Summary - #{hashtag} ({start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')})",
            date=datetime.now(),
            model=model,
            hashtag=hashtag,
            entries_processed=entries_processed,
            generation_time=datetime.now(),
            batch_count=batch_count,
            total_tokens=total_tokens
        )
        
        # Generate content
        content = self._generate_summary_content(batch_summaries, metadata)
        
        # Write to file
        try:
            file_path.write_text(content, encoding='utf-8')
            logger.info(f"Summary written to: {file_path}")
            return file_path
        except Exception as e:
            logger.error(f"Failed to write summary: {e}")
            raise
    
    def _generate_filename(self, hashtag: str, start_date: datetime, 
                          end_date: datetime) -> str:
        """
        Generate filename for summary.
        
        Args:
            hashtag: Target hashtag
            start_date: Start of date range
            end_date: End of date range
            
        Returns:
            Generated filename
        """
        # Format: Week-YYYY-MM-DD-hashtag.md
        return f"Week-{start_date.strftime('%Y-%m-%d')}-{hashtag}.md"
    
    def _generate_summary_content(self, batch_summaries: List[str], 
                                 metadata: SummaryMetadata) -> str:
        """
        Generate the complete summary content.
        
        Args:
            batch_summaries: List of batch summaries
            metadata: Summary metadata
            
        Returns:
            Complete summary content
        """
        # Create frontmatter
        frontmatter = self._create_frontmatter(metadata)
        
        # Merge batch summaries
        merged_summary = self._merge_batch_summaries(batch_summaries)
        
        # Create final content
        content = f"""---
{frontmatter}

# {metadata.title}

{merged_summary}

## Summary Statistics
- **Total Entries**: {metadata.entries_processed}
- **Batches Processed**: {metadata.batch_count}
- **Model Used**: {metadata.model}
- **Generation Time**: {metadata.generation_time.strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        if metadata.total_tokens:
            content += f"- **Total Tokens**: {metadata.total_tokens}\n"
        
        return content
    
    def _create_frontmatter(self, metadata: SummaryMetadata) -> str:
        """
        Create YAML frontmatter for the summary.
        
        Args:
            metadata: Summary metadata
            
        Returns:
            YAML frontmatter string
        """
        frontmatter_data = {
            'title': metadata.title,
            'date': metadata.date.strftime('%Y-%m-%d'),
            'model': metadata.model,
            'hashtag': metadata.hashtag,
            'entries_processed': metadata.entries_processed,
            'generation_time': metadata.generation_time.isoformat(),
            'batch_count': metadata.batch_count
        }
        
        if metadata.total_tokens:
            frontmatter_data['total_tokens'] = metadata.total_tokens
        
        # Convert to YAML
        try:
            import yaml
            return yaml.dump(frontmatter_data, default_flow_style=False, sort_keys=False)
        except ImportError:
            # Fallback to simple format if PyYAML not available
            lines = []
            for key, value in frontmatter_data.items():
                lines.append(f"{key}: {value}")
            return "\n".join(lines)
    
    def _merge_batch_summaries(self, batch_summaries: List[str]) -> str:
        """
        Merge multiple batch summaries into one coherent summary.
        
        Args:
            batch_summaries: List of batch summaries
            
        Returns:
            Merged summary content
        """
        if not batch_summaries:
            return "No content to summarize."
        
        if len(batch_summaries) == 1:
            return batch_summaries[0]
        
        # Simple merge: combine all summaries
        merged = []
        for i, summary in enumerate(batch_summaries, 1):
            if summary.strip():
                merged.append(f"### Batch {i}\n{summary.strip()}\n")
        
        return "\n".join(merged)
    
    def list_summaries(self) -> List[Path]:
        """
        List all summary files in the output directory.
        
        Returns:
            List of summary file paths
        """
        return sorted(self.output_dir.glob("*.md"))
    
    def get_summary_info(self, summary_path: Path) -> Dict[str, Any]:
        """
        Get information about a summary file.
        
        Args:
            summary_path: Path to summary file
            
        Returns:
            Dictionary with summary information
        """
        try:
            content = summary_path.read_text(encoding='utf-8')
            
            # Parse frontmatter
            if content.startswith('---'):
                import yaml
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    frontmatter = yaml.safe_load(parts[1]) or {}
                else:
                    frontmatter = {}
            else:
                frontmatter = {}
            
            return {
                'path': summary_path,
                'size': summary_path.stat().st_size,
                'modified': datetime.fromtimestamp(summary_path.stat().st_mtime),
                'frontmatter': frontmatter
            }
            
        except Exception as e:
            logger.warning(f"Failed to read summary info for {summary_path}: {e}")
            return {'path': summary_path, 'error': str(e)}
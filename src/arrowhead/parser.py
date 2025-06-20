"""
Markdown parsing and hashtag filtering functionality.
"""

from pathlib import Path
from typing import List, Optional, Set
from dataclasses import dataclass
from datetime import datetime
import re
import logging
from pendulum import DateTime, parse as parse_date

logger = logging.getLogger(__name__)

@dataclass
class JournalEntry:
    """Represents a parsed journal entry."""
    file_path: Path
    title: str
    content: str
    date: Optional[DateTime]
    hashtags: Set[str]
    frontmatter: dict
    raw_content: str

class EntryParser:
    """
    Parses markdown files and filters entries by hashtag and date range.
    """
    
    def __init__(self, target_hashtag: str, start_date: Optional[DateTime] = None, 
                 end_date: Optional[DateTime] = None):
        """
        Initialize the parser.
        
        Args:
            target_hashtag: Hashtag to filter for (e.g., "#meeting", "meeting")
            start_date: Start of date range (inclusive)
            end_date: End of date range (inclusive)
        """
        # Normalize hashtag (remove # if present, then add it back)
        self.target_hashtag = target_hashtag.lstrip('#')
        self.start_date = start_date
        self.end_date = end_date
        
        # Compile regex patterns for efficiency
        self.hashtag_pattern = re.compile(r'#(\w+)')
        self.date_patterns = [
            # YYYY-MM-DD
            re.compile(r'(\d{4}-\d{2}-\d{2})'),
            # MM/DD/YYYY
            re.compile(r'(\d{1,2}/\d{1,2}/\d{4})'),
            # DD-MM-YYYY
            re.compile(r'(\d{1,2}-\d{1,2}-\d{4})'),
        ]
        
        logger.info(f"Initialized parser for hashtag #{self.target_hashtag}")
        if start_date and end_date:
            logger.info(f"Date range: {start_date.format('YYYY-MM-DD')} to {end_date.format('YYYY-MM-DD')}")
    
    def parse_files(self, file_paths: List[Path]) -> List[JournalEntry]:
        """
        Parse multiple markdown files and filter by criteria.
        
        Args:
            file_paths: List of markdown file paths to parse
            
        Returns:
            List of JournalEntry objects that match the criteria
        """
        entries = []
        
        for file_path in file_paths:
            try:
                entry = self.parse_file(file_path)
                if entry and self._matches_criteria(entry):
                    entries.append(entry)
                    logger.debug(f"Matched entry: {file_path}")
                else:
                    logger.debug(f"Skipped entry: {file_path}")
            except Exception as e:
                logger.warning(f"Failed to parse {file_path}: {e}")
                continue
        
        logger.info(f"Parsed {len(entries)} matching entries out of {len(file_paths)} files")
        return entries
    
    def parse_file(self, file_path: Path) -> Optional[JournalEntry]:
        """
        Parse a single markdown file.
        
        Args:
            file_path: Path to the markdown file
            
        Returns:
            JournalEntry object or None if parsing fails
        """
        try:
            content = file_path.read_text(encoding='utf-8')
        except Exception as e:
            logger.warning(f"Failed to read {file_path}: {e}")
            return None
        
        # Parse frontmatter if present
        frontmatter, content_without_frontmatter = self._parse_frontmatter(content)
        
        # Extract title from filename or frontmatter
        title = self._extract_title(file_path, frontmatter, content_without_frontmatter)
        
        # Extract hashtags
        hashtags = self._extract_hashtags(content_without_frontmatter)
        
        # Extract date
        date = self._extract_date(file_path, frontmatter, content_without_frontmatter)
        
        return JournalEntry(
            file_path=file_path,
            title=title,
            content=content_without_frontmatter.strip(),
            date=date,
            hashtags=hashtags,
            frontmatter=frontmatter,
            raw_content=content
        )
    
    def _parse_frontmatter(self, content: str) -> tuple[dict, str]:
        """
        Parse YAML frontmatter from markdown content.
        
        Args:
            content: Raw markdown content
            
        Returns:
            Tuple of (frontmatter_dict, content_without_frontmatter)
        """
        frontmatter = {}
        content_without_frontmatter = content
        
        # Check for frontmatter (YAML between --- markers)
        if content.startswith('---'):
            try:
                import yaml
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    frontmatter_text = parts[1].strip()
                    if frontmatter_text:
                        frontmatter = yaml.safe_load(frontmatter_text) or {}
                    content_without_frontmatter = parts[2].strip()
            except ImportError:
                logger.warning("PyYAML not available, skipping frontmatter parsing")
            except Exception as e:
                logger.warning(f"Failed to parse frontmatter: {e}")
        
        return frontmatter, content_without_frontmatter
    
    def _extract_title(self, file_path: Path, frontmatter: dict, content: str) -> str:
        """
        Extract title from filename, frontmatter, or first heading.
        
        Args:
            file_path: Path to the file
            frontmatter: Parsed frontmatter
            content: Content without frontmatter
            
        Returns:
            Extracted title
        """
        # Try frontmatter first
        if 'title' in frontmatter:
            return str(frontmatter['title'])
        
        # Try first heading
        heading_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        if heading_match:
            return heading_match.group(1).strip()
        
        # Fall back to filename without extension
        return file_path.stem
    
    def _extract_hashtags(self, content: str) -> Set[str]:
        """
        Extract all hashtags from content.
        
        Args:
            content: Markdown content
            
        Returns:
            Set of hashtags (without #)
        """
        hashtags = set()
        matches = self.hashtag_pattern.findall(content)
        hashtags.update(matches)
        return hashtags
    
    def _extract_date(self, file_path: Path, frontmatter: dict, content: str) -> Optional[DateTime]:
        """
        Extract date from frontmatter, filename, or content.
        
        Args:
            file_path: Path to the file
            frontmatter: Parsed frontmatter
            content: Content without frontmatter
            
        Returns:
            Parsed date or None
        """
        # Try frontmatter first
        if 'date' in frontmatter:
            try:
                return parse_date(str(frontmatter['date']))
            except Exception:
                pass
        
        # Try filename patterns (common journal naming)
        filename = file_path.stem
        for pattern in self.date_patterns:
            match = pattern.search(filename)
            if match:
                try:
                    return parse_date(match.group(1))
                except Exception:
                    continue
        
        # Try content for date patterns
        for pattern in self.date_patterns:
            match = pattern.search(content)
            if match:
                try:
                    return parse_date(match.group(1))
                except Exception:
                    continue
        
        return None
    
    def _matches_criteria(self, entry: JournalEntry) -> bool:
        """
        Check if an entry matches the filtering criteria.
        
        Args:
            entry: JournalEntry to check
            
        Returns:
            True if entry matches criteria
        """
        # Check hashtag
        if self.target_hashtag not in entry.hashtags:
            return False
        
        # Check date range if specified
        if self.start_date and self.end_date and entry.date:
            if not (self.start_date <= entry.date <= self.end_date):
                return False
        
        return True
    
    def get_entries_by_date(self, entries: List[JournalEntry]) -> dict:
        """
        Group entries by date for summary generation.
        
        Args:
            entries: List of JournalEntry objects
            
        Returns:
            Dictionary with date as key and list of entries as value
        """
        grouped = {}
        
        for entry in entries:
            if entry.date:
                date_key = entry.date.format('YYYY-MM-DD')
                if date_key not in grouped:
                    grouped[date_key] = []
                grouped[date_key].append(entry)
            else:
                # Entries without date go to 'unknown' group
                if 'unknown' not in grouped:
                    grouped['unknown'] = []
                grouped['unknown'].append(entry)
        
        return grouped
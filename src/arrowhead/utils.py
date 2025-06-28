"""
Helper functions for date parsing, logging, and other utilities.
"""

import logging
import sys
from pathlib import Path
from typing import Tuple, Optional
from datetime import datetime, timedelta
from pendulum import DateTime, now

logger = logging.getLogger(__name__)

def setup_logging(verbose: bool = False, log_file: Optional[Path] = None):
    """
    Setup logging configuration.
    
    Args:
        verbose: Enable verbose logging
        log_file: Optional log file path
    """
    level = logging.DEBUG if verbose else logging.INFO
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Setup console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    
    # Setup file handler if specified
    handlers = [console_handler]
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        handlers.append(file_handler)
    
    # Configure root logger
    logging.basicConfig(
        level=level,
        handlers=handlers,
        force=True
    )
    
    logger.info(f"Logging setup complete (level: {logging.getLevelName(level)})")

def parse_date_range(start_date: Optional[str], end_date: Optional[str]) -> Tuple[DateTime, DateTime]:
    """
    Parse date range from strings.
    
    Args:
        start_date: Start date string (YYYY-MM-DD) or None for last Monday
        end_date: End date string (YYYY-MM-DD) or None for last Sunday
        
    Returns:
        Tuple of (start_date, end_date) as DateTime objects
    """
    if start_date and end_date:
        # Parse provided dates
        try:
            start = DateTime.fromisoformat(start_date)
            end = DateTime.fromisoformat(end_date)
            return start, end
        except Exception as e:
            logger.warning(f"Failed to parse provided dates: {e}")
    
    # Default to last week (Monday to Sunday)
    today = now()
    
    if not start_date:
        # Last Monday
        start = today.previous(1)  # Monday is day 1
        start = start.start_of('week')
    else:
        start = DateTime.fromisoformat(start_date)
    
    if not end_date:
        # Last Sunday
        end = start.end_of('week')
    else:
        end = DateTime.fromisoformat(end_date)
    
    logger.info(f"Date range: {start.format('YYYY-MM-DD')} to {end.format('YYYY-MM-DD')}")
    return start, end

def format_duration(seconds: float) -> str:
    """
    Format duration in seconds to human-readable string.
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted duration string
    """
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h"

def safe_filename(text: str) -> str:
    """
    Convert text to a safe filename.
    
    Args:
        text: Text to convert
        
    Returns:
        Safe filename string
    """
    import re
    # Remove or replace unsafe characters
    safe = re.sub(r'[<>:"/\\|?*]', '_', text)
    # Remove leading/trailing spaces and dots
    safe = safe.strip(' .')
    # Limit length
    if len(safe) > 100:
        safe = safe[:100]
    return safe

def get_file_size_mb(file_path: Path) -> float:
    """
    Get file size in megabytes.
    
    Args:
        file_path: Path to file
        
    Returns:
        File size in MB
    """
    try:
        return file_path.stat().st_size / (1024 * 1024)
    except Exception:
        return 0.0

def validate_vault_path(vault_path: Path) -> bool:
    """
    Validate that a path is a proper Obsidian vault.
    
    Args:
        vault_path: Path to validate
        
    Returns:
        True if valid Obsidian vault
    """
    if not vault_path.exists():
        return False
    
    if not vault_path.is_dir():
        return False
    
    # Check for .obsidian directory (indicates Obsidian vault)
    obsidian_dir = vault_path / '.obsidian'
    if not obsidian_dir.exists():
        logger.warning(f"No .obsidian directory found in {vault_path}")
        return False
    
    # Check for markdown files
    md_files = list(vault_path.rglob("*.md"))
    if not md_files:
        logger.warning(f"No markdown files found in {vault_path}")
        return False
    
    return True

def estimate_tokens(text: str) -> int:
    """
    Rough estimate of token count for text.
    
    Args:
        text: Text to estimate
        
    Returns:
        Estimated token count
    """
    # Rough estimate: 1 token ≈ 4 characters for English text
    return len(text) // 4

def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """
    Truncate text to maximum length.
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated
        
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix
"""
Vault scanning functionality for discovering markdown files in Obsidian vaults.
"""

from pathlib import Path
from typing import List, Set
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ScanResult:
    """Result of a vault scan operation."""
    vault_path: Path
    markdown_files: List[Path]
    total_files: int
    excluded_dirs: Set[str]
    scan_time_ms: float

class VaultScanner:
    """
    Scans an Obsidian vault for markdown files.
    
    Handles common Obsidian directory exclusions and provides
    configurable filtering options.
    """
    
    # Default directories to exclude from scanning
    DEFAULT_EXCLUDE_DIRS = {
        '.obsidian',      # Obsidian settings
        '.git',           # Git repository
        '__pycache__',    # Python cache
        '.venv',          # Virtual environment
        'node_modules',   # Node.js dependencies
        '.vscode',        # VS Code settings
        '.idea',          # PyCharm/IntelliJ settings
        'Summaries',      # Output directory for summaries
        'Attachments',    # Obsidian attachments
        'Templates',      # Obsidian templates
    }
    
    # Default file patterns to exclude
    DEFAULT_EXCLUDE_PATTERNS = {
        '*.tmp',
        '*.bak',
        '*.swp',
        '*.swo',
        '~*',
        '.#*',
    }
    
    def __init__(self, vault_path: Path, exclude_dirs: Set[str] = None):
        """
        Initialize the vault scanner.
        
        Args:
            vault_path: Path to the Obsidian vault directory
            exclude_dirs: Additional directories to exclude (merged with defaults)
        """
        self.vault_path = Path(vault_path).resolve()
        
        if not self.vault_path.exists():
            raise ValueError(f"Vault path does not exist: {vault_path}")
        
        if not self.vault_path.is_dir():
            raise ValueError(f"Vault path is not a directory: {vault_path}")
        
        # Merge default exclusions with user-provided ones
        self.exclude_dirs = self.DEFAULT_EXCLUDE_DIRS.copy()
        if exclude_dirs:
            self.exclude_dirs.update(exclude_dirs)
        
        logger.info(f"Initialized scanner for vault: {self.vault_path}")
        logger.debug(f"Excluding directories: {sorted(self.exclude_dirs)}")
    
    def scan(self, recursive: bool = True) -> ScanResult:
        """
        Scan the vault for markdown files.
        
        Args:
            recursive: Whether to scan subdirectories recursively
            
        Returns:
            ScanResult containing scan information and discovered files
        """
        import time
        start_time = time.time()
        
        markdown_files = []
        total_files = 0
        
        if recursive:
            # Use rglob for recursive scanning
            file_iterator = self.vault_path.rglob("*.md")
        else:
            # Use glob for non-recursive scanning
            file_iterator = self.vault_path.glob("*.md")
        
        for file_path in file_iterator:
            total_files += 1
            
            # Skip files in excluded directories
            if self._should_exclude_file(file_path):
                logger.debug(f"Excluding file: {file_path}")
                continue
            
            # Skip files matching exclude patterns
            if self._matches_exclude_pattern(file_path):
                logger.debug(f"Excluding file (pattern match): {file_path}")
                continue
            
            markdown_files.append(file_path)
            logger.debug(f"Found markdown file: {file_path}")
        
        scan_time_ms = (time.time() - start_time) * 1000
        
        result = ScanResult(
            vault_path=self.vault_path,
            markdown_files=sorted(markdown_files),
            total_files=total_files,
            excluded_dirs=self.exclude_dirs,
            scan_time_ms=scan_time_ms
        )
        
        logger.info(
            f"Scan completed: {len(markdown_files)} markdown files found "
            f"out of {total_files} total files in {scan_time_ms:.1f}ms"
        )
        
        return result
    
    def _should_exclude_file(self, file_path: Path) -> bool:
        """
        Check if a file should be excluded based on directory exclusions.
        
        Args:
            file_path: Path to the file to check
            
        Returns:
            True if the file should be excluded
        """
        # Check if any part of the path matches excluded directories
        for part in file_path.parts:
            if part in self.exclude_dirs:
                return True
        return False
    
    def _matches_exclude_pattern(self, file_path: Path) -> bool:
        """
        Check if a file matches any exclude patterns.
        
        Args:
            file_path: Path to the file to check
            
        Returns:
            True if the file matches an exclude pattern
        """
        filename = file_path.name
        
        for pattern in self.DEFAULT_EXCLUDE_PATTERNS:
            if filename.startswith(pattern.replace('*', '')):
                return True
            if filename.endswith(pattern.replace('*', '')):
                return True
        
        return False
    
    def get_vault_info(self) -> dict:
        """
        Get basic information about the vault.
        
        Returns:
            Dictionary containing vault information
        """
        return {
            'vault_path': str(self.vault_path),
            'vault_name': self.vault_path.name,
            'exists': self.vault_path.exists(),
            'is_dir': self.vault_path.is_dir(),
            'exclude_dirs': sorted(self.exclude_dirs),
        }
    
    def validate_vault(self) -> bool:
        """
        Validate that the vault path is a proper Obsidian vault.
        
        Returns:
            True if the vault appears to be valid
        """
        # Check if .obsidian directory exists (indicates Obsidian vault)
        obsidian_dir = self.vault_path / '.obsidian'
        if not obsidian_dir.exists():
            logger.warning(f"No .obsidian directory found in {self.vault_path}")
            logger.warning("This might not be an Obsidian vault")
            return False
        
        # Check if there are any markdown files
        scan_result = self.scan()
        if not scan_result.markdown_files:
            logger.warning(f"No markdown files found in {self.vault_path}")
            return False
        
        logger.info(f"Vault validation passed: {len(scan_result.markdown_files)} markdown files found")
        return True
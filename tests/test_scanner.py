"""
Tests for the VaultScanner functionality.
"""

import pytest
from pathlib import Path
from arrowhead.scanner import VaultScanner, ScanResult

class TestVaultScanner:
    """Test cases for VaultScanner."""
    
    def test_scanner_initialization(self, tmp_path):
        """Test scanner initialization with valid path."""
        scanner = VaultScanner(tmp_path)
        assert scanner.vault_path == tmp_path.resolve()
        assert '.obsidian' in scanner.exclude_dirs
        assert '.git' in scanner.exclude_dirs
    
    def test_scanner_invalid_path(self):
        """Test scanner initialization with invalid path."""
        with pytest.raises(ValueError, match="does not exist"):
            VaultScanner(Path("/nonexistent/path"))
    
    def test_scanner_with_additional_exclusions(self, tmp_path):
        """Test scanner with additional directory exclusions."""
        custom_exclusions = {'custom_dir', 'another_dir'}
        scanner = VaultScanner(tmp_path, exclude_dirs=custom_exclusions)
        
        assert 'custom_dir' in scanner.exclude_dirs
        assert 'another_dir' in scanner.exclude_dirs
        assert '.obsidian' in scanner.exclude_dirs  # Default exclusions still present
    
    def test_scan_empty_vault(self, tmp_path):
        """Test scanning an empty vault."""
        scanner = VaultScanner(tmp_path)
        result = scanner.scan()
        
        assert isinstance(result, ScanResult)
        assert result.vault_path == tmp_path.resolve()
        assert len(result.markdown_files) == 0
        assert result.total_files == 0
    
    def test_scan_with_markdown_files(self, tmp_path):
        """Test scanning a vault with markdown files."""
        # Create some test markdown files
        (tmp_path / "note1.md").write_text("# Test Note 1")
        (tmp_path / "note2.md").write_text("# Test Note 2")
        (tmp_path / "subdir" / "note3.md").write_text("# Test Note 3")
        
        scanner = VaultScanner(tmp_path)
        result = scanner.scan()
        
        assert len(result.markdown_files) == 3
        assert any("note1.md" in str(f) for f in result.markdown_files)
        assert any("note2.md" in str(f) for f in result.markdown_files)
        assert any("note3.md" in str(f) for f in result.markdown_files)
    
    def test_scan_excludes_obsidian_dirs(self, tmp_path):
        """Test that scanner excludes Obsidian-specific directories."""
        # Create markdown files in excluded directories
        (tmp_path / ".obsidian" / "note.md").write_text("# Obsidian Note")
        (tmp_path / ".git" / "note.md").write_text("# Git Note")
        (tmp_path / "valid_note.md").write_text("# Valid Note")
        
        scanner = VaultScanner(tmp_path)
        result = scanner.scan()
        
        # Should only find the valid note
        assert len(result.markdown_files) == 1
        assert "valid_note.md" in str(result.markdown_files[0])
    
    def test_scan_non_recursive(self, tmp_path):
        """Test non-recursive scanning."""
        # Create files at root and in subdirectory
        (tmp_path / "root_note.md").write_text("# Root Note")
        (tmp_path / "subdir" / "sub_note.md").write_text("# Sub Note")
        
        scanner = VaultScanner(tmp_path)
        result = scanner.scan(recursive=False)
        
        # Should only find the root note
        assert len(result.markdown_files) == 1
        assert "root_note.md" in str(result.markdown_files[0])
    
    def test_get_vault_info(self, tmp_path):
        """Test getting vault information."""
        scanner = VaultScanner(tmp_path)
        info = scanner.get_vault_info()
        
        assert info['vault_path'] == str(tmp_path.resolve())
        assert info['vault_name'] == tmp_path.name
        assert info['exists'] is True
        assert info['is_dir'] is True
        assert '.obsidian' in info['exclude_dirs']
    
    def test_validate_vault(self, tmp_path):
        """Test vault validation."""
        scanner = VaultScanner(tmp_path)
        
        # Should fail without .obsidian directory
        assert scanner.validate_vault() is False
        
        # Create .obsidian directory and a markdown file
        (tmp_path / ".obsidian").mkdir()
        (tmp_path / "test.md").write_text("# Test")
        
        # Should pass now
        assert scanner.validate_vault() is True
"""Utility functions for file and directory management."""
import os
from pathlib import Path
from datetime import datetime
from ..core.config import get_settings


def ensure_output_dir(subdir: str = "") -> Path:
    """Ensure output directory exists and return path.
    
    Args:
        subdir: Optional subdirectory
    
    Returns:
        Path object for output directory
    """
    settings = get_settings()
    base_path = Path(settings.OUTPUT_BASE_PATH)
    
    if subdir:
        path = base_path / subdir
    else:
        path = base_path
    
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_mailing_pack_dir(prospect_id: str) -> Path:
    """Get mailing pack directory for a prospect.
    
    Args:
        prospect_id: UUID of prospect
    
    Returns:
        Path object for mailing pack directory
    """
    settings = get_settings()
    path = Path(settings.MAILING_PACKS_PATH) / str(prospect_id)
    path.mkdir(parents=True, exist_ok=True)
    return path


def generate_filename(prefix: str, extension: str = "png") -> str:
    """Generate unique filename with timestamp.
    
    Args:
        prefix: Filename prefix
        extension: File extension
    
    Returns:
        Generated filename
    """
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    return f"{prefix}_{timestamp}.{extension}"


def save_file(content: bytes, output_path: Path, filename: str) -> Path:
    """Save file to output directory.
    
    Args:
        content: File content
        output_path: Output directory path
        filename: Filename
    
    Returns:
        Full path to saved file
    """
    output_path.mkdir(parents=True, exist_ok=True)
    filepath = output_path / filename
    
    with open(filepath, "wb") as f:
        f.write(content)
    
    return filepath

"""
Export utilities for figure meshes.

This module provides convenience functions for exporting figures
and querying supported formats.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from figure_generator.backends import create_backend, get_available_backends

if TYPE_CHECKING:
    from figure_generator.generator import GeneratedFigure


def get_supported_formats(backend: str | None = None) -> list[str]:
    """
    Get list of supported export formats.

    Args:
        backend: Optional backend name. If None, uses default backend.

    Returns:
        List of supported format extensions (e.g., ["glb", "obj", "stl"])
    """
    b = create_backend(backend)
    return b.get_supported_formats()


def export_figure(
    figure: GeneratedFigure,
    filepath: str,
    file_format: str | None = None,
    backend: str | None = None,
) -> Path:
    """
    Export a generated figure to file.

    This is a convenience function that handles backend creation
    and format inference.

    Args:
        figure: GeneratedFigure to export
        filepath: Output file path
        file_format: Optional format override. If None, inferred from extension.
        backend: Optional backend name. If None, uses default.

    Returns:
        Path to the exported file

    Raises:
        ValueError: If format is not supported by the backend
    """
    b = create_backend(backend)

    # Infer format from extension if not specified
    if file_format is None:
        file_format = Path(filepath).suffix.lstrip(".")

    supported = b.get_supported_formats()
    if file_format.lower() not in [f.lower() for f in supported]:
        raise ValueError(
            f"Format '{file_format}' not supported by {b.name} backend. "
            f"Supported formats: {supported}"
        )

    b.export(figure.meshes, filepath, file_format)
    return Path(filepath)


def get_format_info() -> dict:
    """
    Get information about supported formats per backend.

    Returns:
        Dict mapping backend names to their supported formats
    """
    info = {}
    for backend_name in get_available_backends():
        try:
            b = create_backend(backend_name)
            info[backend_name] = b.get_supported_formats()
        except ImportError:
            pass
    return info

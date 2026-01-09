"""Tests for figure_generator.exporters module."""

import tempfile
from pathlib import Path

import pytest

from figure_generator.exporters import (
    export_figure,
    get_format_info,
    get_supported_formats,
)
from figure_generator.generator import FigureGenerator


class TestGetSupportedFormats:
    """Tests for get_supported_formats function."""

    def test_returns_list(self):
        """Test that function returns a list."""
        formats = get_supported_formats()
        assert isinstance(formats, list)
        assert len(formats) > 0

    def test_contains_common_formats(self):
        """Test that common formats are supported."""
        formats = get_supported_formats()
        # At least glb and obj should be supported with trimesh
        assert "glb" in formats or "obj" in formats

    def test_with_specific_backend(self):
        """Test getting formats for specific backend."""
        formats = get_supported_formats(backend="trimesh")
        assert isinstance(formats, list)
        assert "glb" in formats
        assert "obj" in formats
        assert "stl" in formats


class TestExportFigure:
    """Tests for export_figure function."""

    @pytest.fixture
    def figure(self):
        """Generate a figure for testing."""
        generator = FigureGenerator()
        return generator.generate("female_adult", arm_angle=45)

    def test_export_glb(self, figure):
        """Test exporting figure to GLB format."""
        with tempfile.NamedTemporaryFile(suffix=".glb", delete=False) as f:
            temp_path = Path(f.name)

        try:
            result = export_figure(figure, str(temp_path))
            assert result == temp_path
            assert temp_path.exists()
            assert temp_path.stat().st_size > 0
        finally:
            temp_path.unlink()

    def test_export_obj(self, figure):
        """Test exporting figure to OBJ format."""
        with tempfile.NamedTemporaryFile(suffix=".obj", delete=False) as f:
            temp_path = Path(f.name)

        try:
            result = export_figure(figure, str(temp_path))
            assert result == temp_path
            assert temp_path.exists()
        finally:
            temp_path.unlink()

    def test_export_stl(self, figure):
        """Test exporting figure to STL format."""
        with tempfile.NamedTemporaryFile(suffix=".stl", delete=False) as f:
            temp_path = Path(f.name)

        try:
            result = export_figure(figure, str(temp_path))
            assert result == temp_path
            assert temp_path.exists()
        finally:
            temp_path.unlink()

    def test_export_with_explicit_format(self, figure):
        """Test exporting with explicit format override."""
        with tempfile.NamedTemporaryFile(suffix=".bin", delete=False) as f:
            temp_path = Path(f.name)

        try:
            # Export as GLB even though extension is .bin
            result = export_figure(figure, str(temp_path), file_format="glb")
            assert result == temp_path
            assert temp_path.exists()
        finally:
            temp_path.unlink()

    def test_export_with_specific_backend(self, figure):
        """Test exporting with specific backend."""
        with tempfile.NamedTemporaryFile(suffix=".glb", delete=False) as f:
            temp_path = Path(f.name)

        try:
            result = export_figure(figure, str(temp_path), backend="trimesh")
            assert result == temp_path
            assert temp_path.exists()
        finally:
            temp_path.unlink()

    def test_export_unsupported_format(self, figure):
        """Test that unsupported format raises ValueError."""
        with tempfile.NamedTemporaryFile(suffix=".xyz", delete=False) as f:
            temp_path = Path(f.name)

        try:
            with pytest.raises(ValueError, match="not supported"):
                export_figure(figure, str(temp_path))
        finally:
            temp_path.unlink()

    def test_export_unsupported_format_explicit(self, figure):
        """Test that explicitly unsupported format raises ValueError."""
        with tempfile.NamedTemporaryFile(suffix=".glb", delete=False) as f:
            temp_path = Path(f.name)

        try:
            with pytest.raises(ValueError, match="not supported"):
                export_figure(figure, str(temp_path), file_format="invalid_format")
        finally:
            temp_path.unlink()


class TestGetFormatInfo:
    """Tests for get_format_info function."""

    def test_returns_dict(self):
        """Test that function returns a dictionary."""
        info = get_format_info()
        assert isinstance(info, dict)

    def test_contains_available_backends(self):
        """Test that info contains available backends."""
        from figure_generator.backends import get_available_backends

        info = get_format_info()
        available = get_available_backends()

        # All available backends should be in info (except blender which can't be instantiated)
        for backend in available:
            if backend != "blender":
                assert backend in info

    def test_backend_formats_are_lists(self):
        """Test that each backend's formats is a list."""
        info = get_format_info()

        for backend_name, formats in info.items():
            assert isinstance(formats, list), f"{backend_name} formats should be a list"
            assert len(formats) > 0, f"{backend_name} should have at least one format"

    def test_trimesh_formats(self):
        """Test that trimesh backend has expected formats."""
        info = get_format_info()

        if "trimesh" in info:
            formats = info["trimesh"]
            assert "glb" in formats
            assert "obj" in formats
            assert "stl" in formats

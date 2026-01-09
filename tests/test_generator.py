"""Tests for figure_generator.generator module."""

import tempfile
from pathlib import Path

import pytest

from figure_generator.config import FigureConfig
from figure_generator.generator import FigureGenerator, GeneratedFigure
from figure_generator.presets import PRESETS


class TestFigureGenerator:
    """Tests for FigureGenerator class."""

    @pytest.fixture
    def generator(self):
        """Create a FigureGenerator instance."""
        return FigureGenerator()

    def test_backend_name(self, generator):
        """Test that backend_name returns a string."""
        assert isinstance(generator.backend_name, str)
        assert len(generator.backend_name) > 0

    def test_supported_formats(self, generator):
        """Test that supported_formats returns a list."""
        formats = generator.supported_formats
        assert isinstance(formats, list)
        assert len(formats) > 0

    def test_generate_with_preset_name(self, generator):
        """Test generating figure with preset name."""
        figure = generator.generate("female_adult")

        assert isinstance(figure, GeneratedFigure)
        assert figure.part_count > 0
        assert "Head" in figure.part_names

    def test_generate_with_config_dict(self, generator):
        """Test generating figure with config dictionary."""
        config_dict = PRESETS["female_adult"].copy()
        figure = generator.generate(config_dict)

        assert isinstance(figure, GeneratedFigure)
        assert figure.part_count > 0

    def test_generate_with_figure_config(self, generator):
        """Test generating figure with FigureConfig instance."""
        config = FigureConfig.from_dict(PRESETS["female_adult"])
        figure = generator.generate(config)

        assert isinstance(figure, GeneratedFigure)
        assert figure.part_count > 0

    def test_generate_invalid_preset(self, generator):
        """Test that invalid preset raises ValueError."""
        with pytest.raises(ValueError, match="Unknown preset"):
            generator.generate("nonexistent_preset")

    def test_generate_invalid_config_type(self, generator):
        """Test that invalid config type raises TypeError."""
        with pytest.raises(TypeError, match="must be FigureConfig"):
            generator.generate(12345)

    def test_generate_with_arm_angle(self, generator):
        """Test generating with different arm angles."""
        figure_apose = generator.generate("female_adult", arm_angle=45)
        figure_tpose = generator.generate("female_adult", arm_angle=90)

        assert figure_apose.arm_angle == 45
        assert figure_tpose.arm_angle == 90

    def test_generate_all_presets(self, generator):
        """Test that all presets can be generated."""
        for preset_name in PRESETS.keys():
            figure = generator.generate(preset_name)
            assert figure.part_count > 0

    def test_generate_female_has_breasts(self, generator):
        """Test that female preset includes breasts."""
        figure = generator.generate("female_adult")
        assert "Breast_Left" in figure.part_names
        assert "Breast_Right" in figure.part_names

    def test_generate_male_no_breasts(self, generator):
        """Test that male preset does not include breasts."""
        figure = generator.generate("male_adult")
        assert "Breast_Left" not in figure.part_names
        assert "Breast_Right" not in figure.part_names

    def test_generate_has_all_limbs(self, generator):
        """Test that generated figure has all expected limbs."""
        figure = generator.generate("female_adult")

        expected_parts = [
            "Head",
            "Neck",
            "Ribcage",
            "Abdomen",
            "Pelvis",
            "Glute_Left",
            "Glute_Right",
            "UpperArm_Left",
            "UpperArm_Right",
            "Forearm_Left",
            "Forearm_Right",
            "Hand_Left",
            "Hand_Right",
            "Thigh_Left",
            "Thigh_Right",
            "Calf_Left",
            "Calf_Right",
            "Foot_Left",
            "Foot_Right",
        ]

        for part in expected_parts:
            assert part in figure.part_names, f"Missing part: {part}"


class TestGeneratedFigure:
    """Tests for GeneratedFigure dataclass."""

    @pytest.fixture
    def figure(self):
        """Create a GeneratedFigure instance."""
        generator = FigureGenerator()
        return generator.generate("female_adult", arm_angle=45)

    def test_part_names(self, figure):
        """Test part_names property."""
        names = figure.part_names
        assert isinstance(names, list)
        assert all(isinstance(n, str) for n in names)

    def test_part_count(self, figure):
        """Test part_count property."""
        assert figure.part_count == len(figure.meshes)
        assert figure.part_count > 0

    def test_config_preserved(self, figure):
        """Test that config is preserved."""
        assert isinstance(figure.config, FigureConfig)
        assert figure.config.name == "Adult Female"

    def test_arm_angle_preserved(self, figure):
        """Test that arm_angle is preserved."""
        assert figure.arm_angle == 45


class TestExport:
    """Tests for figure export functionality."""

    @pytest.fixture
    def generator(self):
        """Create a FigureGenerator instance."""
        return FigureGenerator()

    @pytest.fixture
    def figure(self, generator):
        """Create a GeneratedFigure instance."""
        return generator.generate("female_adult")

    def test_export_glb(self, generator, figure):
        """Test exporting to GLB format."""
        with tempfile.NamedTemporaryFile(suffix=".glb", delete=False) as f:
            temp_path = Path(f.name)

        try:
            generator.export(figure, str(temp_path))
            assert temp_path.exists()
            assert temp_path.stat().st_size > 0
        finally:
            temp_path.unlink()

    def test_export_obj(self, generator, figure):
        """Test exporting to OBJ format."""
        if "obj" not in generator.supported_formats:
            pytest.skip("OBJ format not supported by backend")

        with tempfile.NamedTemporaryFile(suffix=".obj", delete=False) as f:
            temp_path = Path(f.name)

        try:
            generator.export(figure, str(temp_path))
            assert temp_path.exists()
            assert temp_path.stat().st_size > 0
        finally:
            temp_path.unlink()

    def test_export_stl(self, generator, figure):
        """Test exporting to STL format."""
        if "stl" not in generator.supported_formats:
            pytest.skip("STL format not supported by backend")

        with tempfile.NamedTemporaryFile(suffix=".stl", delete=False) as f:
            temp_path = Path(f.name)

        try:
            generator.export(figure, str(temp_path))
            assert temp_path.exists()
            assert temp_path.stat().st_size > 0
        finally:
            temp_path.unlink()

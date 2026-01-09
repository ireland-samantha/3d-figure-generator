"""Tests for figure_generator.config module."""

import json
import tempfile
from pathlib import Path

import pytest

from figure_generator.config import (
    BodyPartConfig,
    BoxPartConfig,
    FigureConfig,
    FootConfig,
    HandConfig,
    LandmarksConfig,
    SpherePartConfig,
    load_config,
    save_config,
)


class TestBodyPartConfig:
    """Tests for BodyPartConfig dataclass."""

    def test_valid_creation(self):
        """Test creating valid BodyPartConfig."""
        config = BodyPartConfig(radius=0.5, length=1.0)
        assert config.radius == 0.5
        assert config.length == 1.0

    def test_invalid_radius(self):
        """Test that negative radius raises ValueError."""
        with pytest.raises(ValueError, match="radius must be positive"):
            BodyPartConfig(radius=-0.5, length=1.0)

    def test_zero_radius(self):
        """Test that zero radius raises ValueError."""
        with pytest.raises(ValueError, match="radius must be positive"):
            BodyPartConfig(radius=0, length=1.0)

    def test_invalid_length(self):
        """Test that negative length raises ValueError."""
        with pytest.raises(ValueError, match="length must be positive"):
            BodyPartConfig(radius=0.5, length=-1.0)


class TestBoxPartConfig:
    """Tests for BoxPartConfig dataclass."""

    def test_valid_creation(self):
        """Test creating valid BoxPartConfig."""
        config = BoxPartConfig(width=1.0, height=2.0, depth=0.5)
        assert config.width == 1.0
        assert config.height == 2.0
        assert config.depth == 0.5

    def test_invalid_dimensions(self):
        """Test that invalid dimensions raise ValueError."""
        with pytest.raises(ValueError, match="width must be positive"):
            BoxPartConfig(width=-1.0, height=2.0, depth=0.5)

        with pytest.raises(ValueError, match="height must be positive"):
            BoxPartConfig(width=1.0, height=0, depth=0.5)


class TestSpherePartConfig:
    """Tests for SpherePartConfig dataclass."""

    def test_valid_creation(self):
        """Test creating valid SpherePartConfig."""
        config = SpherePartConfig(radius=0.5, offset_x=0.2, offset_y=-0.1, offset_z=0.3)
        assert config.radius == 0.5
        assert config.offset_x == 0.2

    def test_default_offsets(self):
        """Test that offsets default to zero."""
        config = SpherePartConfig(radius=0.5)
        assert config.offset_x == 0.0
        assert config.offset_y == 0.0
        assert config.offset_z == 0.0

    def test_invalid_radius(self):
        """Test that invalid radius raises ValueError."""
        with pytest.raises(ValueError, match="radius must be positive"):
            SpherePartConfig(radius=0)


class TestLandmarksConfig:
    """Tests for LandmarksConfig dataclass."""

    def test_valid_creation(self):
        """Test creating valid LandmarksConfig."""
        config = LandmarksConfig(
            shoulder_y=5.9, bust_y=5.4, waist_y=4.6, pelvis_y=4.0, crotch_y=3.65, knee_y=1.9
        )
        assert config.shoulder_y == 5.9
        assert config.knee_y == 1.9

    def test_invalid_order(self):
        """Test that out-of-order landmarks raise ValueError."""
        with pytest.raises(ValueError, match="descending Y order"):
            LandmarksConfig(
                shoulder_y=5.9,
                bust_y=6.0,  # Higher than shoulder - invalid
                waist_y=4.6,
                pelvis_y=4.0,
                crotch_y=3.65,
                knee_y=1.9,
            )


class TestFigureConfig:
    """Tests for FigureConfig dataclass."""

    @pytest.fixture
    def valid_config_dict(self):
        """Return a valid configuration dictionary."""
        return {
            "name": "Test Figure",
            "total_heads": 7.5,
            "head_radius": 0.5,
            "subdivisions": 2,
            "neck": {"radius": 0.11, "length": 0.35},
            "ribcage": {"width": 1.05, "height": 1.25, "depth": 0.55},
            "breasts": {"radius": 0.18, "offset_x": 0.22, "offset_z": 0.32, "offset_y": -0.1},
            "abdomen": {"radius": 0.30, "length": 0.55},
            "pelvis": {"width": 1.1, "height": 0.7, "depth": 0.5},
            "glutes": {"radius": 0.24, "offset_x": 0.2, "offset_y": -0.15, "offset_z": -0.22},
            "upper_arm": {"radius": 0.105, "length": 1.15},
            "forearm": {"radius": 0.08, "length": 1.0},
            "hand": {"width": 0.09, "length": 0.32, "depth": 0.04},
            "thigh": {"radius": 0.17, "length": 1.75},
            "calf": {"radius": 0.12, "length": 1.7},
            "foot": {"width": 0.14, "height": 0.1, "length": 0.38},
            "shoulder_width": 0.55,
            "hip_width": 0.28,
            "landmarks": {
                "shoulder_y": 5.9,
                "bust_y": 5.4,
                "waist_y": 4.6,
                "pelvis_y": 4.0,
                "crotch_y": 3.65,
                "knee_y": 1.9,
            },
        }

    def test_from_dict(self, valid_config_dict):
        """Test creating FigureConfig from dictionary."""
        config = FigureConfig.from_dict(valid_config_dict)
        assert config.name == "Test Figure"
        assert config.total_heads == 7.5
        assert config.neck.radius == 0.11
        assert config.breasts.radius == 0.18

    def test_from_dict_without_breasts(self, valid_config_dict):
        """Test creating FigureConfig without breasts."""
        valid_config_dict["breasts"] = None
        config = FigureConfig.from_dict(valid_config_dict)
        assert config.breasts is None

    def test_to_dict(self, valid_config_dict):
        """Test converting FigureConfig to dictionary."""
        config = FigureConfig.from_dict(valid_config_dict)
        result = config.to_dict()

        assert result["name"] == "Test Figure"
        assert result["total_heads"] == 7.5
        assert result["neck"]["radius"] == 0.11

    def test_to_dict_removes_none_breasts(self, valid_config_dict):
        """Test that to_dict removes None breasts."""
        valid_config_dict["breasts"] = None
        config = FigureConfig.from_dict(valid_config_dict)
        result = config.to_dict()

        assert "breasts" not in result

    def test_invalid_total_heads(self, valid_config_dict):
        """Test that invalid total_heads raises ValueError."""
        valid_config_dict["total_heads"] = -1
        with pytest.raises(ValueError, match="total_heads must be positive"):
            FigureConfig.from_dict(valid_config_dict)

    def test_invalid_subdivisions(self, valid_config_dict):
        """Test that negative subdivisions raises ValueError."""
        valid_config_dict["subdivisions"] = -1
        with pytest.raises(ValueError, match="subdivisions must be non-negative"):
            FigureConfig.from_dict(valid_config_dict)


class TestLoadSaveConfig:
    """Tests for load_config and save_config functions."""

    @pytest.fixture
    def valid_config_dict(self):
        """Return a valid configuration dictionary."""
        return {
            "name": "Test Figure",
            "total_heads": 7.5,
            "head_radius": 0.5,
            "subdivisions": 2,
            "neck": {"radius": 0.11, "length": 0.35},
            "ribcage": {"width": 1.05, "height": 1.25, "depth": 0.55},
            "abdomen": {"radius": 0.30, "length": 0.55},
            "pelvis": {"width": 1.1, "height": 0.7, "depth": 0.5},
            "glutes": {"radius": 0.24, "offset_x": 0.2, "offset_y": -0.15, "offset_z": -0.22},
            "upper_arm": {"radius": 0.105, "length": 1.15},
            "forearm": {"radius": 0.08, "length": 1.0},
            "hand": {"width": 0.09, "length": 0.32, "depth": 0.04},
            "thigh": {"radius": 0.17, "length": 1.75},
            "calf": {"radius": 0.12, "length": 1.7},
            "foot": {"width": 0.14, "height": 0.1, "length": 0.38},
            "shoulder_width": 0.55,
            "hip_width": 0.28,
            "landmarks": {
                "shoulder_y": 5.9,
                "bust_y": 5.4,
                "waist_y": 4.6,
                "pelvis_y": 4.0,
                "crotch_y": 3.65,
                "knee_y": 1.9,
            },
        }

    def test_save_and_load(self, valid_config_dict):
        """Test saving and loading config round-trip."""
        config = FigureConfig.from_dict(valid_config_dict)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            temp_path = Path(f.name)

        try:
            save_config(config, temp_path)
            loaded = load_config(temp_path)

            assert loaded.name == config.name
            assert loaded.total_heads == config.total_heads
            assert loaded.neck.radius == config.neck.radius
        finally:
            temp_path.unlink()

    def test_load_nonexistent_file(self):
        """Test that loading nonexistent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_config("/nonexistent/path/config.json")

    def test_load_invalid_json(self):
        """Test that loading invalid JSON raises JSONDecodeError."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("not valid json {{{")
            temp_path = Path(f.name)

        try:
            with pytest.raises(json.JSONDecodeError):
                load_config(temp_path)
        finally:
            temp_path.unlink()


class TestConfigEdgeCases:
    """Additional edge case tests for config module."""

    def test_body_part_zero_length(self):
        """Test that zero length raises ValueError."""
        with pytest.raises(ValueError, match="length must be positive"):
            BodyPartConfig(radius=0.5, length=0)

    def test_box_part_zero_depth(self):
        """Test that zero depth raises ValueError."""
        with pytest.raises(ValueError, match="depth must be positive"):
            BoxPartConfig(width=1.0, height=2.0, depth=0)

    def test_sphere_part_negative_offset(self):
        """Test that negative offsets are allowed."""
        config = SpherePartConfig(radius=0.5, offset_x=-0.2, offset_y=-0.1, offset_z=-0.3)
        assert config.offset_x == -0.2
        assert config.offset_y == -0.1
        assert config.offset_z == -0.3

    def test_hand_config_creation(self):
        """Test HandConfig creation."""
        config = HandConfig(width=0.1, length=0.3, depth=0.05)
        assert config.width == 0.1
        assert config.length == 0.3
        assert config.depth == 0.05

    def test_foot_config_creation(self):
        """Test FootConfig creation."""
        config = FootConfig(width=0.15, height=0.1, length=0.4)
        assert config.width == 0.15
        assert config.height == 0.1
        assert config.length == 0.4

    def test_landmarks_with_knee_y(self):
        """Test LandmarksConfig with knee_y."""
        config = LandmarksConfig(
            shoulder_y=5.9, bust_y=5.4, waist_y=4.6, pelvis_y=4.0, crotch_y=3.65, knee_y=1.9
        )
        assert config.shoulder_y == 5.9
        assert config.knee_y == 1.9

    def test_figure_config_head_radius_validation(self):
        """Test head_radius validation in FigureConfig."""
        config_dict = {
            "name": "Test",
            "total_heads": 7.5,
            "head_radius": -0.5,  # Invalid
            "subdivisions": 2,
            "neck": {"radius": 0.11, "length": 0.35},
            "ribcage": {"width": 1.05, "height": 1.25, "depth": 0.55},
            "abdomen": {"radius": 0.30, "length": 0.55},
            "pelvis": {"width": 1.1, "height": 0.7, "depth": 0.5},
            "glutes": {"radius": 0.24, "offset_x": 0.2, "offset_y": -0.15, "offset_z": -0.22},
            "upper_arm": {"radius": 0.105, "length": 1.15},
            "forearm": {"radius": 0.08, "length": 1.0},
            "hand": {"width": 0.09, "length": 0.32, "depth": 0.04},
            "thigh": {"radius": 0.17, "length": 1.75},
            "calf": {"radius": 0.12, "length": 1.7},
            "foot": {"width": 0.14, "height": 0.1, "length": 0.38},
            "shoulder_width": 0.55,
            "hip_width": 0.28,
            "landmarks": {
                "shoulder_y": 5.9,
                "bust_y": 5.4,
                "waist_y": 4.6,
                "pelvis_y": 4.0,
                "crotch_y": 3.65,
                "knee_y": 1.9,
            },
        }
        with pytest.raises(ValueError, match="head_radius must be positive"):
            FigureConfig.from_dict(config_dict)

    def test_figure_config_shoulder_width_validation(self):
        """Test shoulder_width validation in FigureConfig."""
        config_dict = {
            "name": "Test",
            "total_heads": 7.5,
            "head_radius": 0.5,
            "subdivisions": 2,
            "neck": {"radius": 0.11, "length": 0.35},
            "ribcage": {"width": 1.05, "height": 1.25, "depth": 0.55},
            "abdomen": {"radius": 0.30, "length": 0.55},
            "pelvis": {"width": 1.1, "height": 0.7, "depth": 0.5},
            "glutes": {"radius": 0.24, "offset_x": 0.2, "offset_y": -0.15, "offset_z": -0.22},
            "upper_arm": {"radius": 0.105, "length": 1.15},
            "forearm": {"radius": 0.08, "length": 1.0},
            "hand": {"width": 0.09, "length": 0.32, "depth": 0.04},
            "thigh": {"radius": 0.17, "length": 1.75},
            "calf": {"radius": 0.12, "length": 1.7},
            "foot": {"width": 0.14, "height": 0.1, "length": 0.38},
            "shoulder_width": -0.55,  # Invalid
            "hip_width": 0.28,
            "landmarks": {
                "shoulder_y": 5.9,
                "bust_y": 5.4,
                "waist_y": 4.6,
                "pelvis_y": 4.0,
                "crotch_y": 3.65,
                "knee_y": 1.9,
            },
        }
        with pytest.raises(ValueError, match="shoulder_width must be positive"):
            FigureConfig.from_dict(config_dict)

    def test_figure_config_hip_width_validation(self):
        """Test hip_width validation in FigureConfig."""
        config_dict = {
            "name": "Test",
            "total_heads": 7.5,
            "head_radius": 0.5,
            "subdivisions": 2,
            "neck": {"radius": 0.11, "length": 0.35},
            "ribcage": {"width": 1.05, "height": 1.25, "depth": 0.55},
            "abdomen": {"radius": 0.30, "length": 0.55},
            "pelvis": {"width": 1.1, "height": 0.7, "depth": 0.5},
            "glutes": {"radius": 0.24, "offset_x": 0.2, "offset_y": -0.15, "offset_z": -0.22},
            "upper_arm": {"radius": 0.105, "length": 1.15},
            "forearm": {"radius": 0.08, "length": 1.0},
            "hand": {"width": 0.09, "length": 0.32, "depth": 0.04},
            "thigh": {"radius": 0.17, "length": 1.75},
            "calf": {"radius": 0.12, "length": 1.7},
            "foot": {"width": 0.14, "height": 0.1, "length": 0.38},
            "shoulder_width": 0.55,
            "hip_width": -0.28,  # Invalid
            "landmarks": {
                "shoulder_y": 5.9,
                "bust_y": 5.4,
                "waist_y": 4.6,
                "pelvis_y": 4.0,
                "crotch_y": 3.65,
                "knee_y": 1.9,
            },
        }
        with pytest.raises(ValueError, match="hip_width must be positive"):
            FigureConfig.from_dict(config_dict)

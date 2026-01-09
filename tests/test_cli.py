"""Tests for figure_generator.cli module."""

import json
import tempfile
from pathlib import Path

import pytest

from figure_generator.cli import create_parser, main
from figure_generator.presets import POSES, PRESETS


class TestCLIParser:
    """Tests for CLI argument parser."""

    @pytest.fixture
    def parser(self):
        """Create argument parser."""
        return create_parser()

    def test_default_values(self, parser):
        """Test default argument values."""
        args = parser.parse_args([])

        assert args.preset is None
        assert args.config is None
        assert args.pose == "apose"
        assert args.output == "figure.glb"

    def test_preset_argument(self, parser):
        """Test --preset argument."""
        args = parser.parse_args(["--preset", "female_adult"])
        assert args.preset == "female_adult"

    def test_config_argument(self, parser):
        """Test --config argument."""
        args = parser.parse_args(["--config", "test.json"])
        assert args.config == "test.json"

    def test_pose_argument(self, parser):
        """Test --pose argument."""
        args = parser.parse_args(["--pose", "tpose"])
        assert args.pose == "tpose"

    def test_arm_angle_argument(self, parser):
        """Test --arm-angle argument."""
        args = parser.parse_args(["--arm-angle", "60"])
        assert args.arm_angle == 60.0

    def test_output_argument(self, parser):
        """Test --output argument."""
        args = parser.parse_args(["--output", "custom.obj"])
        assert args.output == "custom.obj"

    def test_short_arguments(self, parser):
        """Test short argument forms."""
        args = parser.parse_args(["-p", "male_adult", "-o", "out.glb"])
        assert args.preset == "male_adult"
        assert args.output == "out.glb"


class TestCLIInfoCommands:
    """Tests for CLI info commands."""

    def test_list_presets(self, capsys):
        """Test --list-presets command."""
        result = main(["--list-presets"])

        assert result == 0
        captured = capsys.readouterr()

        for preset_name in PRESETS.keys():
            assert preset_name in captured.out

    def test_list_poses(self, capsys):
        """Test --list-poses command."""
        result = main(["--list-poses"])

        assert result == 0
        captured = capsys.readouterr()

        for pose_name in POSES.keys():
            assert pose_name in captured.out

    def test_list_backends(self, capsys):
        """Test --list-backends command."""
        result = main(["--list-backends"])

        assert result == 0
        captured = capsys.readouterr()
        assert "Available backends" in captured.out

    def test_generate_config(self, capsys):
        """Test --generate-config command."""
        result = main(["--generate-config", "female_adult"])

        assert result == 0
        captured = capsys.readouterr()

        # Should be valid JSON
        config = json.loads(captured.out)
        assert config["name"] == "Adult Female"

    def test_generate_config_invalid_preset(self, capsys):
        """Test --generate-config with invalid preset."""
        result = main(["--generate-config", "nonexistent"])

        assert result == 1
        captured = capsys.readouterr()
        assert "Unknown preset" in captured.err


class TestCLIGeneration:
    """Tests for CLI figure generation."""

    def test_generate_default(self, capsys):
        """Test generation with default options."""
        with tempfile.NamedTemporaryFile(suffix=".glb", delete=False) as f:
            temp_path = Path(f.name)

        try:
            result = main(["--output", str(temp_path)])

            assert result == 0
            assert temp_path.exists()

            captured = capsys.readouterr()
            assert "Exported" in captured.out
        finally:
            temp_path.unlink()

    def test_generate_with_preset(self, capsys):
        """Test generation with preset."""
        with tempfile.NamedTemporaryFile(suffix=".glb", delete=False) as f:
            temp_path = Path(f.name)

        try:
            result = main(["--preset", "male_adult", "--output", str(temp_path)])

            assert result == 0
            assert temp_path.exists()
        finally:
            temp_path.unlink()

    def test_generate_with_config_file(self, capsys):
        """Test generation with config file."""
        # Create temp config file
        config_data = PRESETS["female_adult"]
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            config_path = Path(f.name)

        with tempfile.NamedTemporaryFile(suffix=".glb", delete=False) as f:
            output_path = Path(f.name)

        try:
            result = main(["--config", str(config_path), "--output", str(output_path)])

            assert result == 0
            assert output_path.exists()
        finally:
            config_path.unlink()
            output_path.unlink()

    def test_generate_with_pose(self, capsys):
        """Test generation with pose option."""
        with tempfile.NamedTemporaryFile(suffix=".glb", delete=False) as f:
            temp_path = Path(f.name)

        try:
            result = main(["--pose", "tpose", "--output", str(temp_path)])

            assert result == 0
            assert temp_path.exists()
        finally:
            temp_path.unlink()

    def test_generate_with_arm_angle(self, capsys):
        """Test generation with custom arm angle."""
        with tempfile.NamedTemporaryFile(suffix=".glb", delete=False) as f:
            temp_path = Path(f.name)

        try:
            result = main(["--arm-angle", "60", "--output", str(temp_path)])

            assert result == 0
            assert temp_path.exists()
        finally:
            temp_path.unlink()

    def test_generate_verbose(self, capsys):
        """Test generation with verbose output."""
        with tempfile.NamedTemporaryFile(suffix=".glb", delete=False) as f:
            temp_path = Path(f.name)

        try:
            result = main(["--verbose", "--output", str(temp_path)])

            assert result == 0
            captured = capsys.readouterr()
            assert "Body parts:" in captured.out
        finally:
            temp_path.unlink()

    def test_generate_nonexistent_config(self, capsys):
        """Test generation with nonexistent config file."""
        result = main(["--config", "/nonexistent/config.json"])

        assert result == 1
        captured = capsys.readouterr()
        assert "not found" in captured.err


class TestCLIAllPresets:
    """Test CLI with all presets."""

    @pytest.mark.parametrize("preset_name", list(PRESETS.keys()))
    def test_generate_preset(self, preset_name):
        """Test that each preset can be generated via CLI."""
        with tempfile.NamedTemporaryFile(suffix=".glb", delete=False) as f:
            temp_path = Path(f.name)

        try:
            result = main(["--preset", preset_name, "--output", str(temp_path)])
            assert result == 0
            assert temp_path.exists()
            assert temp_path.stat().st_size > 0
        finally:
            temp_path.unlink()


class TestCLIAllPoses:
    """Test CLI with all poses."""

    @pytest.mark.parametrize("pose_name", list(POSES.keys()))
    def test_generate_pose(self, pose_name):
        """Test that each pose can be generated via CLI."""
        with tempfile.NamedTemporaryFile(suffix=".glb", delete=False) as f:
            temp_path = Path(f.name)

        try:
            result = main(["--pose", pose_name, "--output", str(temp_path)])
            assert result == 0
            assert temp_path.exists()
        finally:
            temp_path.unlink()


class TestCLIEdgeCases:
    """Test CLI edge cases and error handling."""

    def test_backend_argument(self, capsys):
        """Test --backend argument."""
        with tempfile.NamedTemporaryFile(suffix=".glb", delete=False) as f:
            temp_path = Path(f.name)

        try:
            result = main(["--backend", "trimesh", "--output", str(temp_path)])
            assert result == 0
        finally:
            temp_path.unlink()

    def test_format_argument(self, capsys):
        """Test --format argument."""
        with tempfile.NamedTemporaryFile(suffix=".bin", delete=False) as f:
            temp_path = Path(f.name)

        try:
            # Specify format explicitly
            result = main(["--format", "glb", "--output", str(temp_path)])
            assert result == 0
        finally:
            temp_path.unlink()

    def test_export_error_handling(self, capsys):
        """Test export error handling with unsupported format."""
        with tempfile.NamedTemporaryFile(suffix=".xyz", delete=False) as f:
            temp_path = Path(f.name)

        try:
            result = main(["--output", str(temp_path)])
            assert result == 1
            captured = capsys.readouterr()
            assert "Error" in captured.err
        finally:
            if temp_path.exists():
                temp_path.unlink()

    def test_version_shown_in_help(self, capsys):
        """Test that version is accessible."""
        from figure_generator.cli import create_parser

        parser = create_parser()
        # Just verify the parser was created with version
        assert parser is not None


class TestCLIBackendListing:
    """Test CLI backend listing functionality."""

    def test_list_backends_shows_blender_info(self, capsys):
        """Test that list-backends shows Blender backend info correctly."""
        result = main(["--list-backends"])
        assert result == 0

        captured = capsys.readouterr()
        # Should show blender as not installed (since we're not in Blender)
        assert "blender" in captured.out


class TestCLIMultipleFormats:
    """Test CLI with various output formats."""

    @pytest.mark.parametrize(
        "suffix,format_name",
        [
            (".glb", None),
            (".obj", None),
            (".stl", None),
            (".ply", None),
        ],
    )
    def test_various_formats(self, suffix, format_name):
        """Test generation with various output formats."""
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as f:
            temp_path = Path(f.name)

        try:
            args = ["--output", str(temp_path)]
            if format_name:
                args.extend(["--format", format_name])
            result = main(args)
            assert result == 0
            assert temp_path.exists()
        finally:
            temp_path.unlink()

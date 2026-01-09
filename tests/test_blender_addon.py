"""Tests for figure_generator.blender_addon module using mocks.

These tests mock Blender's bpy module to test the addon logic without
requiring Blender to be installed.
"""

import math
import sys
from unittest.mock import MagicMock

import pytest


# Create mock bpy module before importing blender_addon
@pytest.fixture(scope="module", autouse=True)
def mock_bpy():
    """Create a mock bpy module."""
    # Create mock bpy
    mock_bpy = MagicMock()

    # Mock bpy.props
    mock_bpy.props.EnumProperty = MagicMock(return_value=None)
    mock_bpy.props.FloatProperty = MagicMock(return_value=None)
    mock_bpy.props.BoolProperty = MagicMock(return_value=None)
    mock_bpy.props.IntProperty = MagicMock(return_value=None)
    mock_bpy.props.StringProperty = MagicMock(return_value=None)

    # Mock bpy.types
    mock_bpy.types.Operator = MagicMock
    mock_bpy.types.Panel = MagicMock
    mock_bpy.types.Menu = MagicMock
    mock_bpy.types.AddonPreferences = MagicMock

    # Mock bpy.utils
    mock_bpy.utils.register_class = MagicMock()
    mock_bpy.utils.unregister_class = MagicMock()

    # Mock bpy.data
    mock_bpy.data.collections = {}
    mock_bpy.data.meshes = MagicMock()
    mock_bpy.data.objects = MagicMock()

    # Add to sys.modules
    sys.modules["bpy"] = mock_bpy
    sys.modules["bpy.props"] = mock_bpy.props
    sys.modules["bpy.types"] = mock_bpy.types
    sys.modules["bpy.utils"] = mock_bpy.utils

    # Mock bmesh
    mock_bmesh = MagicMock()
    sys.modules["bmesh"] = mock_bmesh

    # Mock mathutils
    mock_mathutils = MagicMock()
    mock_mathutils.Matrix = MagicMock()
    mock_mathutils.Matrix.Rotation = MagicMock(return_value=MagicMock())
    mock_mathutils.Matrix.Scale = MagicMock(return_value=MagicMock())
    mock_mathutils.Vector = MagicMock()
    sys.modules["mathutils"] = mock_mathutils

    yield mock_bpy

    # Cleanup
    del sys.modules["bpy"]
    del sys.modules["bpy.props"]
    del sys.modules["bpy.types"]
    del sys.modules["bpy.utils"]
    del sys.modules["bmesh"]
    del sys.modules["mathutils"]


class TestBlenderAddonPresets:
    """Tests for preset data in blender_addon."""

    def test_presets_exist(self, mock_bpy):
        """Test that all presets are defined."""
        from figure_generator.blender_addon import PRESETS

        assert "female_adult" in PRESETS
        assert "male_adult" in PRESETS
        assert "child" in PRESETS
        assert "heroic" in PRESETS

    def test_preset_structure(self, mock_bpy):
        """Test that presets have required fields."""
        from figure_generator.blender_addon import PRESETS

        required_fields = [
            "name",
            "total_heads",
            "head_radius",
            "shoulder_width",
            "hip_width",
            "subdivisions",
            "neck",
            "ribcage",
            "abdomen",
            "pelvis",
            "glutes",
            "upper_arm",
            "forearm",
            "hand",
            "thigh",
            "calf",
            "foot",
            "landmarks",
        ]

        for preset_name, preset in PRESETS.items():
            for field in required_fields:
                assert field in preset, f"{preset_name} missing {field}"

    def test_female_has_breasts(self, mock_bpy):
        """Test that female preset has breasts."""
        from figure_generator.blender_addon import PRESETS

        assert PRESETS["female_adult"]["breasts"] is not None
        assert PRESETS["female_adult"]["breasts"]["radius"] > 0

    def test_male_no_breasts(self, mock_bpy):
        """Test that male preset has no breasts."""
        from figure_generator.blender_addon import PRESETS

        assert PRESETS["male_adult"]["breasts"] is None

    def test_child_no_breasts(self, mock_bpy):
        """Test that child preset has no breasts."""
        from figure_generator.blender_addon import PRESETS

        assert PRESETS["child"]["breasts"] is None

    def test_heroic_no_breasts(self, mock_bpy):
        """Test that heroic preset has no breasts."""
        from figure_generator.blender_addon import PRESETS

        assert PRESETS["heroic"]["breasts"] is None

    def test_preset_head_counts(self, mock_bpy):
        """Test that presets have correct head counts."""
        from figure_generator.blender_addon import PRESETS

        assert PRESETS["female_adult"]["total_heads"] == 7.5
        assert PRESETS["male_adult"]["total_heads"] == 8.0
        assert PRESETS["child"]["total_heads"] == 6.0
        assert PRESETS["heroic"]["total_heads"] == 8.5


class TestBlenderAddonPoses:
    """Tests for pose data in blender_addon."""

    def test_poses_exist(self, mock_bpy):
        """Test that all poses are defined."""
        from figure_generator.blender_addon import POSES

        assert "apose" in POSES
        assert "tpose" in POSES
        assert "relaxed" in POSES

    def test_pose_angles(self, mock_bpy):
        """Test that poses have correct angles."""
        from figure_generator.blender_addon import POSES

        assert POSES["apose"] == 45.0
        assert POSES["tpose"] == 90.0
        assert POSES["relaxed"] == 20.0  # Shared preset value


class TestBlenderAddonMeshCreation:
    """Tests for mesh creation functions."""

    def test_create_icosphere_function_exists(self, mock_bpy):
        """Test that create_icosphere function exists."""
        from figure_generator.blender_addon import create_icosphere

        assert callable(create_icosphere)

    def test_create_cylinder_z_function_exists(self, mock_bpy):
        """Test that create_cylinder_z function exists."""
        from figure_generator.blender_addon import create_cylinder_z

        assert callable(create_cylinder_z)

    def test_create_cylinder_arm_function_exists(self, mock_bpy):
        """Test that create_cylinder_arm function exists."""
        from figure_generator.blender_addon import create_cylinder_arm

        assert callable(create_cylinder_arm)

    def test_create_box_function_exists(self, mock_bpy):
        """Test that create_box function exists."""
        from figure_generator.blender_addon import create_box

        assert callable(create_box)

    def test_bmesh_to_object_function_exists(self, mock_bpy):
        """Test that bmesh_to_object function exists."""
        from figure_generator.blender_addon import bmesh_to_object

        assert callable(bmesh_to_object)


class TestBlenderAddonFigureGenerator:
    """Tests for generate_figure function."""

    def test_generate_figure_function_exists(self, mock_bpy):
        """Test that generate_figure function exists."""
        from figure_generator.blender_addon import generate_figure

        assert callable(generate_figure)


class TestBlenderAddonOperators:
    """Tests for Blender operators."""

    def test_main_operator_class_exists(self, mock_bpy):
        """Test that main operator class exists."""
        from figure_generator.blender_addon import MESH_OT_figure_generator

        assert MESH_OT_figure_generator is not None
        assert hasattr(MESH_OT_figure_generator, "bl_idname")
        assert hasattr(MESH_OT_figure_generator, "bl_label")

    def test_preset_operators_exist(self, mock_bpy):
        """Test that preset operator classes exist."""
        from figure_generator.blender_addon import (
            MESH_OT_figure_child,
            MESH_OT_figure_female,
            MESH_OT_figure_heroic,
            MESH_OT_figure_male,
        )

        assert MESH_OT_figure_female is not None
        assert MESH_OT_figure_male is not None
        assert MESH_OT_figure_child is not None
        assert MESH_OT_figure_heroic is not None

    def test_operator_bl_idnames(self, mock_bpy):
        """Test that operators have correct bl_idnames."""
        from figure_generator.blender_addon import (
            MESH_OT_figure_child,
            MESH_OT_figure_female,
            MESH_OT_figure_generator,
            MESH_OT_figure_heroic,
            MESH_OT_figure_male,
        )

        assert MESH_OT_figure_generator.bl_idname == "mesh.figure_generator"
        assert MESH_OT_figure_female.bl_idname == "mesh.figure_female"
        assert MESH_OT_figure_male.bl_idname == "mesh.figure_male"
        assert MESH_OT_figure_child.bl_idname == "mesh.figure_child"
        assert MESH_OT_figure_heroic.bl_idname == "mesh.figure_heroic"


class TestBlenderAddonMenu:
    """Tests for Blender menu."""

    def test_menu_class_exists(self, mock_bpy):
        """Test that menu class exists."""
        from figure_generator.blender_addon import MESH_MT_figure_submenu

        assert MESH_MT_figure_submenu is not None
        assert hasattr(MESH_MT_figure_submenu, "bl_idname")
        assert hasattr(MESH_MT_figure_submenu, "bl_label")

    def test_menu_bl_idname(self, mock_bpy):
        """Test that menu has correct bl_idname."""
        from figure_generator.blender_addon import MESH_MT_figure_submenu

        assert MESH_MT_figure_submenu.bl_idname == "MESH_MT_figure_submenu"
        assert MESH_MT_figure_submenu.bl_label == "Figure"


class TestBlenderAddonRegistration:
    """Tests for addon registration."""

    def test_register_function_exists(self, mock_bpy):
        """Test that register function exists."""
        from figure_generator.blender_addon import register

        assert callable(register)

    def test_unregister_function_exists(self, mock_bpy):
        """Test that unregister function exists."""
        from figure_generator.blender_addon import unregister

        assert callable(unregister)

    def test_classes_tuple_exists(self, mock_bpy):
        """Test that classes tuple exists and has correct count."""
        from figure_generator.blender_addon import classes

        assert isinstance(classes, tuple)
        assert len(classes) == 6  # 5 operators + 1 menu


class TestBlenderAddonBlInfo:
    """Tests for bl_info metadata."""

    def test_bl_info_exists(self, mock_bpy):
        """Test that bl_info exists."""
        from figure_generator.blender_addon import bl_info

        assert isinstance(bl_info, dict)

    def test_bl_info_required_fields(self, mock_bpy):
        """Test that bl_info has required fields."""
        from figure_generator.blender_addon import bl_info

        required = ["name", "author", "version", "blender", "location", "description", "category"]

        for field in required:
            assert field in bl_info, f"bl_info missing {field}"

    def test_bl_info_values(self, mock_bpy):
        """Test bl_info values."""
        from figure_generator.blender_addon import bl_info

        assert bl_info["name"] == "Figure Generator"
        assert bl_info["category"] == "Add Mesh"
        assert isinstance(bl_info["version"], tuple)
        assert len(bl_info["version"]) == 3


class TestArmAngleCalculations:
    """Tests for arm angle calculations."""

    def test_apose_angle(self, mock_bpy):
        """Test A-pose angle calculation."""
        from figure_generator.blender_addon import POSES

        angle = POSES["apose"]
        # At 45 degrees, sin and cos should be equal
        assert abs(math.sin(math.radians(angle)) - math.cos(math.radians(angle))) < 0.01

    def test_tpose_angle(self, mock_bpy):
        """Test T-pose angle calculation."""
        from figure_generator.blender_addon import POSES

        angle = POSES["tpose"]
        # At 90 degrees, sin should be 1, cos should be 0
        assert abs(math.sin(math.radians(angle)) - 1.0) < 0.01
        assert abs(math.cos(math.radians(angle))) < 0.01

    def test_relaxed_angle(self, mock_bpy):
        """Test relaxed pose angle calculation."""
        from figure_generator.blender_addon import POSES

        angle = POSES["relaxed"]
        # At 15 degrees, arm is mostly down
        assert math.cos(math.radians(angle)) > 0.9


class TestLandmarkConsistency:
    """Tests for landmark consistency across presets."""

    def test_landmarks_descend(self, mock_bpy):
        """Test that landmarks descend from top to bottom."""
        from figure_generator.blender_addon import PRESETS

        for preset_name, preset in PRESETS.items():
            landmarks = preset["landmarks"]
            assert (
                landmarks["shoulder_y"] > landmarks["bust_y"]
            ), f"{preset_name}: shoulder should be above bust"
            assert (
                landmarks["bust_y"] > landmarks["waist_y"]
            ), f"{preset_name}: bust should be above waist"
            assert (
                landmarks["waist_y"] > landmarks["pelvis_y"]
            ), f"{preset_name}: waist should be above pelvis"
            assert (
                landmarks["pelvis_y"] > landmarks["crotch_y"]
            ), f"{preset_name}: pelvis should be above crotch"

    def test_total_heads_matches_height(self, mock_bpy):
        """Test that total_heads roughly matches figure height."""
        from figure_generator.blender_addon import PRESETS

        for preset_name, preset in PRESETS.items():
            total_heads = preset["total_heads"]
            head_radius = preset["head_radius"]
            shoulder_y = preset["landmarks"]["shoulder_y"]

            # Head top should be roughly at total_heads
            head_top = shoulder_y + head_radius + preset["neck"]["length"] + head_radius
            assert head_top <= total_heads + 0.5, f"{preset_name}: head extends beyond total_heads"

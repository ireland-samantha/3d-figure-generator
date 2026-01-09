"""
Figure generator core logic.

This module contains the FigureGenerator class which orchestrates the creation
of anatomically-proportioned figure meshes using configurable presets and
mesh backends.

The generator follows classical figure drawing proportions where the head
is used as the unit of measurement (typically 7.5-8.5 heads tall for adults).

Architecture:
    - FigureGenerator: Orchestrates mesh creation (this module)
    - MeshBackend: Creates primitive shapes (backends module)
    - FigureConfig: Defines proportions (config module)
    - Presets: Pre-defined figure types (presets module)

Example:
    >>> from figure_generator import FigureGenerator
    >>> generator = FigureGenerator()
    >>> figure = generator.generate("female_adult", arm_angle=45)
    >>> generator.export(figure, "figure.glb")
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from figure_generator.backends import MeshBackend, MeshData, create_backend
from figure_generator.config import FigureConfig
from figure_generator.presets import PRESETS

if TYPE_CHECKING:
    pass


# =============================================================================
# Constants
# =============================================================================

# Ribcage vertical offset from shoulder landmark
# This positions the ribcage box so its top edge aligns near the shoulders
# while allowing for neck/shoulder transition (in head units)
RIBCAGE_SHOULDER_OFFSET: float = 0.4

# Foot forward offset for natural standing position
# Positions the foot slightly forward of the ankle for balance (in head units)
FOOT_FORWARD_OFFSET: float = 0.12

# Default arm angle for A-pose (degrees from vertical)
DEFAULT_ARM_ANGLE: float = 45.0


# =============================================================================
# Data Classes
# =============================================================================


@dataclass
class GeneratedFigure:
    """
    Container for a generated figure and its metadata.

    Holds all the mesh parts that make up a figure along with the
    configuration used to generate it. This allows for inspection,
    modification, and export of the generated figure.

    Attributes:
        meshes: List of MeshData objects, one per body part.
        config: The FigureConfig that defined the proportions.
        arm_angle: Arm angle in degrees from vertical (0=down, 90=T-pose).

    Example:
        >>> figure = generator.generate("male_adult")
        >>> print(f"Figure has {figure.part_count} parts")
        >>> print(f"Parts: {figure.part_names}")
    """

    meshes: list[MeshData]
    config: FigureConfig
    arm_angle: float

    @property
    def part_names(self) -> list[str]:
        """
        Return list of body part names in generation order.

        Returns:
            List of part name strings (e.g., ["Head", "Neck", ...]).
        """
        return [mesh.name for mesh in self.meshes]

    @property
    def part_count(self) -> int:
        """
        Return total number of body parts.

        Returns:
            Integer count of mesh parts.
        """
        return len(self.meshes)


# =============================================================================
# Generator Class
# =============================================================================


class FigureGenerator:
    """
    Generator for anatomically-proportioned figure meshes.

    Creates 3D primitive meshes (spheres, cylinders, boxes) arranged according
    to classical figure drawing proportions. The figure is generated standing
    upright with feet at Y=0.

    Coordinate System:
        - Y-axis: Vertical (height), positive is up
        - X-axis: Lateral (width), positive is figure's left
        - Z-axis: Depth, positive is forward

    Design Principles:
        - Single Responsibility: Only handles figure generation logic
        - Dependency Injection: Backend is injected, not created internally
        - Strategy Pattern: Different backends can be swapped

    Body Part Generation Order:
        1. Head (sphere at top)
        2. Neck (vertical cylinder)
        3. Ribcage (box for torso)
        4. Breasts (optional paired spheres)
        5. Abdomen (vertical cylinder)
        6. Pelvis (box)
        7. Glutes (paired spheres)
        8. Arms (upper arm, forearm, hand - both sides)
        9. Legs (thigh, calf, foot - both sides)

    Example:
        >>> generator = FigureGenerator()
        >>> figure = generator.generate("female_adult", arm_angle=45)
        >>> generator.export(figure, "output.glb")
    """

    def __init__(self, backend: MeshBackend | None = None) -> None:
        """
        Initialize the figure generator.

        Args:
            backend: MeshBackend instance for mesh creation. If None,
                automatically selects the best available backend.
        """
        self._backend = backend or create_backend()

    @property
    def backend_name(self) -> str:
        """
        Return the name of the active mesh backend.

        Returns:
            Backend identifier string (e.g., "trimesh", "blender").
        """
        return self._backend.name

    @property
    def supported_formats(self) -> list[str]:
        """
        Return list of export formats supported by the current backend.

        Returns:
            List of format extensions (e.g., ["glb", "obj", "stl"]).
        """
        return self._backend.get_supported_formats()

    def generate(
        self,
        config: FigureConfig | str | dict[str, Any],
        arm_angle: float = DEFAULT_ARM_ANGLE,
    ) -> GeneratedFigure:
        """
        Generate a complete figure from configuration.

        Accepts configuration in multiple formats for flexibility:
        - Preset name string (e.g., "female_adult")
        - Dictionary matching preset structure
        - FigureConfig instance

        Args:
            config: Figure configuration in one of three forms:
                - str: Preset name ("female_adult", "male_adult", etc.)
                - dict: Configuration dictionary
                - FigureConfig: Pre-built configuration object
            arm_angle: Arm angle in degrees from vertical.
                - 0: Arms straight down
                - 45: A-pose (default, good for sculpting)
                - 90: T-pose (good for rigging)

        Returns:
            GeneratedFigure containing all body part meshes.

        Raises:
            ValueError: If preset name is not recognized.
            TypeError: If config is not a supported type.

        Example:
            >>> figure = generator.generate("female_adult", arm_angle=45)
            >>> figure = generator.generate({"total_heads": 8.0, ...})
        """
        resolved_config = self._resolve_config(config)
        meshes = self._generate_all_body_parts(resolved_config, arm_angle)

        return GeneratedFigure(
            meshes=meshes,
            config=resolved_config,
            arm_angle=arm_angle,
        )

    def export(
        self,
        figure: GeneratedFigure,
        filepath: str,
        file_format: str | None = None,
    ) -> None:
        """
        Export a generated figure to a file.

        Args:
            figure: GeneratedFigure instance to export.
            filepath: Output file path with extension.
            file_format: Optional format override. If None, inferred
                from filepath extension.

        Example:
            >>> generator.export(figure, "output.glb")
            >>> generator.export(figure, "output.obj", file_format="obj")
        """
        self._backend.export(figure.meshes, filepath, file_format)

    # =========================================================================
    # Private Methods - Configuration
    # =========================================================================

    def _resolve_config(
        self,
        config: FigureConfig | str | dict[str, Any],
    ) -> FigureConfig:
        """
        Resolve configuration input to a FigureConfig instance.

        Args:
            config: Configuration in string, dict, or FigureConfig form.

        Returns:
            Resolved FigureConfig instance.

        Raises:
            ValueError: If preset name is not found.
            TypeError: If config type is not supported.
        """
        if isinstance(config, str):
            return self._resolve_preset_name(config)
        elif isinstance(config, dict):
            return FigureConfig.from_dict(config)
        elif isinstance(config, FigureConfig):
            return config
        else:
            raise TypeError(
                f"config must be FigureConfig, str, or dict, got {type(config).__name__}"
            )

    def _resolve_preset_name(self, preset_name: str) -> FigureConfig:
        """
        Look up a preset by name and return its FigureConfig.

        Args:
            preset_name: Name of preset (e.g., "female_adult").

        Returns:
            FigureConfig for the named preset.

        Raises:
            ValueError: If preset name is not found.
        """
        if preset_name not in PRESETS:
            available = list(PRESETS.keys())
            raise ValueError(f"Unknown preset '{preset_name}'. Available: {available}")

        return FigureConfig.from_dict(PRESETS[preset_name])

    # =========================================================================
    # Private Methods - Body Part Generation
    # =========================================================================

    def _generate_all_body_parts(
        self,
        config: FigureConfig,
        arm_angle: float,
    ) -> list[MeshData]:
        """
        Generate all body part meshes in anatomical order.

        Args:
            config: Figure configuration with proportions.
            arm_angle: Arm angle in degrees from vertical.

        Returns:
            List of MeshData for all body parts.
        """
        meshes: list[MeshData] = []

        # Core body parts
        meshes.extend(self._generate_head_and_neck(config))
        meshes.extend(self._generate_torso(config))
        meshes.extend(self._generate_pelvis_and_glutes(config))

        # Limbs
        meshes.extend(self._generate_arms(config, arm_angle))
        meshes.extend(self._generate_legs(config))

        return meshes

    def _generate_head_and_neck(self, config: FigureConfig) -> list[MeshData]:
        """
        Generate head and neck meshes.

        The head is positioned at the top of the figure based on total_heads
        height. The neck connects the head to the torso.

        Args:
            config: Figure configuration.

        Returns:
            List containing head and neck MeshData.
        """
        meshes: list[MeshData] = []
        subdivisions = config.subdivisions

        # Head: sphere at top of figure
        # Position is total height minus head radius (so top of head = total_heads)
        head_y = config.total_heads - config.head_radius
        head = self._backend.create_sphere(
            radius=config.head_radius,
            center=(0, head_y, 0),
            subdivisions=subdivisions,
        )
        head.name = "Head"
        meshes.append(head)

        # Neck: vertical cylinder connecting head to torso
        # Positioned between bottom of head and top of ribcage
        neck_y = head_y - config.head_radius - config.neck.length / 2
        neck = self._backend.create_cylinder(
            radius=config.neck.radius,
            height=config.neck.length,
            center=(0, neck_y, 0),
            rotation_degrees=(90, 0, 0),  # Rotate to vertical (along Y-axis)
        )
        neck.name = "Neck"
        meshes.append(neck)

        return meshes

    def _generate_torso(self, config: FigureConfig) -> list[MeshData]:
        """
        Generate torso meshes: ribcage, breasts (optional), and abdomen.

        The torso spans from shoulders to waist, with the ribcage forming
        the upper chest and the abdomen connecting to the pelvis.

        Args:
            config: Figure configuration.

        Returns:
            List containing ribcage, optional breasts, and abdomen MeshData.
        """
        meshes: list[MeshData] = []
        landmarks = config.landmarks
        subdivisions = config.subdivisions

        # Ribcage: box forming upper torso
        # Offset from shoulder landmark to position top edge near shoulders
        ribcage_y = landmarks.shoulder_y - config.ribcage.height / 2 + RIBCAGE_SHOULDER_OFFSET
        ribcage = self._backend.create_box(
            extents=(config.ribcage.width, config.ribcage.height, config.ribcage.depth),
            center=(0, ribcage_y, 0),
        )
        ribcage.name = "Ribcage"
        meshes.append(ribcage)

        # Breasts: optional paired spheres on front of ribcage
        if config.breasts is not None:
            breast_meshes = self._generate_paired_spheres(
                radius=config.breasts.radius,
                base_y=landmarks.bust_y,
                offset_x=config.breasts.offset_x,
                offset_z=config.breasts.offset_z,
                subdivisions=subdivisions,
                name_prefix="Breast",
            )
            meshes.extend(breast_meshes)

        # Abdomen: vertical cylinder at waist
        abdomen = self._backend.create_cylinder(
            radius=config.abdomen.radius,
            height=config.abdomen.length,
            center=(0, landmarks.waist_y, 0),
            rotation_degrees=(90, 0, 0),  # Vertical
        )
        abdomen.name = "Abdomen"
        meshes.append(abdomen)

        return meshes

    def _generate_pelvis_and_glutes(self, config: FigureConfig) -> list[MeshData]:
        """
        Generate pelvis and glute meshes.

        The pelvis is a box forming the hip structure. Glutes are paired
        spheres positioned behind and below the pelvis center.

        Args:
            config: Figure configuration.

        Returns:
            List containing pelvis and glute MeshData.
        """
        meshes: list[MeshData] = []
        landmarks = config.landmarks
        subdivisions = config.subdivisions

        # Pelvis: box at hip level
        pelvis = self._backend.create_box(
            extents=(config.pelvis.width, config.pelvis.height, config.pelvis.depth),
            center=(0, landmarks.pelvis_y, 0),
        )
        pelvis.name = "Pelvis"
        meshes.append(pelvis)

        # Glutes: paired spheres behind pelvis
        glute_y = landmarks.pelvis_y + config.glutes.offset_y
        glute_meshes = self._generate_paired_spheres(
            radius=config.glutes.radius,
            base_y=glute_y,
            offset_x=config.glutes.offset_x,
            offset_z=config.glutes.offset_z,
            subdivisions=subdivisions,
            name_prefix="Glute",
        )
        meshes.extend(glute_meshes)

        return meshes

    def _generate_arms(
        self,
        config: FigureConfig,
        arm_angle: float,
    ) -> list[MeshData]:
        """
        Generate arm meshes for both sides.

        Each arm consists of:
        - Upper arm: cylinder from shoulder to elbow
        - Forearm: cylinder from elbow to wrist
        - Hand: box at wrist

        Arms are positioned and rotated based on arm_angle parameter.

        Args:
            config: Figure configuration.
            arm_angle: Angle in degrees from vertical (0=down, 90=horizontal).

        Returns:
            List containing all arm part MeshData (6 total: 3 per side).
        """
        meshes: list[MeshData] = []

        shoulder_x = config.shoulder_width
        shoulder_y = config.landmarks.shoulder_y
        angle_rad = math.radians(arm_angle)

        # Generate for both sides: Left (positive X) and Right (negative X)
        for side_name, x_sign in [("Left", 1), ("Right", -1)]:
            arm_parts = self._generate_single_arm(
                config=config,
                shoulder_x=shoulder_x,
                shoulder_y=shoulder_y,
                angle_rad=angle_rad,
                arm_angle=arm_angle,
                side_name=side_name,
                x_sign=x_sign,
            )
            meshes.extend(arm_parts)

        return meshes

    def _generate_single_arm(
        self,
        config: FigureConfig,
        shoulder_x: float,
        shoulder_y: float,
        angle_rad: float,
        arm_angle: float,
        side_name: str,
        x_sign: int,
    ) -> list[MeshData]:
        """
        Generate meshes for a single arm (upper arm, forearm, hand).

        Args:
            config: Figure configuration.
            shoulder_x: X distance from center to shoulder joint.
            shoulder_y: Y height of shoulder joint.
            angle_rad: Arm angle in radians.
            arm_angle: Arm angle in degrees (for rotation).
            side_name: "Left" or "Right".
            x_sign: 1 for left side, -1 for right side.

        Returns:
            List of 3 MeshData (upper arm, forearm, hand).
        """
        meshes: list[MeshData] = []

        # Upper arm: from shoulder, angled down/out
        upper_arm_center, elbow_pos = self._calculate_limb_segment_position(
            joint_x=shoulder_x,
            joint_y=shoulder_y,
            segment_length=config.upper_arm.length,
            angle_rad=angle_rad,
            x_sign=x_sign,
        )

        upper_arm = self._backend.create_cylinder(
            radius=config.upper_arm.radius,
            height=config.upper_arm.length,
            center=upper_arm_center,
            rotation_degrees=(90, 0, x_sign * arm_angle),
        )
        upper_arm.name = f"UpperArm_{side_name}"
        meshes.append(upper_arm)

        # Forearm: from elbow, continuing at same angle
        forearm_center, wrist_pos = self._calculate_limb_segment_position(
            joint_x=elbow_pos[0],
            joint_y=elbow_pos[1],
            segment_length=config.forearm.length,
            angle_rad=angle_rad,
            x_sign=x_sign,
        )

        forearm = self._backend.create_cylinder(
            radius=config.forearm.radius,
            height=config.forearm.length,
            center=forearm_center,
            rotation_degrees=(90, 0, x_sign * arm_angle),
        )
        forearm.name = f"Forearm_{side_name}"
        meshes.append(forearm)

        # Hand: box at wrist, oriented along arm direction
        hand_center = self._calculate_hand_position(
            wrist_x=wrist_pos[0],
            wrist_y=wrist_pos[1],
            hand_length=config.hand.length,
            angle_rad=angle_rad,
            x_sign=x_sign,
        )

        hand = self._backend.create_box(
            extents=(config.hand.width, config.hand.length, config.hand.depth),
            center=hand_center,
            rotation_degrees=(0, 0, x_sign * arm_angle),
        )
        hand.name = f"Hand_{side_name}"
        meshes.append(hand)

        return meshes

    def _generate_legs(self, config: FigureConfig) -> list[MeshData]:
        """
        Generate leg meshes for both sides.

        Each leg consists of:
        - Thigh: vertical cylinder from hip to knee
        - Calf: vertical cylinder from knee to ankle
        - Foot: box at ground level

        Legs are always vertical (no leg angle parameter).

        Args:
            config: Figure configuration.

        Returns:
            List containing all leg part MeshData (6 total: 3 per side).
        """
        meshes: list[MeshData] = []

        hip_x = config.hip_width
        crotch_y = config.landmarks.crotch_y

        # Generate for both sides
        for side_name, x_sign in [("Left", 1), ("Right", -1)]:
            leg_parts = self._generate_single_leg(
                config=config,
                hip_x=hip_x,
                crotch_y=crotch_y,
                side_name=side_name,
                x_sign=x_sign,
            )
            meshes.extend(leg_parts)

        return meshes

    def _generate_single_leg(
        self,
        config: FigureConfig,
        hip_x: float,
        crotch_y: float,
        side_name: str,
        x_sign: int,
    ) -> list[MeshData]:
        """
        Generate meshes for a single leg (thigh, calf, foot).

        Args:
            config: Figure configuration.
            hip_x: X distance from center to hip joint.
            crotch_y: Y height of crotch/hip joint.
            side_name: "Left" or "Right".
            x_sign: 1 for left side, -1 for right side.

        Returns:
            List of 3 MeshData (thigh, calf, foot).
        """
        meshes: list[MeshData] = []

        leg_x = x_sign * hip_x

        # Thigh: vertical cylinder from hip down
        thigh_center_y = crotch_y - config.thigh.length / 2
        thigh = self._backend.create_cylinder(
            radius=config.thigh.radius,
            height=config.thigh.length,
            center=(leg_x, thigh_center_y, 0),
            rotation_degrees=(90, 0, 0),  # Vertical
        )
        thigh.name = f"Thigh_{side_name}"
        meshes.append(thigh)

        # Knee position (bottom of thigh)
        knee_y = crotch_y - config.thigh.length

        # Calf: vertical cylinder from knee down
        calf_center_y = knee_y - config.calf.length / 2
        calf = self._backend.create_cylinder(
            radius=config.calf.radius,
            height=config.calf.length,
            center=(leg_x, calf_center_y, 0),
            rotation_degrees=(90, 0, 0),  # Vertical
        )
        calf.name = f"Calf_{side_name}"
        meshes.append(calf)

        # Foot: box at ground level, offset forward for natural stance
        foot_center = (
            leg_x,
            config.foot.height / 2,  # Bottom of foot at Y=0
            config.foot.length / 2 - FOOT_FORWARD_OFFSET,  # Slightly forward
        )
        foot = self._backend.create_box(
            extents=(config.foot.width, config.foot.height, config.foot.length),
            center=foot_center,
        )
        foot.name = f"Foot_{side_name}"
        meshes.append(foot)

        return meshes

    # =========================================================================
    # Private Methods - Geometry Helpers
    # =========================================================================

    def _generate_paired_spheres(
        self,
        radius: float,
        base_y: float,
        offset_x: float,
        offset_z: float,
        subdivisions: int,
        name_prefix: str,
    ) -> list[MeshData]:
        """
        Generate a symmetric pair of spheres (left and right).

        Used for breasts, glutes, and other paired anatomical features.

        Args:
            radius: Sphere radius.
            base_y: Y position for both spheres.
            offset_x: X distance from center (positive = left).
            offset_z: Z offset (positive = forward).
            subdivisions: Mesh subdivision level.
            name_prefix: Name prefix (e.g., "Breast" -> "Breast_Left").

        Returns:
            List of 2 MeshData (left and right spheres).
        """
        left = self._backend.create_sphere(
            radius=radius,
            center=(offset_x, base_y, offset_z),
            subdivisions=subdivisions,
        )
        left.name = f"{name_prefix}_Left"

        right = self._backend.create_sphere(
            radius=radius,
            center=(-offset_x, base_y, offset_z),
            subdivisions=subdivisions,
        )
        right.name = f"{name_prefix}_Right"

        return [left, right]

    def _calculate_limb_segment_position(
        self,
        joint_x: float,
        joint_y: float,
        segment_length: float,
        angle_rad: float,
        x_sign: int,
    ) -> tuple[tuple[float, float, float], tuple[float, float]]:
        """
        Calculate center position and end joint for an angled limb segment.

        Used for arm segments that extend at an angle from a joint.

        Args:
            joint_x: X position of the starting joint (absolute, unsigned).
            joint_y: Y position of the starting joint.
            segment_length: Length of the limb segment.
            angle_rad: Angle in radians from vertical.
            x_sign: 1 for left side, -1 for right side.

        Returns:
            Tuple of:
                - center: (x, y, z) position for cylinder center
                - end_joint: (x, y) position of the ending joint
        """
        # Calculate offset from joint to segment center
        half_length = segment_length / 2
        offset_x = math.cos(angle_rad) * half_length
        offset_y = math.sin(angle_rad) * half_length

        # Segment center position
        center = (
            x_sign * (joint_x + offset_x),
            joint_y - offset_y,
            0.0,
        )

        # End joint position (for connecting next segment)
        end_joint_x = joint_x + math.cos(angle_rad) * segment_length
        end_joint_y = joint_y - math.sin(angle_rad) * segment_length

        return center, (end_joint_x, end_joint_y)

    def _calculate_hand_position(
        self,
        wrist_x: float,
        wrist_y: float,
        hand_length: float,
        angle_rad: float,
        x_sign: int,
    ) -> tuple[float, float, float]:
        """
        Calculate center position for hand box.

        Args:
            wrist_x: X position of wrist joint (absolute, unsigned).
            wrist_y: Y position of wrist joint.
            hand_length: Length of hand.
            angle_rad: Arm angle in radians.
            x_sign: 1 for left side, -1 for right side.

        Returns:
            (x, y, z) center position for hand box.
        """
        half_length = hand_length / 2
        offset_x = math.cos(angle_rad) * half_length
        offset_y = math.sin(angle_rad) * half_length

        return (
            x_sign * (wrist_x + offset_x),
            wrist_y - offset_y,
            0.0,
        )

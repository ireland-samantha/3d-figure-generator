"""
Built-in figure presets based on classical figure drawing proportions.

This module defines pre-configured body proportions for common figure types.
The proportions are based on established figure drawing standards where the
head is used as the unit of measurement.

Anatomical Basis:
    These presets draw from classical figure drawing traditions established
    by artists like Andrew Loomis, Burne Hogarth, and George Bridgman.

    - Adult figures: 7.5-8 head units tall (idealized proportions)
    - Children (6-8 years): ~6 head units tall
    - Heroic/idealized: 8.5 head units (superhero proportions)

Landmark References:
    Key anatomical landmarks as fractions of total height:
    - Shoulders: ~7/8 of total height
    - Bust/nipple line: ~6.5/8 of total height
    - Waist/navel: ~5.5/8 of total height
    - Pelvis/hip: ~4/8 of total height (halfway point)
    - Crotch: ~3.5/8 of total height
    - Knee: ~2/8 of total height

Measurement Units:
    All measurements use the head as the base unit:
    - head_radius: 0.5 (head diameter = 1.0 unit)
    - total_heads: Total figure height in head units
    - All body part dimensions scale proportionally

Usage:
    >>> from figure_generator.presets import PRESETS, POSES
    >>> female_config = PRESETS["female_adult"]
    >>> arm_angle = POSES["apose"]  # 45 degrees
"""

from typing import Any

# =============================================================================
# Pose Definitions
# =============================================================================

# Arm pose angles measured in degrees from vertical (Y-axis)
# These standard poses are used in 3D character workflows:
POSES: dict[str, float] = {
    # A-pose: Arms at 45 degrees, the ideal pose for digital sculpting.
    # Provides good shoulder definition while avoiding armpit mesh issues.
    "apose": 45.0,
    # T-pose: Arms horizontal (90 degrees), the standard rigging pose.
    # Essential for skeletal rigging and weight painting workflows.
    "tpose": 90.0,
    # Relaxed: Arms mostly down (20 degrees), natural standing position.
    # Good for realistic presentation and final renders.
    "relaxed": 20.0,
}


# =============================================================================
# Figure Presets
# =============================================================================

# Built-in figure presets as raw dictionaries.
# These are converted to FigureConfig objects by the generator when needed.
#
# Each preset defines:
#   - Basic metrics (total_heads, head_radius, subdivisions)
#   - Body segments (neck, ribcage, abdomen, pelvis)
#   - Optional features (breasts, glutes)
#   - Limb dimensions (upper_arm, forearm, hand, thigh, calf, foot)
#   - Width parameters (shoulder_width, hip_width)
#   - Anatomical landmarks (Y-positions for key body points)

PRESETS: dict[str, dict[str, Any]] = {
    # =========================================================================
    # Female Adult - 7.5 heads tall
    # =========================================================================
    # Based on classical female proportions with:
    # - Narrower shoulders relative to hips
    # - Higher waist position
    # - Wider hip structure
    # - Defined bust
    "female_adult": {
        "name": "Adult Female",
        "total_heads": 7.5,  # Standard female proportion
        "head_radius": 0.5,  # Head diameter = 1.0 unit
        "subdivisions": 2,  # Mesh smoothness (2 = 162 verts per sphere)
        # Neck: Slightly narrower than male, shorter
        "neck": {"radius": 0.11, "length": 0.35},
        # Torso: Narrower ribcage, defined waist, wider pelvis
        "ribcage": {"width": 1.05, "height": 1.25, "depth": 0.55},
        "breasts": {
            "radius": 0.18,
            "offset_x": 0.22,  # Distance from center
            "offset_z": 0.32,  # Forward projection
            "offset_y": -0.1,  # Slight downward offset
        },
        "abdomen": {"radius": 0.30, "length": 0.55},
        "pelvis": {"width": 1.1, "height": 0.7, "depth": 0.5},
        "glutes": {
            "radius": 0.24,
            "offset_x": 0.2,
            "offset_y": -0.15,
            "offset_z": -0.22,  # Posterior projection
        },
        # Arms: Slimmer than male proportions
        "upper_arm": {"radius": 0.105, "length": 1.15},
        "forearm": {"radius": 0.08, "length": 1.0},
        "hand": {"width": 0.09, "length": 0.32, "depth": 0.04},
        # Legs: Slightly longer relative to torso
        "thigh": {"radius": 0.17, "length": 1.75},
        "calf": {"radius": 0.12, "length": 1.7},
        "foot": {"width": 0.14, "height": 0.1, "length": 0.38},
        # Joint positions: Distance from body center
        "shoulder_width": 0.55,  # Narrower than male
        "hip_width": 0.28,
        # Anatomical landmarks (Y-positions from ground)
        "landmarks": {
            "shoulder_y": 5.9,  # Top of shoulder
            "bust_y": 5.4,  # Nipple line
            "waist_y": 4.6,  # Narrowest torso point
            "pelvis_y": 4.0,  # Hip bone level
            "crotch_y": 3.65,  # Base of torso
            "knee_y": 1.9,  # Knee joint center
        },
    },
    # =========================================================================
    # Male Adult - 8 heads tall
    # =========================================================================
    # Based on classical male proportions with:
    # - Broader shoulders relative to hips
    # - Lower waist position
    # - Narrower hip structure
    # - No bust definition
    "male_adult": {
        "name": "Adult Male",
        "total_heads": 8.0,  # Standard idealized male proportion
        "head_radius": 0.5,
        "subdivisions": 2,
        # Neck: Thicker than female
        "neck": {"radius": 0.14, "length": 0.35},
        # Torso: Wider ribcage, less defined waist
        "ribcage": {"width": 1.25, "height": 1.35, "depth": 0.6},
        "breasts": None,  # No breast geometry
        "abdomen": {"radius": 0.38, "length": 0.55},
        "pelvis": {"width": 0.95, "height": 0.65, "depth": 0.48},
        "glutes": {
            "radius": 0.2,
            "offset_x": 0.18,
            "offset_y": -0.15,
            "offset_z": -0.2,
        },
        # Arms: More muscular proportions
        "upper_arm": {"radius": 0.13, "length": 1.25},
        "forearm": {"radius": 0.095, "length": 1.1},
        "hand": {"width": 0.11, "length": 0.38, "depth": 0.05},
        # Legs: Proportionally shorter relative to torso
        "thigh": {"radius": 0.18, "length": 1.85},
        "calf": {"radius": 0.13, "length": 1.8},
        "foot": {"width": 0.16, "height": 0.12, "length": 0.42},
        # Joint positions
        "shoulder_width": 0.65,  # Broader than female
        "hip_width": 0.26,  # Narrower than female
        # Anatomical landmarks
        "landmarks": {
            "shoulder_y": 6.3,
            "bust_y": 5.8,  # Pectoral line
            "waist_y": 4.9,
            "pelvis_y": 4.2,
            "crotch_y": 3.85,
            "knee_y": 2.0,
        },
    },
    # =========================================================================
    # Child (6-8 years) - 6 heads tall
    # =========================================================================
    # Child proportions differ significantly from adults:
    # - Larger head relative to body
    # - Shorter limbs
    # - Less defined gender characteristics
    # - Higher waist position
    # - Rounder, softer forms
    "child": {
        "name": "Child (6-8 years)",
        "total_heads": 6.0,  # Children have proportionally larger heads
        "head_radius": 0.55,  # Slightly larger head
        "subdivisions": 2,
        # Neck: Thinner and shorter
        "neck": {"radius": 0.09, "length": 0.25},
        # Torso: More cylindrical, less defined
        "ribcage": {"width": 0.85, "height": 0.9, "depth": 0.45},
        "breasts": None,
        "abdomen": {"radius": 0.28, "length": 0.45},
        "pelvis": {"width": 0.75, "height": 0.5, "depth": 0.4},
        "glutes": {
            "radius": 0.16,
            "offset_x": 0.14,
            "offset_y": -0.1,
            "offset_z": -0.15,
        },
        # Arms: Shorter, less defined musculature
        "upper_arm": {"radius": 0.07, "length": 0.8},
        "forearm": {"radius": 0.055, "length": 0.7},
        "hand": {"width": 0.07, "length": 0.22, "depth": 0.03},
        # Legs: Proportionally shorter
        "thigh": {"radius": 0.11, "length": 1.1},
        "calf": {"radius": 0.08, "length": 1.0},
        "foot": {"width": 0.1, "height": 0.08, "length": 0.28},
        # Joint positions: Narrower overall
        "shoulder_width": 0.45,
        "hip_width": 0.2,
        # Anatomical landmarks (scaled to 6-head proportion)
        "landmarks": {
            "shoulder_y": 4.7,
            "bust_y": 4.3,
            "waist_y": 3.7,
            "pelvis_y": 3.3,
            "crotch_y": 3.0,
            "knee_y": 1.5,
        },
    },
    # =========================================================================
    # Heroic/Idealized - 8.5 heads tall
    # =========================================================================
    # Exaggerated proportions commonly used in:
    # - Comic book art
    # - Video game characters
    # - Fantasy/superhero designs
    #
    # Features:
    # - Extra-tall stature
    # - Broader shoulders
    # - More muscular build
    # - Longer legs
    "heroic": {
        "name": "Heroic/Idealized (8.5 heads)",
        "total_heads": 8.5,  # Taller than natural proportions
        "head_radius": 0.5,
        "subdivisions": 2,
        # Neck: Thick and powerful
        "neck": {"radius": 0.15, "length": 0.4},
        # Torso: Exaggerated V-taper
        "ribcage": {"width": 1.4, "height": 1.45, "depth": 0.65},
        "breasts": None,
        "abdomen": {"radius": 0.42, "length": 0.6},
        "pelvis": {"width": 1.0, "height": 0.7, "depth": 0.5},
        "glutes": {
            "radius": 0.22,
            "offset_x": 0.2,
            "offset_y": -0.15,
            "offset_z": -0.22,
        },
        # Arms: Heroic musculature
        "upper_arm": {"radius": 0.15, "length": 1.35},
        "forearm": {"radius": 0.11, "length": 1.2},
        "hand": {"width": 0.12, "length": 0.4, "depth": 0.05},
        # Legs: Long and powerful
        "thigh": {"radius": 0.2, "length": 2.0},
        "calf": {"radius": 0.14, "length": 1.9},
        "foot": {"width": 0.17, "height": 0.13, "length": 0.45},
        # Joint positions: Exaggerated width
        "shoulder_width": 0.75,
        "hip_width": 0.28,
        # Anatomical landmarks
        "landmarks": {
            "shoulder_y": 6.7,
            "bust_y": 6.1,
            "waist_y": 5.2,
            "pelvis_y": 4.5,
            "crotch_y": 4.1,
            "knee_y": 2.1,
        },
    },
}


# =============================================================================
# Utility Functions
# =============================================================================


def get_preset_names() -> list[str]:
    """
    Return list of available preset names.

    Returns:
        List of preset name strings that can be passed to FigureGenerator.

    Example:
        >>> presets = get_preset_names()
        >>> print(presets)
        ['female_adult', 'male_adult', 'child', 'heroic']
    """
    return list(PRESETS.keys())


def get_pose_names() -> list[str]:
    """
    Return list of available pose names.

    Returns:
        List of pose name strings with their corresponding arm angles.

    Example:
        >>> poses = get_pose_names()
        >>> print(poses)
        ['apose', 'tpose', 'relaxed']
    """
    return list(POSES.keys())

"""
Built-in presets for common figure types.

Presets are based on classical figure drawing proportions:
- Adult figures: 7.5-8 head units tall
- Children: 5-6 head units tall

All measurements use the head as the base unit (head_radius = 0.5).
"""

from typing import Dict, Any

# Arm pose angles (degrees from vertical)
POSES: Dict[str, float] = {
    "apose": 45.0,    # A-pose: arms 45° down - ideal for sculpting
    "tpose": 90.0,    # T-pose: arms horizontal - ideal for rigging
    "relaxed": 20.0,  # Relaxed: arms mostly down
}

# Built-in figure presets as raw dictionaries
# These are converted to FigureConfig objects when needed
PRESETS: Dict[str, Dict[str, Any]] = {
    "female_adult": {
        "name": "Adult Female",
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
    },
    
    "male_adult": {
        "name": "Adult Male",
        "total_heads": 8.0,
        "head_radius": 0.5,
        "subdivisions": 2,
        
        "neck": {"radius": 0.14, "length": 0.35},
        
        "ribcage": {"width": 1.25, "height": 1.35, "depth": 0.6},
        "breasts": None,
        "abdomen": {"radius": 0.38, "length": 0.55},
        "pelvis": {"width": 0.95, "height": 0.65, "depth": 0.48},
        "glutes": {"radius": 0.2, "offset_x": 0.18, "offset_y": -0.15, "offset_z": -0.2},
        
        "upper_arm": {"radius": 0.13, "length": 1.25},
        "forearm": {"radius": 0.095, "length": 1.1},
        "hand": {"width": 0.11, "length": 0.38, "depth": 0.05},
        
        "thigh": {"radius": 0.18, "length": 1.85},
        "calf": {"radius": 0.13, "length": 1.8},
        "foot": {"width": 0.16, "height": 0.12, "length": 0.42},
        
        "shoulder_width": 0.65,
        "hip_width": 0.26,
        
        "landmarks": {
            "shoulder_y": 6.3,
            "bust_y": 5.8,
            "waist_y": 4.9,
            "pelvis_y": 4.2,
            "crotch_y": 3.85,
            "knee_y": 2.0,
        },
    },
    
    "child": {
        "name": "Child (6-8 years)",
        "total_heads": 6.0,
        "head_radius": 0.55,
        "subdivisions": 2,
        
        "neck": {"radius": 0.09, "length": 0.25},
        
        "ribcage": {"width": 0.85, "height": 0.9, "depth": 0.45},
        "breasts": None,
        "abdomen": {"radius": 0.28, "length": 0.45},
        "pelvis": {"width": 0.75, "height": 0.5, "depth": 0.4},
        "glutes": {"radius": 0.16, "offset_x": 0.14, "offset_y": -0.1, "offset_z": -0.15},
        
        "upper_arm": {"radius": 0.07, "length": 0.8},
        "forearm": {"radius": 0.055, "length": 0.7},
        "hand": {"width": 0.07, "length": 0.22, "depth": 0.03},
        
        "thigh": {"radius": 0.11, "length": 1.1},
        "calf": {"radius": 0.08, "length": 1.0},
        "foot": {"width": 0.1, "height": 0.08, "length": 0.28},
        
        "shoulder_width": 0.45,
        "hip_width": 0.2,
        
        "landmarks": {
            "shoulder_y": 4.7,
            "bust_y": 4.3,
            "waist_y": 3.7,
            "pelvis_y": 3.3,
            "crotch_y": 3.0,
            "knee_y": 1.5,
        },
    },
    
    "heroic": {
        "name": "Heroic/Idealized (8.5 heads)",
        "total_heads": 8.5,
        "head_radius": 0.5,
        "subdivisions": 2,
        
        "neck": {"radius": 0.15, "length": 0.4},
        
        "ribcage": {"width": 1.4, "height": 1.45, "depth": 0.65},
        "breasts": None,
        "abdomen": {"radius": 0.42, "length": 0.6},
        "pelvis": {"width": 1.0, "height": 0.7, "depth": 0.5},
        "glutes": {"radius": 0.22, "offset_x": 0.2, "offset_y": -0.15, "offset_z": -0.22},
        
        "upper_arm": {"radius": 0.15, "length": 1.35},
        "forearm": {"radius": 0.11, "length": 1.2},
        "hand": {"width": 0.12, "length": 0.4, "depth": 0.05},
        
        "thigh": {"radius": 0.2, "length": 2.0},
        "calf": {"radius": 0.14, "length": 1.9},
        "foot": {"width": 0.17, "height": 0.13, "length": 0.45},
        
        "shoulder_width": 0.75,
        "hip_width": 0.28,
        
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


def get_preset_names() -> list:
    """Return list of available preset names."""
    return list(PRESETS.keys())


def get_pose_names() -> list:
    """Return list of available pose names."""
    return list(POSES.keys())

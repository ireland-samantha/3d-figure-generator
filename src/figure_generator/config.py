"""
Configuration management for figure generation.

This module provides dataclasses for type-safe configuration
and utilities for loading/saving JSON configs.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional, Dict, Any, Union


@dataclass
class BodyPartConfig:
    """Configuration for a cylindrical body part."""
    radius: float
    length: float

    def __post_init__(self) -> None:
        if self.radius <= 0:
            raise ValueError(f"radius must be positive, got {self.radius}")
        if self.length <= 0:
            raise ValueError(f"length must be positive, got {self.length}")


@dataclass
class BoxPartConfig:
    """Configuration for a box-shaped body part."""
    width: float
    height: float
    depth: float

    def __post_init__(self) -> None:
        for name, val in [("width", self.width), ("height", self.height), ("depth", self.depth)]:
            if val <= 0:
                raise ValueError(f"{name} must be positive, got {val}")


@dataclass
class SpherePartConfig:
    """Configuration for a spherical body part with offset positioning."""
    radius: float
    offset_x: float = 0.0
    offset_y: float = 0.0
    offset_z: float = 0.0

    def __post_init__(self) -> None:
        if self.radius <= 0:
            raise ValueError(f"radius must be positive, got {self.radius}")


@dataclass
class FootConfig:
    """Configuration for foot dimensions."""
    width: float
    height: float
    length: float

    def __post_init__(self) -> None:
        for name, val in [("width", self.width), ("height", self.height), ("length", self.length)]:
            if val <= 0:
                raise ValueError(f"{name} must be positive, got {val}")


@dataclass
class HandConfig:
    """Configuration for hand dimensions."""
    width: float
    length: float
    depth: float

    def __post_init__(self) -> None:
        for name, val in [("width", self.width), ("length", self.length), ("depth", self.depth)]:
            if val <= 0:
                raise ValueError(f"{name} must be positive, got {val}")


@dataclass
class LandmarksConfig:
    """Y-axis positions for anatomical landmarks."""
    shoulder_y: float
    bust_y: float
    waist_y: float
    pelvis_y: float
    crotch_y: float
    knee_y: float

    def __post_init__(self) -> None:
        # Validate landmarks are in descending order (top to bottom)
        order = [self.shoulder_y, self.bust_y, self.waist_y, 
                 self.pelvis_y, self.crotch_y, self.knee_y]
        for i in range(len(order) - 1):
            if order[i] < order[i + 1]:
                raise ValueError("Landmarks must be in descending Y order (top to bottom)")


@dataclass
class FigureConfig:
    """
    Complete configuration for a figure's proportions.
    
    This dataclass defines all parameters needed to generate a figure,
    following classical figure drawing proportions measured in "head units".
    
    Attributes:
        name: Human-readable name for this configuration
        total_heads: Total figure height in head units (typically 7-8)
        head_radius: Radius of the head sphere
        subdivisions: Icosphere subdivision level for spheres
        neck: Neck cylinder configuration
        ribcage: Ribcage box configuration
        breasts: Optional breast spheres (None for male/child figures)
        abdomen: Abdomen cylinder configuration
        pelvis: Pelvis box configuration
        glutes: Glute sphere configuration
        upper_arm: Upper arm cylinder configuration
        forearm: Forearm cylinder configuration
        hand: Hand box configuration
        thigh: Thigh cylinder configuration
        calf: Calf cylinder configuration
        foot: Foot box configuration
        shoulder_width: X offset for shoulder/arm attachment
        hip_width: X offset for hip/leg attachment
        landmarks: Y positions for anatomical landmarks
    """
    name: str
    total_heads: float
    head_radius: float
    subdivisions: int
    
    neck: BodyPartConfig
    ribcage: BoxPartConfig
    abdomen: BodyPartConfig
    pelvis: BoxPartConfig
    glutes: SpherePartConfig
    upper_arm: BodyPartConfig
    forearm: BodyPartConfig
    hand: HandConfig
    thigh: BodyPartConfig
    calf: BodyPartConfig
    foot: FootConfig
    
    shoulder_width: float
    hip_width: float
    landmarks: LandmarksConfig
    
    breasts: Optional[SpherePartConfig] = None

    def __post_init__(self) -> None:
        if self.total_heads <= 0:
            raise ValueError(f"total_heads must be positive, got {self.total_heads}")
        if self.head_radius <= 0:
            raise ValueError(f"head_radius must be positive, got {self.head_radius}")
        if self.subdivisions < 0:
            raise ValueError(f"subdivisions must be non-negative, got {self.subdivisions}")
        if self.shoulder_width <= 0:
            raise ValueError(f"shoulder_width must be positive, got {self.shoulder_width}")
        if self.hip_width <= 0:
            raise ValueError(f"hip_width must be positive, got {self.hip_width}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary for JSON serialization."""
        result = asdict(self)
        # Remove None values
        if result.get("breasts") is None:
            del result["breasts"]
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FigureConfig":
        """
        Create FigureConfig from a dictionary.
        
        Args:
            data: Dictionary with configuration values
            
        Returns:
            FigureConfig instance
            
        Raises:
            ValueError: If required fields are missing or invalid
            KeyError: If required fields are missing
        """
        # Convert nested dicts to dataclasses
        return cls(
            name=data["name"],
            total_heads=data["total_heads"],
            head_radius=data["head_radius"],
            subdivisions=data.get("subdivisions", 2),
            neck=BodyPartConfig(**data["neck"]),
            ribcage=BoxPartConfig(**data["ribcage"]),
            breasts=SpherePartConfig(**data["breasts"]) if data.get("breasts") else None,
            abdomen=BodyPartConfig(**data["abdomen"]),
            pelvis=BoxPartConfig(**data["pelvis"]),
            glutes=SpherePartConfig(**data["glutes"]),
            upper_arm=BodyPartConfig(**data["upper_arm"]),
            forearm=BodyPartConfig(**data["forearm"]),
            hand=HandConfig(**data["hand"]),
            thigh=BodyPartConfig(**data["thigh"]),
            calf=BodyPartConfig(**data["calf"]),
            foot=FootConfig(**data["foot"]),
            shoulder_width=data["shoulder_width"],
            hip_width=data["hip_width"],
            landmarks=LandmarksConfig(**data["landmarks"]),
        )


def load_config(path: Union[str, Path]) -> FigureConfig:
    """
    Load configuration from a JSON file.
    
    Args:
        path: Path to JSON configuration file
        
    Returns:
        FigureConfig instance
        
    Raises:
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If file contains invalid JSON
        ValueError: If configuration is invalid
    """
    path = Path(path)
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return FigureConfig.from_dict(data)


def save_config(config: FigureConfig, path: Union[str, Path]) -> None:
    """
    Save configuration to a JSON file.
    
    Args:
        config: FigureConfig instance to save
        path: Output file path
    """
    path = Path(path)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(config.to_dict(), f, indent=2)

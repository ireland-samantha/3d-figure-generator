"""
Figure generator core logic.

This module contains the FigureGenerator class which orchestrates
the creation of anatomically-proportioned figure meshes.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple, Dict, Any
import math

from figure_generator.config import FigureConfig
from figure_generator.backends import MeshBackend, MeshData, create_backend
from figure_generator.presets import PRESETS


@dataclass
class GeneratedFigure:
    """
    Container for a generated figure.
    
    Attributes:
        meshes: List of MeshData objects for each body part
        config: The FigureConfig used to generate the figure
        arm_angle: The arm angle used (degrees from vertical)
    """
    meshes: List[MeshData]
    config: FigureConfig
    arm_angle: float
    
    @property
    def part_names(self) -> List[str]:
        """Return list of body part names."""
        return [m.name for m in self.meshes]
    
    @property
    def part_count(self) -> int:
        """Return number of body parts."""
        return len(self.meshes)


class FigureGenerator:
    """
    Generator for anatomically-proportioned figure meshes.
    
    This class creates 3D primitive meshes (spheres, cylinders, boxes)
    arranged according to classical figure drawing proportions.
    
    The generator follows the Single Responsibility Principle by
    focusing solely on figure generation logic, delegating mesh
    creation to the backend and configuration to FigureConfig.
    
    Example:
        >>> generator = FigureGenerator()
        >>> figure = generator.generate("female_adult", arm_angle=45)
        >>> generator.export(figure, "output.glb")
    """
    
    def __init__(self, backend: Optional[MeshBackend] = None):
        """
        Initialize the generator.
        
        Args:
            backend: MeshBackend instance. If None, auto-selects best available.
        """
        self._backend = backend or create_backend()
    
    @property
    def backend_name(self) -> str:
        """Return the name of the active backend."""
        return self._backend.name
    
    @property
    def supported_formats(self) -> List[str]:
        """Return list of supported export formats."""
        return self._backend.get_supported_formats()
    
    def generate(
        self,
        config: FigureConfig | str | Dict[str, Any],
        arm_angle: float = 45.0
    ) -> GeneratedFigure:
        """
        Generate a figure from configuration.
        
        Args:
            config: FigureConfig instance, preset name string, or config dict
            arm_angle: Arm angle in degrees from vertical
                      (0=down, 45=A-pose, 90=T-pose)
        
        Returns:
            GeneratedFigure containing all body part meshes
            
        Raises:
            ValueError: If preset name is invalid
            TypeError: If config type is not supported
        """
        # Resolve config
        if isinstance(config, str):
            if config not in PRESETS:
                raise ValueError(
                    f"Unknown preset '{config}'. "
                    f"Available: {list(PRESETS.keys())}"
                )
            config = FigureConfig.from_dict(PRESETS[config])
        elif isinstance(config, dict):
            config = FigureConfig.from_dict(config)
        elif not isinstance(config, FigureConfig):
            raise TypeError(
                f"config must be FigureConfig, str, or dict, got {type(config)}"
            )
        
        meshes = self._generate_meshes(config, arm_angle)
        return GeneratedFigure(meshes=meshes, config=config, arm_angle=arm_angle)
    
    def export(
        self,
        figure: GeneratedFigure,
        filepath: str,
        file_format: Optional[str] = None
    ) -> None:
        """
        Export a generated figure to file.
        
        Args:
            figure: GeneratedFigure to export
            filepath: Output file path
            file_format: Optional format override (inferred from extension if None)
        """
        self._backend.export(figure.meshes, filepath, file_format)
    
    def _generate_meshes(
        self,
        config: FigureConfig,
        arm_angle: float
    ) -> List[MeshData]:
        """Generate all body part meshes from config."""
        meshes: List[MeshData] = []
        
        landmarks = config.landmarks
        subdivisions = config.subdivisions
        
        # === HEAD ===
        head_y = config.total_heads - config.head_radius
        head = self._backend.create_sphere(
            config.head_radius,
            (0, head_y, 0),
            subdivisions
        )
        head.name = "Head"
        meshes.append(head)
        
        # === NECK ===
        neck_y = head_y - config.head_radius - config.neck.length / 2
        neck = self._backend.create_cylinder(
            config.neck.radius,
            config.neck.length,
            (0, neck_y, 0),
            rotation_degrees=(90, 0, 0)  # Vertical
        )
        neck.name = "Neck"
        meshes.append(neck)
        
        # === RIBCAGE ===
        ribcage_y = landmarks.shoulder_y - config.ribcage.height / 2 + 0.4
        ribcage = self._backend.create_box(
            (config.ribcage.width, config.ribcage.height, config.ribcage.depth),
            (0, ribcage_y, 0)
        )
        ribcage.name = "Ribcage"
        meshes.append(ribcage)
        
        # === BREASTS (optional) ===
        if config.breasts is not None:
            breast_y = landmarks.bust_y
            
            breast_left = self._backend.create_sphere(
                config.breasts.radius,
                (config.breasts.offset_x, breast_y, config.breasts.offset_z),
                subdivisions
            )
            breast_left.name = "Breast_Left"
            meshes.append(breast_left)
            
            breast_right = self._backend.create_sphere(
                config.breasts.radius,
                (-config.breasts.offset_x, breast_y, config.breasts.offset_z),
                subdivisions
            )
            breast_right.name = "Breast_Right"
            meshes.append(breast_right)
        
        # === ABDOMEN ===
        abdomen = self._backend.create_cylinder(
            config.abdomen.radius,
            config.abdomen.length,
            (0, landmarks.waist_y, 0),
            rotation_degrees=(90, 0, 0)
        )
        abdomen.name = "Abdomen"
        meshes.append(abdomen)
        
        # === PELVIS ===
        pelvis = self._backend.create_box(
            (config.pelvis.width, config.pelvis.height, config.pelvis.depth),
            (0, landmarks.pelvis_y, 0)
        )
        pelvis.name = "Pelvis"
        meshes.append(pelvis)
        
        # === GLUTES ===
        glute_y = landmarks.pelvis_y + config.glutes.offset_y
        
        glute_left = self._backend.create_sphere(
            config.glutes.radius,
            (config.glutes.offset_x, glute_y, config.glutes.offset_z),
            subdivisions
        )
        glute_left.name = "Glute_Left"
        meshes.append(glute_left)
        
        glute_right = self._backend.create_sphere(
            config.glutes.radius,
            (-config.glutes.offset_x, glute_y, config.glutes.offset_z),
            subdivisions
        )
        glute_right.name = "Glute_Right"
        meshes.append(glute_right)
        
        # === ARMS ===
        arm_meshes = self._generate_arms(config, arm_angle, subdivisions)
        meshes.extend(arm_meshes)
        
        # === LEGS ===
        leg_meshes = self._generate_legs(config, subdivisions)
        meshes.extend(leg_meshes)
        
        return meshes
    
    def _generate_arms(
        self,
        config: FigureConfig,
        arm_angle: float,
        subdivisions: int
    ) -> List[MeshData]:
        """Generate arm meshes for both sides."""
        meshes = []
        
        shoulder_x = config.shoulder_width
        shoulder_y = config.landmarks.shoulder_y
        
        angle_rad = math.radians(arm_angle)
        
        for side, sign in [("Left", 1), ("Right", -1)]:
            # Upper arm
            ua_offset_x = math.cos(angle_rad) * config.upper_arm.length / 2
            ua_offset_y = math.sin(angle_rad) * config.upper_arm.length / 2
            
            ua_center = (
                sign * (shoulder_x + ua_offset_x),
                shoulder_y - ua_offset_y,
                0
            )
            
            upper_arm = self._backend.create_cylinder(
                config.upper_arm.radius,
                config.upper_arm.length,
                ua_center,
                rotation_degrees=(90, 0, sign * arm_angle)
            )
            upper_arm.name = f"UpperArm_{side}"
            meshes.append(upper_arm)
            
            # Elbow position
            elbow_x = shoulder_x + math.cos(angle_rad) * config.upper_arm.length
            elbow_y = shoulder_y - math.sin(angle_rad) * config.upper_arm.length
            
            # Forearm
            fa_offset_x = math.cos(angle_rad) * config.forearm.length / 2
            fa_offset_y = math.sin(angle_rad) * config.forearm.length / 2
            
            fa_center = (
                sign * (elbow_x + fa_offset_x),
                elbow_y - fa_offset_y,
                0
            )
            
            forearm = self._backend.create_cylinder(
                config.forearm.radius,
                config.forearm.length,
                fa_center,
                rotation_degrees=(90, 0, sign * arm_angle)
            )
            forearm.name = f"Forearm_{side}"
            meshes.append(forearm)
            
            # Wrist position
            wrist_x = elbow_x + math.cos(angle_rad) * config.forearm.length
            wrist_y = elbow_y - math.sin(angle_rad) * config.forearm.length
            
            # Hand
            hand_offset_x = math.cos(angle_rad) * config.hand.length / 2
            hand_offset_y = math.sin(angle_rad) * config.hand.length / 2
            
            hand_center = (
                sign * (wrist_x + hand_offset_x),
                wrist_y - hand_offset_y,
                0
            )
            
            hand = self._backend.create_box(
                (config.hand.width, config.hand.length, config.hand.depth),
                hand_center,
                rotation_degrees=(0, 0, sign * arm_angle)
            )
            hand.name = f"Hand_{side}"
            meshes.append(hand)
        
        return meshes
    
    def _generate_legs(
        self,
        config: FigureConfig,
        subdivisions: int
    ) -> List[MeshData]:
        """Generate leg meshes for both sides."""
        meshes = []
        
        hip_x = config.hip_width
        crotch_y = config.landmarks.crotch_y
        
        for side, sign in [("Left", 1), ("Right", -1)]:
            # Thigh
            thigh_center = (
                sign * hip_x,
                crotch_y - config.thigh.length / 2,
                0
            )
            
            thigh = self._backend.create_cylinder(
                config.thigh.radius,
                config.thigh.length,
                thigh_center,
                rotation_degrees=(90, 0, 0)
            )
            thigh.name = f"Thigh_{side}"
            meshes.append(thigh)
            
            # Knee position
            knee_y = crotch_y - config.thigh.length
            
            # Calf
            calf_center = (
                sign * hip_x,
                knee_y - config.calf.length / 2,
                0
            )
            
            calf = self._backend.create_cylinder(
                config.calf.radius,
                config.calf.length,
                calf_center,
                rotation_degrees=(90, 0, 0)
            )
            calf.name = f"Calf_{side}"
            meshes.append(calf)
            
            # Foot
            foot_center = (
                sign * hip_x,
                config.foot.height / 2,
                config.foot.length / 2 - 0.12
            )
            
            foot = self._backend.create_box(
                (config.foot.width, config.foot.height, config.foot.length),
                foot_center
            )
            foot.name = f"Foot_{side}"
            meshes.append(foot)
        
        return meshes

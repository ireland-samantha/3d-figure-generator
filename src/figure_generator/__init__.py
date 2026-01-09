"""
Figure Generator - Configurable 3D figure primitive meshes for sculpting.

A tool for generating anatomically-proportioned primitive meshes
that serve as base templates for digital sculpting workflows.
"""

__version__ = "1.0.0"
__author__ = "Figure Generator Contributors"

from figure_generator.backends import (
    create_backend,
    get_available_backends,
    is_running_in_blender,
)
from figure_generator.config import FigureConfig, load_config, save_config
from figure_generator.exporters import export_figure, get_supported_formats
from figure_generator.generator import FigureGenerator
from figure_generator.presets import POSES, PRESETS

__all__ = [
    "FigureGenerator",
    "FigureConfig",
    "load_config",
    "save_config",
    "PRESETS",
    "POSES",
    "export_figure",
    "get_supported_formats",
    "is_running_in_blender",
    "get_available_backends",
    "create_backend",
]

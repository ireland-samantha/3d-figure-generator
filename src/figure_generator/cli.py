#!/usr/bin/env python3
"""
Command-line interface for figure-generator.

Usage:
    figure-generator --preset=female_adult --output=figure.glb
    figure-generator --config=my_config.json --pose=tpose --output=figure.obj
    figure-generator --list-presets
    figure-generator --generate-config=female_adult > custom.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

from figure_generator import __version__
from figure_generator.generator import FigureGenerator
from figure_generator.config import FigureConfig, load_config, save_config
from figure_generator.presets import PRESETS, POSES, get_preset_names, get_pose_names
from figure_generator.backends import get_available_backends, create_backend


def create_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(
        prog="figure-generator",
        description="Generate configurable 3D figure primitive meshes for sculpting",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Generate with built-in preset
    %(prog)s --preset=female_adult --output=figure.glb
    
    # Use custom config file
    %(prog)s --config=my_proportions.json --pose=tpose --output=figure.obj
    
    # Generate config file for customization
    %(prog)s --generate-config=female_adult > custom.json
    
    # Use specific backend
    %(prog)s --preset=male_adult --backend=open3d --output=figure.ply
    
    # List available options
    %(prog)s --list-presets
    %(prog)s --list-backends
        """
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}"
    )
    
    # Input options (mutually exclusive)
    input_group = parser.add_argument_group("Input Options")
    input_mutex = input_group.add_mutually_exclusive_group()
    
    input_mutex.add_argument(
        "--preset", "-p",
        type=str,
        choices=get_preset_names(),
        help="Use built-in preset"
    )
    
    input_mutex.add_argument(
        "--config", "-c",
        type=str,
        metavar="FILE",
        help="Path to JSON configuration file"
    )
    
    # Pose options
    pose_group = parser.add_argument_group("Pose Options")
    pose_mutex = pose_group.add_mutually_exclusive_group()
    
    pose_mutex.add_argument(
        "--pose",
        type=str,
        choices=get_pose_names(),
        default="apose",
        help="Arm pose preset (default: apose)"
    )
    
    pose_mutex.add_argument(
        "--arm-angle",
        type=float,
        metavar="DEGREES",
        help="Custom arm angle in degrees (0=down, 90=horizontal)"
    )
    
    # Output options
    output_group = parser.add_argument_group("Output Options")
    
    output_group.add_argument(
        "--output", "-o",
        type=str,
        default="figure.glb",
        metavar="FILE",
        help="Output file path (default: figure.glb)"
    )
    
    output_group.add_argument(
        "--format", "-f",
        type=str,
        metavar="FORMAT",
        help="Output format (inferred from extension if not specified)"
    )
    
    # Get backend choices, filtering out blender (not usable from CLI)
    backend_choices = [b for b in (get_available_backends() or ["trimesh"]) if b != "blender"]
    output_group.add_argument(
        "--backend", "-b",
        type=str,
        choices=backend_choices,
        help="Mesh backend to use (default: auto-select)"
    )
    
    # Info/utility options
    info_group = parser.add_argument_group("Information")
    
    info_group.add_argument(
        "--list-presets",
        action="store_true",
        help="List available presets and exit"
    )
    
    info_group.add_argument(
        "--list-poses",
        action="store_true",
        help="List available poses and exit"
    )
    
    info_group.add_argument(
        "--list-backends",
        action="store_true",
        help="List available backends and their formats"
    )
    
    info_group.add_argument(
        "--generate-config",
        type=str,
        metavar="PRESET",
        help="Output JSON config for a preset (for customization)"
    )
    
    info_group.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )
    
    return parser


def list_presets() -> None:
    """Print available presets."""
    print("Available presets:")
    print("-" * 50)
    for name, preset in PRESETS.items():
        print(f"  {name:15} {preset['name']:25} ({preset['total_heads']} heads)")
    print()


def list_poses() -> None:
    """Print available poses."""
    print("Available poses:")
    print("-" * 50)
    for name, angle in POSES.items():
        desc = {
            "apose": "A-pose, ideal for sculpting",
            "tpose": "T-pose, ideal for rigging",
            "relaxed": "Arms mostly down",
        }.get(name, "")
        print(f"  {name:10} {angle:5.0f}°  {desc}")
    print()


def list_backends() -> None:
    """Print available backends and their formats."""
    print("Available backends:")
    print("-" * 50)

    available = get_available_backends()
    all_backends = ["trimesh", "open3d", "numpy-stl", "blender"]

    for name in all_backends:
        status = "✓" if name in available else "✗"
        if name in available:
            try:
                if name == "blender":
                    # Don't try to instantiate blender backend outside Blender
                    formats = "blend, glb, gltf, fbx, obj, stl, ply, dae, usd"
                    print(f"  {status} {name:12} formats: {formats}")
                    print(f"                    (use via: blender --python blender_script.py)")
                else:
                    b = create_backend(name)
                    formats = ", ".join(b.get_supported_formats())
                    print(f"  {status} {name:12} formats: {formats}")
            except Exception as e:
                print(f"  {status} {name:12} (error: {e})")
        else:
            install_hint = {
                "trimesh": "pip install trimesh",
                "open3d": "pip install open3d",
                "numpy-stl": "pip install numpy-stl",
                "blender": "run inside Blender",
            }.get(name, "")
            print(f"  {status} {name:12} (not installed: {install_hint})")
    print()


def generate_config(preset_name: str) -> int:
    """Output JSON config for a preset."""
    if preset_name not in PRESETS:
        print(f"Error: Unknown preset '{preset_name}'", file=sys.stderr)
        print(f"Available: {', '.join(PRESETS.keys())}", file=sys.stderr)
        return 1
    
    print(json.dumps(PRESETS[preset_name], indent=2))
    return 0


def run_generation(args: argparse.Namespace) -> int:
    """Run the figure generation."""
    # Determine config source
    if args.config:
        config_path = Path(args.config)
        if not config_path.exists():
            print(f"Error: Config file not found: {args.config}", file=sys.stderr)
            return 1
        
        if args.verbose:
            print(f"Loading config: {config_path}")
        
        config = load_config(config_path)
    else:
        preset_name = args.preset or "female_adult"
        if args.verbose:
            print(f"Using preset: {preset_name}")
        config = preset_name  # Generator accepts preset names
    
    # Determine arm angle
    if args.arm_angle is not None:
        arm_angle = args.arm_angle
    else:
        arm_angle = POSES[args.pose]
    
    if args.verbose:
        print(f"Arm angle: {arm_angle}°")
    
    # Create generator with specified backend
    try:
        generator = FigureGenerator(
            backend=create_backend(args.backend) if args.backend else None
        )
    except ImportError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    
    if args.verbose:
        print(f"Backend: {generator.backend_name}")
    
    # Generate figure
    try:
        figure = generator.generate(config, arm_angle=arm_angle)
    except Exception as e:
        print(f"Error generating figure: {e}", file=sys.stderr)
        return 1
    
    # Export
    output_path = args.output
    try:
        generator.export(figure, output_path, args.format)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error exporting: {e}", file=sys.stderr)
        return 1
    
    print(f"Exported {figure.part_count} objects to: {output_path}")
    
    if args.verbose:
        print("\nBody parts:")
        for name in figure.part_names:
            print(f"  - {name}")
    
    return 0


def main(argv: Optional[list] = None) -> int:
    """
    Main entry point for CLI.
    
    Args:
        argv: Command line arguments (defaults to sys.argv[1:])
        
    Returns:
        Exit code (0 for success, non-zero for errors)
    """
    parser = create_parser()
    args = parser.parse_args(argv)
    
    # Handle info commands
    if args.list_presets:
        list_presets()
        return 0
    
    if args.list_poses:
        list_poses()
        return 0
    
    if args.list_backends:
        list_backends()
        return 0
    
    if args.generate_config:
        return generate_config(args.generate_config)
    
    # Run generation
    return run_generation(args)


if __name__ == "__main__":
    sys.exit(main())

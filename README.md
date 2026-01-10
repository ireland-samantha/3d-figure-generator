# Figure Generator

[![CI](https://github.com/ireland-samantha/3d-figure-generator/actions/workflows/ci.yml/badge.svg)](https://github.com/ireland-samantha/3d-figure-generator/actions/workflows/ci.yml)
[![PyPI version](https://img.shields.io/pypi/v/figure-generator.svg)](https://pypi.org/project/figure-generator/)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://github.com/ireland-samantha/3d-figure-generator#docker)

CLI tool for creating anatomically-proportioned base meshes using simple primitives (spheres, cylinders, boxes) that serve as starting points for sculpting in apps like Nomad Sculpt, Blender, ZBrush, and others.

## Features

- **Multiple Presets**: Adult female, adult male, child, and heroic proportions
- **Configurable Poses**: A-pose, T-pose, relaxed, or custom arm angles
- **Accurate Proportions**: Based on classical figure drawing (6-8.5 head units)
- **Fully Customizable**: JSON configuration for every body part dimension
- **Multiple Backends**: trimesh, Open3D, numpy-stl, or Blender
- **Multiple Formats**: GLB, GLTF, OBJ, STL, PLY, FBX, DAE, USD, and more
- **Clean Python API**: Use as a library or CLI tool

## Installation

### From Source

```bash
git clone https://github.com/ireland-samantha/3d-figure-generator.git
cd figure-generator
pip install -e ".[trimesh]"
```

### With Development Dependencies

```bash
pip install -e ".[trimesh,dev]"
```

## Quick Start

### Command Line

```bash
# Generate with default settings (female adult, A-pose, GLB format)
figure-generator --output figure.glb

# Use a different preset and pose
figure-generator --preset male_adult --pose tpose --output male.glb

# Custom arm angle (degrees from vertical: 0=down, 90=horizontal)
figure-generator --preset female_adult --arm-angle 60 --output figure.obj

# List available options
figure-generator --list-presets
figure-generator --list-poses
figure-generator --list-backends

# Generate a config file for customization
figure-generator --generate-config female_adult > my_config.json
# Edit my_config.json, then:
figure-generator --config my_config.json --output custom.glb
```

### Python API

```python
from figure_generator import FigureGenerator

# Simple usage
generator = FigureGenerator()
figure = generator.generate("female_adult", arm_angle=45)
generator.export(figure, "output.glb")

# With custom config
from figure_generator import load_config

config = load_config("my_config.json")
figure = generator.generate(config, arm_angle=90)
generator.export(figure, "output.obj")

# Access individual body parts
for mesh in figure.meshes:
    print(f"{mesh.name}: {len(mesh.vertices)} vertices")
```


## Configuration

Generate a config file to customize proportions:

```bash
figure-generator --generate-config female_adult > config.json
```

Example configuration structure:

```json
{
  "name": "Custom Figure",
  "total_heads": 7.5,
  "head_radius": 0.5,
  "subdivisions": 2,
  "shoulder_width": 0.85,
  "hip_width": 0.45,
  "neck": {"radius": 0.18, "length": 0.35},
  "ribcage": {"width": 1.1, "height": 1.4, "depth": 0.65},
  "breasts": {"radius": 0.28, "offset_x": 0.32, "offset_z": 0.38, "offset_y": 0.0},
  "abdomen": {"radius": 0.38, "length": 0.8},
  "pelvis": {"width": 1.15, "height": 0.65, "depth": 0.55},
  "glutes": {"radius": 0.35, "offset_x": 0.28, "offset_z": -0.25, "offset_y": 0.1},
  "upper_arm": {"radius": 0.12, "length": 1.1},
  "forearm": {"radius": 0.10, "length": 1.0},
  "hand": {"width": 0.22, "length": 0.38, "depth": 0.08},
  "thigh": {"radius": 0.24, "length": 1.5},
  "calf": {"radius": 0.16, "length": 1.45},
  "foot": {"width": 0.25, "length": 0.55, "height": 0.18},
  "landmarks": {
    "shoulder_y": 6.0,
    "bust_y": 5.4,
    "waist_y": 4.5,
    "pelvis_y": 3.7,
    "crotch_y": 3.5
  }
}
```

Set `"breasts": null` for presets without breasts (male, child, heroic).

## Body Parts Generated

Each figure includes these separately-named mesh objects:

| Part | Type | Notes |
|------|------|-------|
| Head | Sphere | |
| Neck | Cylinder | |
| Ribcage | Box | |
| Breast_Left, Breast_Right | Spheres | Female preset only |
| Abdomen | Cylinder | |
| Pelvis | Box | |
| Glute_Left, Glute_Right | Spheres | |
| UpperArm_Left, UpperArm_Right | Cylinders | |
| Forearm_Left, Forearm_Right | Cylinders | |
| Hand_Left, Hand_Right | Boxes | |
| Thigh_Left, Thigh_Right | Cylinders | |
| Calf_Left, Calf_Right | Cylinders | |
| Foot_Left, Foot_Right | Boxes | |

Total: 19-21 objects depending on preset.

## Backends

### Available Backends

| Backend | Install | Formats | Notes |
|---------|---------|---------|-------|
| **trimesh** | `pip install trimesh` | glb, gltf, obj, stl, ply, off, dae | Recommended, most formats |
| **open3d** | `pip install open3d` | obj, stl, ply, off, gltf, glb | Good alternative |
| **numpy-stl** | `pip install numpy-stl` | stl | Lightweight, STL only |
| **blender** | Run inside Blender | blend, glb, gltf, fbx, obj, stl, ply, dae, usd | Use add-on or script |

### Backend Selection

The CLI automatically selects the best available backend (trimesh > open3d > numpy-stl).

Force a specific backend:

```bash
figure-generator --backend trimesh --output figure.glb
```

```python
from figure_generator import FigureGenerator
from figure_generator.backends import create_backend

backend = create_backend("trimesh")
generator = FigureGenerator(backend=backend)
```

When running inside Blender, the blender backend is automatically selected.

## Development

### Setup

```bash
git clone https://github.com/ireland-samantha/3d-figure-generator.git
cd figure-generator
pip install -e ".[trimesh,dev]"
```

### Running Tests

```bash
pytest
pytest --cov=figure_generator  # With coverage
```

### Code Quality

```bash
black src tests           # Format code
isort src tests           # Sort imports
ruff check src tests      # Lint
mypy src                  # Type check
```

## Project Structure

```
figure-generator/
├── src/figure_generator/
│   ├── __init__.py       # Package exports
│   ├── config.py         # Configuration dataclasses and I/O
│   ├── presets.py        # Built-in figure presets
│   ├── backends.py       # Mesh creation backends (trimesh, open3d, numpy-stl, blender)
│   ├── generator.py      # Figure generation logic
│   ├── exporters.py      # Export utilities
│   ├── cli.py            # Command-line interface
│   └── blender_addon.py # Blender add-on (standalone)
├── tests/                # Test suite
├── configs/              # Example configurations
├── pyproject.toml        # Package configuration
└── README.md
```

## License

MIT License - see [LICENSE](LICENSE) for details.

## Acknowledgments

- Proportions based on classical figure drawing techniques (Andrew Loomis, etc.)
- Designed for digital sculptors using Nomad Sculpt, Blender, ZBrush, and similar tools

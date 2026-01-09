# Architecture

This document describes the design and architecture of the Figure Generator project.

## Overview

Figure Generator is a Python library for creating anatomically-proportioned 3D figure meshes. It follows classical figure drawing proportions using the head as the unit of measurement.

## Design Principles

### SOLID Principles

1. **Single Responsibility**: Each module has one clear purpose
   - `config.py`: Data validation and configuration
   - `presets.py`: Preset data only
   - `generator.py`: Figure generation orchestration
   - `backends.py`: Mesh primitive creation
   - `exporters.py`: File export utilities

2. **Open/Closed**: Extensible without modification
   - New backends can be added by implementing `MeshBackend` ABC
   - New presets can be added to `PRESETS` dictionary
   - New export formats supported via backend capabilities

3. **Liskov Substitution**: Backends are interchangeable
   - All backends implement the same `MeshBackend` interface
   - Any backend can be used with any figure configuration

4. **Interface Segregation**: Focused interfaces
   - `MeshBackend` defines only mesh creation methods
   - Configuration classes are separate from generation logic

5. **Dependency Inversion**: Depend on abstractions
   - `FigureGenerator` depends on `MeshBackend` ABC, not concrete implementations
   - Backend selection is handled by factory function

### Clean Code Practices

- **Meaningful Names**: Variables and functions reveal intent
- **Small Functions**: Functions do one thing well
- **No Magic Numbers**: Constants are named and documented
- **DRY**: Common code extracted into utilities
- **Comments**: Explain *why*, code explains *what*

## Module Structure

```
figure_generator/
├── __init__.py          # Public API exports
├── config.py            # Configuration dataclasses
├── presets.py           # Built-in figure presets
├── generator.py         # Figure generation logic
├── backends.py          # Mesh creation backends
├── exporters.py         # Export utilities
├── cli.py               # Command-line interface
└── blender_addon.py     # Blender integration
```

## Data Flow

```
User Input
    │
    ▼
┌─────────────────┐
│  CLI / API      │  Parse arguments, select preset
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ FigureGenerator │  Orchestrate mesh creation
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  FigureConfig   │  Validate and structure config
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  MeshBackend    │  Create primitive meshes
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   MeshData[]    │  Backend-agnostic mesh data
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│    Export       │  Write to file
└─────────────────┘
```

## Key Components

### FigureConfig (config.py)

Validates and structures figure configuration using Python dataclasses.

```python
@dataclass
class FigureConfig:
    total_heads: float      # Figure height in head units
    head_radius: float      # Head radius (usually 0.5)
    neck: BodyPartConfig
    ribcage: BoxPartConfig
    # ... more body parts
    landmarks: LandmarksConfig
```

**Design Decisions:**
- Dataclasses for immutability and type safety
- Validation in `__post_init__` methods
- `from_dict()` / `to_dict()` for serialization

### MeshBackend (backends.py)

Abstract base class defining the mesh creation interface.

```python
class MeshBackend(ABC):
    def create_sphere(...) -> MeshData
    def create_cylinder(...) -> MeshData
    def create_box(...) -> MeshData
    def export(...) -> None
    def get_supported_formats() -> List[str]
```

**Implementations:**
- `TrimeshBackend`: Full-featured, recommended default
- `Open3DBackend`: Alternative with point cloud support
- `NumpySTLBackend`: Lightweight, STL-only
- `BlenderBackend`: Native Blender integration

**Design Decisions:**
- Strategy pattern allows runtime backend selection
- Factory function `create_backend()` handles auto-selection
- Shared geometry utilities reduce code duplication

### FigureGenerator (generator.py)

Orchestrates body part creation using configuration and backend.

```python
class FigureGenerator:
    def generate(config, arm_angle) -> GeneratedFigure
    def export(figure, filepath) -> None
```

**Generation Order:**
1. Head and neck
2. Torso (ribcage, breasts, abdomen)
3. Pelvis and glutes
4. Arms (both sides)
5. Legs (both sides)

**Design Decisions:**
- Single entry point for figure generation
- Body parts generated in anatomical groups
- Paired parts (arms, legs) use helper methods

### Presets (presets.py)

Pre-defined figure proportions based on classical figure drawing.

```python
PRESETS = {
    "female_adult": {...},  # 7.5 heads
    "male_adult": {...},    # 8 heads
    "child": {...},         # 6 heads
    "heroic": {...},        # 8.5 heads
}

POSES = {
    "apose": 45.0,   # Sculpting pose
    "tpose": 90.0,   # Rigging pose
    "relaxed": 20.0, # Natural pose
}
```

**Design Decisions:**
- Raw dictionaries for JSON serialization compatibility
- Converted to `FigureConfig` by generator when needed
- Documented anatomical basis for each measurement

## Coordinate System

- **Y-axis**: Vertical (height), positive is up
- **X-axis**: Lateral (width), positive is figure's left
- **Z-axis**: Depth, positive is forward
- **Origin**: Ground level, centered on figure

Note: Blender uses Z-up. The Blender addon handles conversion.

## Extension Points

### Adding a New Backend

1. Create class inheriting from `MeshBackend`
2. Implement all abstract methods
3. Add to `create_backend()` factory function
4. Add availability check to `get_available_backends()`

### Adding a New Preset

1. Add preset dictionary to `PRESETS` in `presets.py`
2. Follow existing structure with all required keys
3. Document anatomical basis in comments
4. Add tests for the new preset

### Adding a New Body Part

1. Add configuration class to `config.py`
2. Add to `FigureConfig` dataclass
3. Add generation logic to `generator.py`
4. Update presets with new measurements

## Testing Strategy

- **Unit Tests**: Individual function behavior
- **Integration Tests**: Full generation pipeline
- **Mock Tests**: Blender addon (without Blender)
- **Coverage Target**: >80% for core modules

## Dependencies

### Required
- `numpy`: Array operations
- `scipy`: Rotation transforms

### Backend-Specific
- `trimesh`: Default mesh backend
- `open3d`: Alternative backend
- `numpy-stl`: Lightweight STL backend
- `bpy`: Blender backend (Blender environment only)

### Development
- `pytest`: Testing framework
- `black`: Code formatting
- `ruff`: Linting
- `mypy`: Type checking

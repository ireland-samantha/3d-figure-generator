# Contributing to Figure Generator

Thank you for your interest in contributing to Figure Generator! This document provides guidelines and information to help you contribute effectively.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Code Style](#code-style)
- [Architecture Overview](#architecture-overview)
- [Making Changes](#making-changes)
- [Testing](#testing)
- [Submitting Changes](#submitting-changes)
- [Release Process](#release-process)

## Code of Conduct

This project adheres to the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## Getting Started

### Prerequisites

- Python 3.9 or higher
- Git
- (Optional) Blender 3.0+ for Blender addon development

### Development Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/ireland-samantha/3d-figure-generator.git
   cd 3d-figure-generator
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install in development mode with all dependencies:**
   ```bash
   pip install -e ".[dev]"
   ```

4. **Verify installation:**
   ```bash
   pytest
   figure-generator --help
   ```

## Code Style

We follow strict code quality standards to maintain readability and consistency.

### Formatting and Linting

We use the following tools (configured in `pyproject.toml`):

- **Black**: Code formatting (line length: 99)
- **Ruff**: Fast linting and import sorting
- **mypy**: Static type checking

Run all checks before committing:

```bash
# Format code
black src tests

# Lint and fix issues
ruff check --fix src tests

# Type check
mypy src
```

### Naming Conventions

| Element | Convention | Example |
|---------|------------|---------|
| Classes | PascalCase | `FigureGenerator`, `MeshBackend` |
| Functions/Methods | snake_case | `create_sphere`, `generate_figure` |
| Constants | UPPER_SNAKE_CASE | `DEFAULT_SUBDIVISIONS`, `HEAD_RADIUS` |
| Private members | Leading underscore | `_generate_meshes`, `_apply_transform` |
| Type variables | Short PascalCase | `T`, `ConfigT` |

### Docstring Standards

We use Google-style docstrings for all public APIs:

```python
def create_sphere(
    radius: float,
    center: tuple[float, float, float],
    subdivisions: int = 2,
) -> MeshData:
    """Create an icosphere mesh at the specified position.

    Generates a geodesic sphere (icosphere) by subdividing an icosahedron.
    Higher subdivision values produce smoother spheres but increase
    vertex count exponentially.

    Args:
        radius: Sphere radius in scene units.
        center: Position as (x, y, z) coordinates.
        subdivisions: Number of subdivision iterations. Each iteration
            quadruples the face count. Defaults to 2.

    Returns:
        MeshData containing vertices, faces, and optional native object.

    Raises:
        ValueError: If radius is not positive or subdivisions is negative.

    Example:
        >>> backend = TrimeshBackend()
        >>> sphere = backend.create_sphere(1.0, (0, 0, 5))
        >>> len(sphere.vertices)
        42
    """
```

### Type Hints

All code must include type hints:

```python
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from numpy.typing import NDArray

def transform_vertices(
    vertices: NDArray[np.float64],
    matrix: NDArray[np.float64],
) -> NDArray[np.float64]:
    """Apply transformation matrix to vertices."""
    ...
```

### SOLID Principles

We adhere to SOLID principles:

1. **Single Responsibility**: Each class/function should have one reason to change
2. **Open/Closed**: Open for extension, closed for modification
3. **Liskov Substitution**: Subtypes must be substitutable for base types
4. **Interface Segregation**: Prefer small, focused interfaces
5. **Dependency Inversion**: Depend on abstractions, not concretions

### Clean Code Guidelines

- **Meaningful names**: Variables and functions should reveal intent
- **Small functions**: Functions should do one thing and do it well
- **No magic numbers**: Use named constants with explanatory comments
- **DRY**: Don't repeat yourself—extract common logic
- **Comments**: Explain *why*, not *what* (code should be self-documenting)

## Architecture Overview

```
figure_generator/
├── config.py      # Configuration dataclasses with validation
├── presets.py     # Built-in figure presets and poses
├── generator.py   # High-level figure generation orchestration
├── backends.py    # Mesh creation backends (trimesh, numpy-stl, blender)
├── exporters.py   # Export utilities and format handling
├── cli.py         # Command-line interface
└── blender_addon.py  # Blender integration (standalone capable)
```

### Key Design Decisions

1. **Backend Abstraction**: `MeshBackend` ABC allows multiple mesh libraries
2. **Configuration as Data**: Dataclasses with validation for type safety
3. **Coordinate System**: Internal Y-up, Blender uses Z-up (converted in addon)
4. **Preset System**: Dictionary-based for JSON serialization

## Making Changes

### Branch Naming

- `feature/short-description` - New features
- `fix/issue-number-description` - Bug fixes
- `docs/description` - Documentation updates
- `refactor/description` - Code refactoring

### Commit Messages

Follow conventional commits:

```
type(scope): short description

Longer description if needed.

Fixes #123
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

### Adding a New Preset

1. Add preset dictionary to `presets.py`
2. Document anatomical basis in comments
3. Add tests in `test_config.py` and `test_generator.py`
4. Update README preset table

### Adding a New Backend

1. Create class inheriting from `MeshBackend`
2. Implement all abstract methods
3. Register in `_BACKEND_REGISTRY`
4. Add tests in `test_backends.py`
5. Document in README

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=figure_generator --cov-report=term-missing

# Run specific test file
pytest tests/test_generator.py

# Run tests matching pattern
pytest -k "test_sphere"

# Verbose output
pytest -v
```

### Test Requirements

- All new code must have tests
- Maintain or improve coverage percentage
- Test edge cases and error conditions
- Use descriptive test names: `test_create_sphere_with_zero_radius_raises_error`

### Test Structure

```python
class TestClassName:
    """Tests for ClassName functionality."""

    def test_method_does_expected_thing(self):
        """Verify method behavior under normal conditions."""
        # Arrange
        input_value = ...

        # Act
        result = method(input_value)

        # Assert
        assert result == expected

    def test_method_with_invalid_input_raises_error(self):
        """Verify proper error handling for invalid input."""
        with pytest.raises(ValueError, match="specific message"):
            method(invalid_input)
```

## Submitting Changes

### Pull Request Process

1. **Create a feature branch** from `main`
2. **Make your changes** following code style guidelines
3. **Write/update tests** for your changes
4. **Run the full test suite** and ensure it passes
5. **Update documentation** if needed
6. **Create a pull request** with a clear description

### PR Checklist

- [ ] Code follows project style guidelines
- [ ] All tests pass (`pytest`)
- [ ] Type checking passes (`mypy src`)
- [ ] Linting passes (`ruff check src tests`)
- [ ] New code has docstrings
- [ ] README updated if needed
- [ ] CHANGELOG updated for user-facing changes

### Review Process

1. Maintainers will review your PR
2. Address any requested changes
3. Once approved, maintainers will merge

## Release Process

Releases follow semantic versioning (MAJOR.MINOR.PATCH):

- **MAJOR**: Breaking API changes
- **MINOR**: New features, backward compatible
- **PATCH**: Bug fixes, backward compatible

## Questions?

- Open an issue for bugs or feature requests
- Start a discussion for questions or ideas

Thank you for contributing!

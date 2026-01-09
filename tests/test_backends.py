"""Tests for figure_generator.backends module."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from figure_generator.backends import (
    MeshData,
    MeshBackend,
    TrimeshBackend,
    NumpySTLBackend,
    create_backend,
    get_available_backends,
    is_running_in_blender,
)


class TestMeshData:
    """Tests for MeshData dataclass."""
    
    def test_creation(self):
        """Test creating MeshData."""
        import numpy as np
        
        vertices = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0]])
        faces = np.array([[0, 1, 2]])
        
        mesh = MeshData(vertices=vertices, faces=faces, name="test")
        
        assert mesh.name == "test"
        assert len(mesh.vertices) == 3
        assert len(mesh.faces) == 1
    
    def test_default_name(self):
        """Test default name is empty string."""
        import numpy as np
        
        mesh = MeshData(
            vertices=np.array([[0, 0, 0]]),
            faces=np.array([[0, 0, 0]])
        )
        
        assert mesh.name == ""


class TestGetAvailableBackends:
    """Tests for get_available_backends function."""
    
    def test_returns_list(self):
        """Test that function returns a list."""
        backends = get_available_backends()
        assert isinstance(backends, list)
    
    def test_trimesh_available(self):
        """Test that trimesh is available (it's a dependency)."""
        backends = get_available_backends()
        assert "trimesh" in backends


class TestCreateBackend:
    """Tests for create_backend function."""
    
    def test_auto_select(self):
        """Test auto-selecting backend."""
        backend = create_backend()
        assert isinstance(backend, MeshBackend)
    
    def test_select_trimesh(self):
        """Test selecting trimesh backend."""
        backend = create_backend("trimesh")
        assert backend.name == "trimesh"
    
    def test_invalid_backend(self):
        """Test that invalid backend raises error."""
        with pytest.raises((ImportError, ValueError)):
            create_backend("nonexistent_backend")


class TestTrimeshBackend:
    """Tests for TrimeshBackend class."""
    
    @pytest.fixture
    def backend(self):
        """Create TrimeshBackend instance."""
        return TrimeshBackend()
    
    def test_name(self, backend):
        """Test backend name."""
        assert backend.name == "trimesh"
    
    def test_supported_formats(self, backend):
        """Test supported formats."""
        formats = backend.get_supported_formats()
        assert isinstance(formats, list)
        assert "glb" in formats
        assert "obj" in formats
    
    def test_create_sphere(self, backend):
        """Test creating sphere mesh."""
        mesh = backend.create_sphere(
            radius=1.0,
            center=(0, 0, 0),
            subdivisions=2
        )
        
        assert isinstance(mesh, MeshData)
        assert len(mesh.vertices) > 0
        assert len(mesh.faces) > 0
    
    def test_create_sphere_at_position(self, backend):
        """Test creating sphere at specific position."""
        import numpy as np
        
        mesh = backend.create_sphere(
            radius=1.0,
            center=(5, 10, 15),
            subdivisions=1
        )
        
        # Check that vertices are centered around the specified position
        center = np.mean(mesh.vertices, axis=0)
        assert abs(center[0] - 5) < 0.1
        assert abs(center[1] - 10) < 0.1
        assert abs(center[2] - 15) < 0.1
    
    def test_create_cylinder(self, backend):
        """Test creating cylinder mesh."""
        mesh = backend.create_cylinder(
            radius=0.5,
            height=2.0,
            center=(0, 0, 0),
            rotation_degrees=(90, 0, 0)
        )
        
        assert isinstance(mesh, MeshData)
        assert len(mesh.vertices) > 0
        assert len(mesh.faces) > 0
    
    def test_create_cylinder_vertical(self, backend):
        """Test creating vertical cylinder."""
        import numpy as np
        
        mesh = backend.create_cylinder(
            radius=0.5,
            height=2.0,
            center=(0, 1, 0),
            rotation_degrees=(90, 0, 0)  # Rotate to vertical
        )
        
        # Vertical cylinder should have Y extent roughly equal to height
        y_min = mesh.vertices[:, 1].min()
        y_max = mesh.vertices[:, 1].max()
        y_extent = y_max - y_min
        
        assert abs(y_extent - 2.0) < 0.1
    
    def test_create_box(self, backend):
        """Test creating box mesh."""
        mesh = backend.create_box(
            extents=(1.0, 2.0, 0.5),
            center=(0, 0, 0)
        )
        
        assert isinstance(mesh, MeshData)
        assert len(mesh.vertices) == 8  # Box has 8 vertices
        assert len(mesh.faces) == 12    # Box has 12 triangular faces
    
    def test_create_box_dimensions(self, backend):
        """Test box has correct dimensions."""
        import numpy as np
        
        mesh = backend.create_box(
            extents=(2.0, 4.0, 1.0),
            center=(0, 0, 0)
        )
        
        x_extent = mesh.vertices[:, 0].max() - mesh.vertices[:, 0].min()
        y_extent = mesh.vertices[:, 1].max() - mesh.vertices[:, 1].min()
        z_extent = mesh.vertices[:, 2].max() - mesh.vertices[:, 2].min()
        
        assert abs(x_extent - 2.0) < 0.01
        assert abs(y_extent - 4.0) < 0.01
        assert abs(z_extent - 1.0) < 0.01
    
    def test_export_glb(self, backend):
        """Test exporting to GLB format."""
        mesh = backend.create_sphere(1.0, (0, 0, 0))
        mesh.name = "test_sphere"
        
        with tempfile.NamedTemporaryFile(suffix='.glb', delete=False) as f:
            temp_path = Path(f.name)
        
        try:
            backend.export([mesh], str(temp_path))
            assert temp_path.exists()
            assert temp_path.stat().st_size > 0
        finally:
            temp_path.unlink()
    
    def test_export_multiple_meshes(self, backend):
        """Test exporting multiple meshes."""
        meshes = [
            backend.create_sphere(0.5, (0, 0, 0)),
            backend.create_box((1, 1, 1), (2, 0, 0)),
            backend.create_cylinder(0.3, 1.0, (0, 2, 0)),
        ]
        meshes[0].name = "sphere"
        meshes[1].name = "box"
        meshes[2].name = "cylinder"
        
        with tempfile.NamedTemporaryFile(suffix='.glb', delete=False) as f:
            temp_path = Path(f.name)
        
        try:
            backend.export(meshes, str(temp_path))
            assert temp_path.exists()
            assert temp_path.stat().st_size > 0
        finally:
            temp_path.unlink()


class TestBackendConsistency:
    """Tests to ensure backends produce consistent results."""

    def test_sphere_vertex_count_increases_with_subdivisions(self):
        """Test that more subdivisions = more vertices."""
        backend = create_backend()

        mesh_low = backend.create_sphere(1.0, (0, 0, 0), subdivisions=1)
        mesh_high = backend.create_sphere(1.0, (0, 0, 0), subdivisions=3)

        assert len(mesh_high.vertices) > len(mesh_low.vertices)

    def test_cylinder_vertex_count_increases_with_sections(self):
        """Test that more sections = more vertices."""
        backend = create_backend()

        mesh_low = backend.create_cylinder(1.0, 2.0, (0, 0, 0), sections=8)
        mesh_high = backend.create_cylinder(1.0, 2.0, (0, 0, 0), sections=32)

        assert len(mesh_high.vertices) > len(mesh_low.vertices)


class TestIsRunningInBlender:
    """Tests for is_running_in_blender function."""

    def test_returns_bool(self):
        """Test that function returns a boolean."""
        result = is_running_in_blender()
        assert isinstance(result, bool)

    def test_false_outside_blender(self):
        """Test that it returns False when not in Blender."""
        # We're not running in Blender, so this should be False
        assert is_running_in_blender() is False

    @patch('figure_generator.backends._check_available')
    def test_true_when_bpy_available(self, mock_check):
        """Test that it returns True when bpy is available."""
        mock_check.return_value = True
        assert is_running_in_blender() is True
        mock_check.assert_called_with("bpy")


class TestNumpySTLBackend:
    """Tests for NumpySTLBackend class."""

    @pytest.fixture
    def backend(self):
        """Create NumpySTLBackend instance."""
        return NumpySTLBackend()

    def test_name(self, backend):
        """Test backend name."""
        assert backend.name == "numpy-stl"

    def test_supported_formats(self, backend):
        """Test supported formats (STL only)."""
        formats = backend.get_supported_formats()
        assert formats == ["stl"]

    def test_create_sphere(self, backend):
        """Test creating sphere mesh."""
        mesh = backend.create_sphere(
            radius=1.0,
            center=(0, 0, 0),
            subdivisions=2
        )

        assert isinstance(mesh, MeshData)
        assert len(mesh.vertices) > 0
        assert len(mesh.faces) > 0

    def test_create_sphere_at_position(self, backend):
        """Test creating sphere at specific position."""
        mesh = backend.create_sphere(
            radius=1.0,
            center=(5, 10, 15),
            subdivisions=1
        )

        # Check that vertices are centered around the specified position
        center = np.mean(mesh.vertices, axis=0)
        assert abs(center[0] - 5) < 0.5
        assert abs(center[1] - 10) < 0.5
        assert abs(center[2] - 15) < 0.5

    def test_create_cylinder(self, backend):
        """Test creating cylinder mesh."""
        mesh = backend.create_cylinder(
            radius=0.5,
            height=2.0,
            center=(0, 0, 0),
            rotation_degrees=(90, 0, 0)
        )

        assert isinstance(mesh, MeshData)
        assert len(mesh.vertices) > 0
        assert len(mesh.faces) > 0

    def test_create_cylinder_with_rotation(self, backend):
        """Test creating cylinder with rotation."""
        mesh = backend.create_cylinder(
            radius=0.5,
            height=2.0,
            center=(1, 2, 3),
            rotation_degrees=(45, 30, 15),
            sections=12
        )

        assert isinstance(mesh, MeshData)
        assert len(mesh.vertices) > 0

    def test_create_box(self, backend):
        """Test creating box mesh."""
        mesh = backend.create_box(
            extents=(1.0, 2.0, 0.5),
            center=(0, 0, 0)
        )

        assert isinstance(mesh, MeshData)
        assert len(mesh.vertices) == 8  # Box has 8 vertices
        assert len(mesh.faces) == 12    # Box has 12 triangular faces

    def test_create_box_with_rotation(self, backend):
        """Test creating box with rotation."""
        mesh = backend.create_box(
            extents=(2.0, 1.0, 0.5),
            center=(1, 2, 3),
            rotation_degrees=(45, 0, 0)
        )

        assert isinstance(mesh, MeshData)
        assert len(mesh.vertices) == 8

    def test_create_box_dimensions(self, backend):
        """Test box has correct dimensions."""
        mesh = backend.create_box(
            extents=(2.0, 4.0, 1.0),
            center=(0, 0, 0)
        )

        x_extent = mesh.vertices[:, 0].max() - mesh.vertices[:, 0].min()
        y_extent = mesh.vertices[:, 1].max() - mesh.vertices[:, 1].min()
        z_extent = mesh.vertices[:, 2].max() - mesh.vertices[:, 2].min()

        assert abs(x_extent - 2.0) < 0.01
        assert abs(y_extent - 4.0) < 0.01
        assert abs(z_extent - 1.0) < 0.01

    def test_export_stl(self, backend):
        """Test exporting to STL format."""
        mesh = backend.create_sphere(1.0, (0, 0, 0))
        mesh.name = "test_sphere"

        with tempfile.NamedTemporaryFile(suffix='.stl', delete=False) as f:
            temp_path = Path(f.name)

        try:
            backend.export([mesh], str(temp_path))
            assert temp_path.exists()
            assert temp_path.stat().st_size > 0
        finally:
            temp_path.unlink()

    def test_export_multiple_meshes(self, backend):
        """Test exporting multiple meshes."""
        meshes = [
            backend.create_sphere(0.5, (0, 0, 0)),
            backend.create_box((1, 1, 1), (2, 0, 0)),
            backend.create_cylinder(0.3, 1.0, (0, 2, 0)),
        ]
        meshes[0].name = "sphere"
        meshes[1].name = "box"
        meshes[2].name = "cylinder"

        with tempfile.NamedTemporaryFile(suffix='.stl', delete=False) as f:
            temp_path = Path(f.name)

        try:
            backend.export(meshes, str(temp_path))
            assert temp_path.exists()
            assert temp_path.stat().st_size > 0
        finally:
            temp_path.unlink()


class TestCreateBackendWithNumpySTL:
    """Tests for create_backend with numpy-stl."""

    def test_select_numpy_stl(self):
        """Test selecting numpy-stl backend."""
        backend = create_backend("numpy-stl")
        assert backend.name == "numpy-stl"

    def test_numpy_stl_in_available(self):
        """Test that numpy-stl is in available backends."""
        backends = get_available_backends()
        assert "numpy-stl" in backends


class TestTrimeshBackendRotation:
    """Additional tests for TrimeshBackend rotation handling."""

    @pytest.fixture
    def backend(self):
        """Create TrimeshBackend instance."""
        return TrimeshBackend()

    def test_cylinder_no_rotation(self, backend):
        """Test cylinder without rotation."""
        mesh = backend.create_cylinder(
            radius=0.5,
            height=2.0,
            center=(0, 0, 0),
            rotation_degrees=(0, 0, 0)
        )
        assert isinstance(mesh, MeshData)

    def test_box_with_rotation(self, backend):
        """Test box with rotation."""
        mesh = backend.create_box(
            extents=(1.0, 2.0, 0.5),
            center=(0, 0, 0),
            rotation_degrees=(45, 30, 15)
        )
        assert isinstance(mesh, MeshData)
        assert len(mesh.vertices) == 8

    def test_export_without_native(self, backend):
        """Test exporting mesh without native object."""
        # Create MeshData without native
        vertices = np.array([
            [0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0],
            [0, 0, 1], [1, 0, 1], [1, 1, 1], [0, 1, 1]
        ], dtype=float)
        faces = np.array([
            [0, 1, 2], [0, 2, 3],
            [4, 6, 5], [4, 7, 6],
            [0, 4, 5], [0, 5, 1],
            [2, 6, 7], [2, 7, 3],
            [0, 3, 7], [0, 7, 4],
            [1, 5, 6], [1, 6, 2],
        ])
        mesh = MeshData(vertices=vertices, faces=faces, name="test_box")

        with tempfile.NamedTemporaryFile(suffix='.glb', delete=False) as f:
            temp_path = Path(f.name)

        try:
            backend.export([mesh], str(temp_path))
            assert temp_path.exists()
        finally:
            temp_path.unlink()


class TestMeshDataWithNative:
    """Tests for MeshData with native object."""

    def test_native_default_none(self):
        """Test that native defaults to None."""
        mesh = MeshData(
            vertices=np.array([[0, 0, 0]]),
            faces=np.array([[0, 0, 0]])
        )
        assert mesh.native is None

    def test_native_can_be_set(self):
        """Test that native can be set to any object."""
        native_obj = {"test": "object"}
        mesh = MeshData(
            vertices=np.array([[0, 0, 0]]),
            faces=np.array([[0, 0, 0]]),
            native=native_obj
        )
        assert mesh.native == native_obj

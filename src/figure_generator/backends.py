"""
Mesh creation backends for 3D figure generation.

This module provides an abstraction layer for mesh creation, supporting multiple
3D libraries with a unified interface. The backend pattern allows the figure
generator to work with different mesh libraries without modification.

Supported Backends:
    - trimesh: Full-featured mesh library (recommended for most use cases)
    - open3d: Alternative with good point cloud support
    - numpy-stl: Lightweight, STL-only output
    - blender: Native Blender integration (only available inside Blender)

Design Patterns:
    - Strategy Pattern: Each backend implements MeshBackend interface
    - Factory Pattern: create_backend() selects appropriate implementation

Example:
    >>> backend = create_backend()  # Auto-selects best available
    >>> sphere = backend.create_sphere(radius=1.0, center=(0, 0, 5))
    >>> backend.export([sphere], "output.glb")
"""

from __future__ import annotations

import importlib.util
import math
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import numpy as np
    from numpy.typing import NDArray


# =============================================================================
# Constants
# =============================================================================

# Golden ratio - used for icosahedron generation (most uniform sphere subdivision)
GOLDEN_RATIO: float = (1.0 + math.sqrt(5.0)) / 2.0

# Default mesh resolution settings
DEFAULT_SPHERE_SUBDIVISIONS: int = 2
DEFAULT_CYLINDER_SECTIONS: int = 16

# Icosahedron base geometry (normalized to unit sphere)
# These 12 vertices form the starting point for icosphere subdivision
ICOSAHEDRON_VERTICES: list[tuple[float, float, float]] = [
    (-1, GOLDEN_RATIO, 0),
    (1, GOLDEN_RATIO, 0),
    (-1, -GOLDEN_RATIO, 0),
    (1, -GOLDEN_RATIO, 0),
    (0, -1, GOLDEN_RATIO),
    (0, 1, GOLDEN_RATIO),
    (0, -1, -GOLDEN_RATIO),
    (0, 1, -GOLDEN_RATIO),
    (GOLDEN_RATIO, 0, -1),
    (GOLDEN_RATIO, 0, 1),
    (-GOLDEN_RATIO, 0, -1),
    (-GOLDEN_RATIO, 0, 1),
]

# 20 triangular faces of icosahedron (vertex indices)
ICOSAHEDRON_FACES: list[tuple[int, int, int]] = [
    (0, 11, 5),
    (0, 5, 1),
    (0, 1, 7),
    (0, 7, 10),
    (0, 10, 11),
    (1, 5, 9),
    (5, 11, 4),
    (11, 10, 2),
    (10, 7, 6),
    (7, 1, 8),
    (3, 9, 4),
    (3, 4, 2),
    (3, 2, 6),
    (3, 6, 8),
    (3, 8, 9),
    (4, 9, 5),
    (2, 4, 11),
    (6, 2, 10),
    (8, 6, 7),
    (9, 8, 1),
]


# =============================================================================
# Data Classes
# =============================================================================


@dataclass
class MeshData:
    """
    Backend-agnostic container for mesh geometry data.

    Provides a standardized representation of mesh data that can be passed
    between different backends and exported to various formats.

    Attributes:
        vertices: Vertex positions as Nx3 array where each row is (x, y, z).
        faces: Triangle indices as Mx3 array where each row contains
            three vertex indices forming a triangle.
        name: Optional identifier for the mesh part (e.g., "head", "left_arm").
        native: Optional reference to the backend's native mesh object.
            Preserves full fidelity when exporting with the same backend.

    Example:
        >>> mesh = MeshData(
        ...     vertices=np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0]]),
        ...     faces=np.array([[0, 1, 2]]),
        ...     name="triangle"
        ... )
    """

    vertices: Any  # NDArray[np.float64] - Nx3 array of vertex positions
    faces: Any  # NDArray[np.int64] - Mx3 array of triangle face indices
    name: str = ""
    native: Any | None = None


# =============================================================================
# Geometry Utilities
# =============================================================================


def create_rotation_matrix(
    rotation_degrees: tuple[float, float, float],
) -> NDArray[np.float64]:
    """
    Create a 3x3 rotation matrix from Euler angles.

    Uses XYZ rotation order (rotate around X, then Y, then Z).
    This is extracted as a utility to avoid duplicating rotation logic
    across backends and to provide consistent rotation behavior.

    Args:
        rotation_degrees: Rotation angles in degrees as (rx, ry, rz).

    Returns:
        3x3 rotation matrix as numpy array.

    Note:
        Uses scipy.spatial.transform.Rotation for robust quaternion-based
        rotation to avoid gimbal lock issues.
    """
    from scipy.spatial.transform import Rotation

    return Rotation.from_euler("xyz", rotation_degrees, degrees=True).as_matrix()


def apply_transform(
    vertices: NDArray[np.float64],
    rotation_degrees: tuple[float, float, float],
    translation: tuple[float, float, float],
) -> NDArray[np.float64]:
    """
    Apply rotation and translation to a vertex array.

    Rotation is applied first (around origin), then translation.
    This ordering ensures predictable positioning of rotated objects.

    Args:
        vertices: Nx3 array of vertex positions.
        rotation_degrees: Euler angles in degrees as (rx, ry, rz).
        translation: Translation vector as (tx, ty, tz).

    Returns:
        Transformed Nx3 vertex array.

    Example:
        >>> verts = np.array([[1, 0, 0], [0, 1, 0]])
        >>> transformed = apply_transform(verts, (0, 0, 90), (5, 0, 0))
    """
    import numpy as np

    result = vertices.copy()

    # Apply rotation if any angle is non-zero
    if any(angle != 0 for angle in rotation_degrees):
        rotation_matrix = create_rotation_matrix(rotation_degrees)
        result = result @ rotation_matrix.T

    # Apply translation
    result = result + np.array(translation)

    return result


def generate_icosphere_geometry(
    radius: float,
    subdivisions: int = DEFAULT_SPHERE_SUBDIVISIONS,
) -> tuple[NDArray[np.float64], NDArray[np.int64]]:
    """
    Generate icosphere (geodesic sphere) vertices and faces.

    Creates a sphere by recursively subdividing an icosahedron. This produces
    a more uniform vertex distribution than UV spheres, making it ideal for
    sculpting base meshes.

    Algorithm:
        1. Start with icosahedron (12 vertices, 20 faces)
        2. For each subdivision:
           a. Split each edge at midpoint
           b. Project midpoint onto unit sphere
           c. Create 4 triangles from each original triangle
        3. Scale to desired radius

    Vertex/Face count by subdivision level:
        - Level 0: 12 vertices, 20 faces
        - Level 1: 42 vertices, 80 faces
        - Level 2: 162 vertices, 320 faces (default)
        - Level 3: 642 vertices, 1280 faces

    Args:
        radius: Sphere radius in scene units.
        subdivisions: Number of subdivision iterations. Higher values
            produce smoother spheres but increase vertex count by ~4x
            per level.

    Returns:
        Tuple of (vertices, faces) where vertices is Nx3 float array
        and faces is Mx3 integer array.
    """
    import numpy as np

    # Initialize with icosahedron geometry
    vertices = np.array(ICOSAHEDRON_VERTICES, dtype=np.float64)
    faces = np.array(ICOSAHEDRON_FACES, dtype=np.int64)

    # Normalize to unit sphere
    norms = np.linalg.norm(vertices, axis=1, keepdims=True)
    vertices = vertices / norms

    # Subdivide icosahedron
    for _ in range(subdivisions):
        vertices, faces = _subdivide_icosphere(vertices, faces)

    # Scale to desired radius
    vertices = vertices * radius

    return vertices, faces


def _subdivide_icosphere(
    vertices: NDArray[np.float64],
    faces: NDArray[np.int64],
) -> tuple[NDArray[np.float64], NDArray[np.int64]]:
    """
    Perform one subdivision iteration on icosphere geometry.

    Each triangle is split into 4 triangles by adding vertices at
    edge midpoints and projecting them onto the unit sphere.

    Args:
        vertices: Current vertex array (Nx3).
        faces: Current face array (Mx3).

    Returns:
        Tuple of (new_vertices, new_faces) with ~4x more faces.
    """
    import numpy as np

    midpoint_cache: dict[tuple[int, int], int] = {}
    new_faces = []

    for face in faces:
        # Get or create midpoint vertices for each edge
        midpoint_indices = []
        for i in range(3):
            edge = tuple(sorted([face[i], face[(i + 1) % 3]]))

            if edge not in midpoint_cache:
                # Calculate midpoint and project to unit sphere
                midpoint = (vertices[edge[0]] + vertices[edge[1]]) / 2
                midpoint = midpoint / np.linalg.norm(midpoint)

                # Add new vertex
                midpoint_cache[edge] = len(vertices)
                vertices = np.vstack([vertices, midpoint])

            midpoint_indices.append(midpoint_cache[edge])

        # Create 4 new triangles from original triangle
        m0, m1, m2 = midpoint_indices
        new_faces.extend(
            [
                [face[0], m0, m2],
                [face[1], m1, m0],
                [face[2], m2, m1],
                [m0, m1, m2],
            ]
        )

    return vertices, np.array(new_faces, dtype=np.int64)


def generate_cylinder_geometry(
    radius: float,
    height: float,
    sections: int = DEFAULT_CYLINDER_SECTIONS,
) -> tuple[NDArray[np.float64], NDArray[np.int64]]:
    """
    Generate cylinder vertices and faces along the Z axis.

    Creates a cylinder centered at origin, extending from -height/2 to +height/2
    along the Z axis. Includes capped ends.

    Args:
        radius: Cylinder radius.
        height: Total height (length) of cylinder.
        sections: Number of segments around circumference. Higher values
            produce smoother cylinders.

    Returns:
        Tuple of (vertices, faces) arrays.
    """
    import numpy as np

    # Generate circle points
    angles = np.linspace(0, 2 * np.pi, sections, endpoint=False)
    cos_angles = np.cos(angles)
    sin_angles = np.sin(angles)

    half_height = height / 2

    # Bottom circle vertices
    bottom_ring = np.column_stack(
        [
            radius * cos_angles,
            radius * sin_angles,
            np.full(sections, -half_height),
        ]
    )

    # Top circle vertices
    top_ring = np.column_stack(
        [
            radius * cos_angles,
            radius * sin_angles,
            np.full(sections, half_height),
        ]
    )

    # Cap center vertices
    bottom_center = np.array([[0, 0, -half_height]])
    top_center = np.array([[0, 0, half_height]])

    vertices = np.vstack([bottom_ring, top_ring, bottom_center, top_center])

    # Build faces
    faces = []
    bottom_center_idx = 2 * sections
    top_center_idx = 2 * sections + 1

    for i in range(sections):
        next_i = (i + 1) % sections

        # Side faces (two triangles per quad)
        faces.append([i, next_i, sections + i])
        faces.append([next_i, sections + next_i, sections + i])

        # Bottom cap triangle
        faces.append([bottom_center_idx, next_i, i])

        # Top cap triangle
        faces.append([top_center_idx, sections + i, sections + next_i])

    return vertices, np.array(faces, dtype=np.int64)


def generate_box_geometry(
    extents: tuple[float, float, float],
) -> tuple[NDArray[np.float64], NDArray[np.int64]]:
    """
    Generate axis-aligned box vertices and faces.

    Creates a box centered at origin with the specified dimensions.

    Args:
        extents: Box dimensions as (width, height, depth) corresponding
            to (X, Y, Z) axis sizes.

    Returns:
        Tuple of (vertices, faces) arrays.
    """
    import numpy as np

    half_w, half_h, half_d = [e / 2 for e in extents]

    # 8 corner vertices
    vertices = np.array(
        [
            [-half_w, -half_h, -half_d],  # 0: back-bottom-left
            [+half_w, -half_h, -half_d],  # 1: back-bottom-right
            [+half_w, +half_h, -half_d],  # 2: back-top-right
            [-half_w, +half_h, -half_d],  # 3: back-top-left
            [-half_w, -half_h, +half_d],  # 4: front-bottom-left
            [+half_w, -half_h, +half_d],  # 5: front-bottom-right
            [+half_w, +half_h, +half_d],  # 6: front-top-right
            [-half_w, +half_h, +half_d],  # 7: front-top-left
        ],
        dtype=np.float64,
    )

    # 12 triangles (2 per face)
    faces = np.array(
        [
            [0, 1, 2],
            [0, 2, 3],  # back face (-Z)
            [4, 6, 5],
            [4, 7, 6],  # front face (+Z)
            [0, 4, 5],
            [0, 5, 1],  # bottom face (-Y)
            [2, 6, 7],
            [2, 7, 3],  # top face (+Y)
            [0, 3, 7],
            [0, 7, 4],  # left face (-X)
            [1, 5, 6],
            [1, 6, 2],  # right face (+X)
        ],
        dtype=np.int64,
    )

    return vertices, faces


# =============================================================================
# Abstract Base Class
# =============================================================================


class MeshBackend(ABC):
    """
    Abstract base class defining the mesh creation interface.

    All mesh backends must implement this interface to ensure consistent
    behavior across different 3D libraries. The interface follows the
    Strategy pattern, allowing runtime selection of mesh implementation.

    Subclasses must implement:
        - name: Property returning backend identifier
        - create_sphere: Generate sphere mesh
        - create_cylinder: Generate cylinder mesh
        - create_box: Generate box mesh
        - export: Save meshes to file
        - get_supported_formats: List exportable formats

    Example:
        >>> class CustomBackend(MeshBackend):
        ...     @property
        ...     def name(self) -> str:
        ...         return "custom"
        ...     # ... implement other methods
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """
        Return the backend's identifier string.

        Returns:
            Lowercase backend name (e.g., "trimesh", "blender").
        """
        pass

    @abstractmethod
    def create_sphere(
        self,
        radius: float,
        center: tuple[float, float, float],
        subdivisions: int = DEFAULT_SPHERE_SUBDIVISIONS,
    ) -> MeshData:
        """
        Create a sphere (icosphere) mesh.

        Args:
            radius: Sphere radius in scene units.
            center: Center position as (x, y, z).
            subdivisions: Icosphere subdivision level.

        Returns:
            MeshData containing sphere geometry.
        """
        pass

    @abstractmethod
    def create_cylinder(
        self,
        radius: float,
        height: float,
        center: tuple[float, float, float],
        rotation_degrees: tuple[float, float, float] = (0, 0, 0),
        sections: int = DEFAULT_CYLINDER_SECTIONS,
    ) -> MeshData:
        """
        Create a cylinder mesh with optional rotation.

        The cylinder is created along the Z axis by default, then rotated
        and translated to the specified position.

        Args:
            radius: Cylinder radius.
            height: Cylinder height (length).
            center: Center position as (x, y, z).
            rotation_degrees: Euler rotation as (rx, ry, rz) in degrees.
            sections: Number of segments around circumference.

        Returns:
            MeshData containing cylinder geometry.
        """
        pass

    @abstractmethod
    def create_box(
        self,
        extents: tuple[float, float, float],
        center: tuple[float, float, float],
        rotation_degrees: tuple[float, float, float] = (0, 0, 0),
    ) -> MeshData:
        """
        Create a box mesh with optional rotation.

        Args:
            extents: Box dimensions as (width, height, depth).
            center: Center position as (x, y, z).
            rotation_degrees: Euler rotation as (rx, ry, rz) in degrees.

        Returns:
            MeshData containing box geometry.
        """
        pass

    @abstractmethod
    def export(
        self,
        meshes: list[MeshData],
        filepath: str,
        file_format: str | None = None,
    ) -> None:
        """
        Export meshes to a file.

        Args:
            meshes: List of MeshData objects to export.
            filepath: Output file path.
            file_format: Export format (e.g., "glb", "obj"). If None,
                inferred from filepath extension.

        Raises:
            ValueError: If format is not supported by this backend.
        """
        pass

    @abstractmethod
    def get_supported_formats(self) -> list[str]:
        """
        Return list of supported export format extensions.

        Returns:
            List of format strings (e.g., ["glb", "obj", "stl"]).
        """
        pass


# =============================================================================
# Backend Implementations
# =============================================================================


class TrimeshBackend(MeshBackend):
    """
    Mesh backend using the trimesh library.

    Trimesh is the recommended backend for most use cases, offering:
        - Wide format support (GLB, OBJ, STL, PLY, etc.)
        - Scene/hierarchy support for organized exports
        - Good performance and stability

    Requires: pip install trimesh
    """

    def __init__(self) -> None:
        """Initialize trimesh backend and import dependencies."""
        import numpy as np
        import trimesh
        from scipy.spatial.transform import Rotation

        self._trimesh = trimesh
        self._np = np
        self._Rotation = Rotation

    @property
    def name(self) -> str:
        """Return backend identifier."""
        return "trimesh"

    def _apply_transform(
        self,
        mesh: Any,
        rotation_degrees: tuple[float, float, float],
        center: tuple[float, float, float],
    ) -> Any:
        """
        Apply rotation and translation to a trimesh mesh object.

        Args:
            mesh: Trimesh mesh object.
            rotation_degrees: Euler angles in degrees.
            center: Translation vector.

        Returns:
            Transformed mesh object.
        """
        if any(r != 0 for r in rotation_degrees):
            rotation_matrix = self._Rotation.from_euler(
                "xyz", rotation_degrees, degrees=True
            ).as_matrix()
            transform = self._np.eye(4)
            transform[:3, :3] = rotation_matrix
            mesh.apply_transform(transform)

        mesh.apply_translation(center)
        return mesh

    def create_sphere(
        self,
        radius: float,
        center: tuple[float, float, float],
        subdivisions: int = DEFAULT_SPHERE_SUBDIVISIONS,
    ) -> MeshData:
        """Create an icosphere mesh at the specified position."""
        mesh = self._trimesh.creation.icosphere(
            subdivisions=subdivisions,
            radius=radius,
        )
        mesh.apply_translation(center)

        return MeshData(
            vertices=mesh.vertices,
            faces=mesh.faces,
            native=mesh,
        )

    def create_cylinder(
        self,
        radius: float,
        height: float,
        center: tuple[float, float, float],
        rotation_degrees: tuple[float, float, float] = (0, 0, 0),
        sections: int = DEFAULT_CYLINDER_SECTIONS,
    ) -> MeshData:
        """Create a cylinder mesh with optional rotation."""
        mesh = self._trimesh.creation.cylinder(
            radius=radius,
            height=height,
            sections=sections,
        )
        mesh = self._apply_transform(mesh, rotation_degrees, center)

        return MeshData(
            vertices=mesh.vertices,
            faces=mesh.faces,
            native=mesh,
        )

    def create_box(
        self,
        extents: tuple[float, float, float],
        center: tuple[float, float, float],
        rotation_degrees: tuple[float, float, float] = (0, 0, 0),
    ) -> MeshData:
        """Create a box mesh with optional rotation."""
        mesh = self._trimesh.creation.box(extents=extents)
        mesh = self._apply_transform(mesh, rotation_degrees, center)

        return MeshData(
            vertices=mesh.vertices,
            faces=mesh.faces,
            native=mesh,
        )

    def export(
        self,
        meshes: list[MeshData],
        filepath: str,
        file_format: str | None = None,
    ) -> None:
        """Export meshes to file using trimesh's scene export."""
        scene = self._trimesh.Scene()

        for mesh in meshes:
            if mesh.native is not None:
                geometry = mesh.native
            else:
                geometry = self._trimesh.Trimesh(
                    vertices=mesh.vertices,
                    faces=mesh.faces,
                )
            scene.add_geometry(geometry, node_name=mesh.name, geom_name=mesh.name)

        scene.export(filepath, file_type=file_format)

    def get_supported_formats(self) -> list[str]:
        """Return list of formats supported by trimesh."""
        return ["glb", "gltf", "obj", "stl", "ply", "off", "dae"]


class Open3DBackend(MeshBackend):
    """
    Mesh backend using the Open3D library.

    Open3D is a good alternative when you need:
        - Point cloud processing integration
        - Advanced visualization
        - Research/academic workflows

    Note: Open3D doesn't support scene hierarchies, so meshes are merged
    on export.

    Requires: pip install open3d
    """

    def __init__(self) -> None:
        """Initialize Open3D backend and import dependencies."""
        import numpy as np
        import open3d as o3d

        self._o3d = o3d
        self._np = np

    @property
    def name(self) -> str:
        """Return backend identifier."""
        return "open3d"

    def create_sphere(
        self,
        radius: float,
        center: tuple[float, float, float],
        subdivisions: int = DEFAULT_SPHERE_SUBDIVISIONS,
    ) -> MeshData:
        """Create a sphere mesh using Open3D's UV sphere."""
        # Open3D uses resolution parameter (approximate subdivision equivalent)
        resolution = 10 * (subdivisions + 1)

        mesh = self._o3d.geometry.TriangleMesh.create_sphere(
            radius=radius,
            resolution=resolution,
        )
        mesh.translate(center)
        mesh.compute_vertex_normals()

        return MeshData(
            vertices=self._np.asarray(mesh.vertices),
            faces=self._np.asarray(mesh.triangles),
            native=mesh,
        )

    def create_cylinder(
        self,
        radius: float,
        height: float,
        center: tuple[float, float, float],
        rotation_degrees: tuple[float, float, float] = (0, 0, 0),
        sections: int = DEFAULT_CYLINDER_SECTIONS,
    ) -> MeshData:
        """Create a cylinder mesh with optional rotation."""
        mesh = self._o3d.geometry.TriangleMesh.create_cylinder(
            radius=radius,
            height=height,
            resolution=sections,
        )

        # Apply rotation around origin
        if any(r != 0 for r in rotation_degrees):
            rotation_matrix = mesh.get_rotation_matrix_from_xyz(self._np.radians(rotation_degrees))
            mesh.rotate(rotation_matrix, center=(0, 0, 0))

        mesh.translate(center)
        mesh.compute_vertex_normals()

        return MeshData(
            vertices=self._np.asarray(mesh.vertices),
            faces=self._np.asarray(mesh.triangles),
            native=mesh,
        )

    def create_box(
        self,
        extents: tuple[float, float, float],
        center: tuple[float, float, float],
        rotation_degrees: tuple[float, float, float] = (0, 0, 0),
    ) -> MeshData:
        """Create a box mesh with optional rotation."""
        mesh = self._o3d.geometry.TriangleMesh.create_box(
            width=extents[0],
            height=extents[1],
            depth=extents[2],
        )

        # Center the box (Open3D creates box with corner at origin)
        mesh.translate((-extents[0] / 2, -extents[1] / 2, -extents[2] / 2))

        # Apply rotation around origin
        if any(r != 0 for r in rotation_degrees):
            rotation_matrix = mesh.get_rotation_matrix_from_xyz(self._np.radians(rotation_degrees))
            mesh.rotate(rotation_matrix, center=(0, 0, 0))

        mesh.translate(center)
        mesh.compute_vertex_normals()

        return MeshData(
            vertices=self._np.asarray(mesh.vertices),
            faces=self._np.asarray(mesh.triangles),
            native=mesh,
        )

    def export(
        self,
        meshes: list[MeshData],
        filepath: str,
        file_format: str | None = None,
    ) -> None:
        """Export meshes by merging into single mesh (Open3D limitation)."""
        combined = self._o3d.geometry.TriangleMesh()

        for mesh in meshes:
            if mesh.native is not None:
                combined += mesh.native
            else:
                mesh_obj = self._o3d.geometry.TriangleMesh()
                mesh_obj.vertices = self._o3d.utility.Vector3dVector(mesh.vertices)
                mesh_obj.triangles = self._o3d.utility.Vector3iVector(mesh.faces)
                combined += mesh_obj

        self._o3d.io.write_triangle_mesh(filepath, combined)

    def get_supported_formats(self) -> list[str]:
        """Return list of formats supported by Open3D."""
        return ["obj", "stl", "ply", "off", "gltf", "glb"]


class NumpySTLBackend(MeshBackend):
    """
    Lightweight mesh backend using numpy-stl.

    This backend is ideal when you:
        - Only need STL output
        - Want minimal dependencies
        - Need fast, simple mesh generation

    Limitations:
        - STL format only (no materials, colors, or hierarchy)
        - No native mesh manipulation features

    Requires: pip install numpy-stl
    """

    def __init__(self) -> None:
        """Initialize numpy-stl backend and import dependencies."""
        import numpy as np
        from stl import mesh as stl_mesh

        self._stl_mesh = stl_mesh
        self._np = np

    @property
    def name(self) -> str:
        """Return backend identifier."""
        return "numpy-stl"

    def create_sphere(
        self,
        radius: float,
        center: tuple[float, float, float],
        subdivisions: int = DEFAULT_SPHERE_SUBDIVISIONS,
    ) -> MeshData:
        """Create an icosphere using shared geometry generator."""
        vertices, faces = generate_icosphere_geometry(radius, subdivisions)
        vertices = vertices + self._np.array(center)

        return MeshData(vertices=vertices, faces=faces)

    def create_cylinder(
        self,
        radius: float,
        height: float,
        center: tuple[float, float, float],
        rotation_degrees: tuple[float, float, float] = (0, 0, 0),
        sections: int = DEFAULT_CYLINDER_SECTIONS,
    ) -> MeshData:
        """Create a cylinder using shared geometry generator."""
        vertices, faces = generate_cylinder_geometry(radius, height, sections)
        vertices = apply_transform(vertices, rotation_degrees, center)

        return MeshData(vertices=vertices, faces=faces)

    def create_box(
        self,
        extents: tuple[float, float, float],
        center: tuple[float, float, float],
        rotation_degrees: tuple[float, float, float] = (0, 0, 0),
    ) -> MeshData:
        """Create a box using shared geometry generator."""
        vertices, faces = generate_box_geometry(extents)
        vertices = apply_transform(vertices, rotation_degrees, center)

        return MeshData(vertices=vertices, faces=faces)

    def export(
        self,
        meshes: list[MeshData],
        filepath: str,
        file_format: str | None = None,
    ) -> None:
        """Export meshes to STL format."""
        # Combine all meshes into single vertex/face arrays
        all_vertices = []
        all_faces = []
        vertex_offset = 0

        for mesh in meshes:
            all_vertices.append(mesh.vertices)
            all_faces.append(mesh.faces + vertex_offset)
            vertex_offset += len(mesh.vertices)

        vertices = self._np.vstack(all_vertices)
        faces = self._np.vstack(all_faces)

        # Create STL mesh structure
        stl_data = self._stl_mesh.Mesh(self._np.zeros(len(faces), dtype=self._stl_mesh.Mesh.dtype))

        for i, face in enumerate(faces):
            for j in range(3):
                stl_data.vectors[i][j] = vertices[face[j]]

        stl_data.save(filepath)

    def get_supported_formats(self) -> list[str]:
        """Return list of formats supported (STL only)."""
        return ["stl"]


class BlenderBackend(MeshBackend):
    """
    Mesh backend using Blender's Python API (bpy).

    Creates native Blender objects directly in the scene, making it ideal
    for use within Blender's scripting environment or the Figure Generator
    Blender addon.

    Features:
        - Native Blender mesh objects
        - Automatic collection organization
        - Wide export format support via Blender

    Limitations:
        - Only works when running inside Blender
        - Requires Blender 3.0+

    Note:
        This backend is automatically selected when running inside Blender.
    """

    def __init__(self) -> None:
        """Initialize Blender backend and import bpy modules."""
        import bmesh
        import bpy
        import numpy as np
        from mathutils import Matrix, Vector

        self._bpy = bpy
        self._bmesh = bmesh
        self._np = np
        self._Matrix = Matrix
        self._Vector = Vector
        self._created_objects: list[Any] = []

    @property
    def name(self) -> str:
        """Return backend identifier."""
        return "blender"

    def _get_or_create_collection(
        self,
        name: str = "FigureGenerator",
    ) -> Any:
        """
        Get existing collection or create new one for generated meshes.

        Args:
            name: Collection name.

        Returns:
            Blender collection object.
        """
        bpy = self._bpy

        if name in bpy.data.collections:
            return bpy.data.collections[name]

        collection = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(collection)
        return collection

    def _create_mesh_object(
        self,
        vertices: list[list[float]],
        faces: list[list[int]],
        name: str,
    ) -> Any:
        """
        Create a Blender mesh object from vertex/face data.

        Args:
            vertices: List of [x, y, z] vertex positions.
            faces: List of vertex index lists for each face.
            name: Object name in Blender.

        Returns:
            Blender object reference.
        """
        bpy = self._bpy

        mesh = bpy.data.meshes.new(name)
        mesh.from_pydata(vertices, [], faces)
        mesh.update()

        obj = bpy.data.objects.new(name, mesh)
        collection = self._get_or_create_collection()
        collection.objects.link(obj)

        self._created_objects.append(obj)
        return obj

    def create_sphere(
        self,
        radius: float,
        center: tuple[float, float, float],
        subdivisions: int = DEFAULT_SPHERE_SUBDIVISIONS,
    ) -> MeshData:
        """Create an icosphere using Blender's bmesh operations."""
        bmesh_mod = self._bmesh

        bm = bmesh_mod.new()
        bmesh_mod.ops.create_icosphere(
            bm,
            subdivisions=subdivisions,
            radius=radius,
        )

        # Extract geometry
        vertices = [[v.co.x + center[0], v.co.y + center[1], v.co.z + center[2]] for v in bm.verts]
        bm.verts.ensure_lookup_table()
        faces = [[v.index for v in f.verts] for f in bm.faces]

        bm.free()

        obj = self._create_mesh_object(vertices, faces, "Sphere")

        return MeshData(
            vertices=self._np.array(vertices),
            faces=self._np.array(faces),
            native=obj,
        )

    def create_cylinder(
        self,
        radius: float,
        height: float,
        center: tuple[float, float, float],
        rotation_degrees: tuple[float, float, float] = (0, 0, 0),
        sections: int = DEFAULT_CYLINDER_SECTIONS,
    ) -> MeshData:
        """Create a cylinder using Blender's bmesh operations."""
        bmesh_mod = self._bmesh
        np = self._np

        bm = bmesh_mod.new()
        bmesh_mod.ops.create_cone(
            bm,
            cap_ends=True,
            cap_tris=False,
            segments=sections,
            radius1=radius,
            radius2=radius,
            depth=height,
        )

        # Extract geometry as numpy array for transformation
        vertices = np.array([list(v.co) for v in bm.verts])
        bm.verts.ensure_lookup_table()
        faces = [[v.index for v in f.verts] for f in bm.faces]

        bm.free()

        # Apply transformation
        vertices = apply_transform(vertices, rotation_degrees, center)

        obj = self._create_mesh_object(vertices.tolist(), faces, "Cylinder")

        return MeshData(
            vertices=vertices,
            faces=np.array(faces),
            native=obj,
        )

    def create_box(
        self,
        extents: tuple[float, float, float],
        center: tuple[float, float, float],
        rotation_degrees: tuple[float, float, float] = (0, 0, 0),
    ) -> MeshData:
        """Create a box using Blender's bmesh operations."""
        bmesh_mod = self._bmesh
        np = self._np

        bm = bmesh_mod.new()
        bmesh_mod.ops.create_cube(bm, size=1.0)

        # Scale to extents
        for v in bm.verts:
            v.co.x *= extents[0]
            v.co.y *= extents[1]
            v.co.z *= extents[2]

        # Extract geometry
        vertices = np.array([list(v.co) for v in bm.verts])
        bm.verts.ensure_lookup_table()
        faces = [[v.index for v in f.verts] for f in bm.faces]

        bm.free()

        # Apply transformation
        vertices = apply_transform(vertices, rotation_degrees, center)

        obj = self._create_mesh_object(vertices.tolist(), faces, "Box")

        return MeshData(
            vertices=vertices,
            faces=np.array(faces),
            native=obj,
        )

    def export(
        self,
        meshes: list[MeshData],
        filepath: str,
        file_format: str | None = None,
    ) -> None:
        """
        Export meshes using Blender's native exporters.

        If filepath is empty, meshes remain in scene without file export.
        """
        import os

        bpy = self._bpy

        if not filepath:
            return  # Keep meshes in scene only

        # Determine format from extension if not specified
        if file_format is None:
            file_format = os.path.splitext(filepath)[1].lstrip(".").lower()

        # Select only generated objects for export
        bpy.ops.object.select_all(action="DESELECT")
        for mesh in meshes:
            if mesh.native and hasattr(mesh.native, "select_set"):
                mesh.native.select_set(True)

        # Set active object for export context
        if meshes and meshes[0].native:
            bpy.context.view_layer.objects.active = meshes[0].native

        # Dispatch to appropriate exporter
        export_handlers = {
            "blend": lambda: bpy.ops.wm.save_as_mainfile(filepath=filepath),
            "glb": lambda: bpy.ops.export_scene.gltf(
                filepath=filepath, use_selection=True, export_format="GLB"
            ),
            "gltf": lambda: bpy.ops.export_scene.gltf(
                filepath=filepath, use_selection=True, export_format="GLTF_SEPARATE"
            ),
            "fbx": lambda: bpy.ops.export_scene.fbx(filepath=filepath, use_selection=True),
            "obj": lambda: bpy.ops.wm.obj_export(filepath=filepath, export_selected_objects=True),
            "stl": lambda: bpy.ops.export_mesh.stl(filepath=filepath, use_selection=True),
            "ply": lambda: bpy.ops.export_mesh.ply(filepath=filepath, use_selection=True),
            "dae": lambda: bpy.ops.wm.collada_export(filepath=filepath, selected=True),
            "usd": lambda: bpy.ops.wm.usd_export(filepath=filepath, selected_objects_only=True),
            "usdc": lambda: bpy.ops.wm.usd_export(filepath=filepath, selected_objects_only=True),
            "usda": lambda: bpy.ops.wm.usd_export(filepath=filepath, selected_objects_only=True),
        }

        handler = export_handlers.get(file_format)
        if handler is None:
            raise ValueError(f"Unsupported export format: {file_format}")

        handler()

    def get_supported_formats(self) -> list[str]:
        """Return list of formats supported by Blender export."""
        return ["blend", "glb", "gltf", "fbx", "obj", "stl", "ply", "dae", "usd", "usdc", "usda"]

    def get_created_objects(self) -> list[Any]:
        """
        Return list of Blender objects created by this backend instance.

        Useful for selecting, modifying, or cleaning up generated objects.
        """
        return self._created_objects.copy()

    def clear_created_objects(self) -> None:
        """Remove all objects created by this backend from the scene."""
        bpy = self._bpy

        for obj in self._created_objects:
            if obj.name in bpy.data.objects:
                bpy.data.objects.remove(obj, do_unlink=True)

        self._created_objects.clear()


# =============================================================================
# Factory Functions
# =============================================================================


def _check_available(module_name: str) -> bool:
    """
    Check if a Python module is available for import.

    Args:
        module_name: Module name to check (e.g., "trimesh").

    Returns:
        True if module can be imported, False otherwise.
    """
    return importlib.util.find_spec(module_name) is not None


def get_available_backends() -> list[str]:
    """
    Return list of currently available backend names.

    Checks which mesh libraries are installed and returns their
    corresponding backend names.

    Returns:
        List of available backend names (e.g., ["trimesh", "numpy-stl"]).

    Example:
        >>> backends = get_available_backends()
        >>> print(backends)
        ['trimesh', 'numpy-stl']
    """
    available = []

    if _check_available("trimesh"):
        available.append("trimesh")
    if _check_available("open3d"):
        available.append("open3d")
    if _check_available("stl"):
        available.append("numpy-stl")
    if _check_available("bpy"):
        available.append("blender")

    return available


def is_running_in_blender() -> bool:
    """
    Check if code is running inside Blender's Python environment.

    Returns:
        True if bpy module is available (running in Blender).
    """
    return _check_available("bpy")


def create_backend(name: str | None = None) -> MeshBackend:
    """
    Create a mesh backend instance.

    Factory function that instantiates the appropriate backend class.
    If no name is specified, automatically selects the best available
    backend based on environment and installed packages.

    Selection priority (when name is None):
        1. blender (if running inside Blender)
        2. trimesh (most full-featured)
        3. open3d (good alternative)
        4. numpy-stl (lightweight fallback)

    Args:
        name: Backend name to instantiate. One of:
            - "trimesh": Full-featured mesh library
            - "open3d": Alternative with point cloud support
            - "numpy-stl": Lightweight, STL-only
            - "blender": Native Blender integration
            - None: Auto-select best available

    Returns:
        Instantiated MeshBackend subclass.

    Raises:
        ValueError: If no backends are available.
        ImportError: If requested backend is not installed.

    Example:
        >>> backend = create_backend()  # Auto-select
        >>> backend = create_backend("trimesh")  # Specific backend
    """
    available = get_available_backends()

    if not available:
        raise ValueError(
            "No mesh backends available. Install one of: " "trimesh, open3d, or numpy-stl"
        )

    if name is None:
        # Auto-select: prefer Blender if inside Blender, otherwise by priority
        if is_running_in_blender():
            name = "blender"
        else:
            priority_order = ["trimesh", "open3d", "numpy-stl"]
            for preferred in priority_order:
                if preferred in available:
                    name = preferred
                    break

    if name not in available:
        raise ImportError(f"Backend '{name}' not available. " f"Available backends: {available}")

    # Instantiate requested backend
    backend_classes = {
        "trimesh": TrimeshBackend,
        "open3d": Open3DBackend,
        "numpy-stl": NumpySTLBackend,
        "blender": BlenderBackend,
    }

    backend_class = backend_classes.get(name)
    if backend_class is None:
        raise ValueError(f"Unknown backend: {name}")

    return backend_class()

"""
Mesh creation backends.

This module provides an abstraction layer for mesh creation,
supporting multiple 3D libraries:
- trimesh (default, most full-featured)
- open3d (alternative, good for point cloud work)
- numpy-stl (lightweight, STL-only output)

The backend is selected automatically based on availability,
or can be explicitly specified.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Tuple, Any, Protocol
import importlib.util


@dataclass
class MeshData:
    """
    Container for mesh geometry data.
    
    This provides a backend-agnostic representation of mesh data
    that can be converted to any supported library's format.
    
    Attributes:
        vertices: Nx3 array of vertex positions
        faces: Mx3 array of triangle face indices
        name: Optional name for the mesh
        native: Optional reference to native mesh object
    """
    vertices: Any  # numpy array
    faces: Any     # numpy array
    name: str = ""
    native: Optional[Any] = None


class MeshBackend(ABC):
    """Abstract base class for mesh creation backends."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Return backend name."""
        pass
    
    @abstractmethod
    def create_sphere(
        self, 
        radius: float, 
        center: Tuple[float, float, float],
        subdivisions: int = 2
    ) -> MeshData:
        """Create a sphere mesh."""
        pass
    
    @abstractmethod
    def create_cylinder(
        self,
        radius: float,
        height: float,
        center: Tuple[float, float, float],
        rotation_degrees: Tuple[float, float, float] = (0, 0, 0),
        sections: int = 16
    ) -> MeshData:
        """Create a cylinder mesh with optional rotation."""
        pass
    
    @abstractmethod
    def create_box(
        self,
        extents: Tuple[float, float, float],
        center: Tuple[float, float, float],
        rotation_degrees: Tuple[float, float, float] = (0, 0, 0)
    ) -> MeshData:
        """Create a box mesh with optional rotation."""
        pass
    
    @abstractmethod
    def export(
        self,
        meshes: List[MeshData],
        filepath: str,
        file_format: Optional[str] = None
    ) -> None:
        """Export meshes to file."""
        pass
    
    @abstractmethod
    def get_supported_formats(self) -> List[str]:
        """Return list of supported export formats."""
        pass


class TrimeshBackend(MeshBackend):
    """Mesh backend using trimesh library."""
    
    def __init__(self):
        import trimesh
        import numpy as np
        from scipy.spatial.transform import Rotation
        self._trimesh = trimesh
        self._np = np
        self._Rotation = Rotation
    
    @property
    def name(self) -> str:
        return "trimesh"
    
    def _apply_transform(self, mesh, rotation_degrees, center):
        """Apply rotation and translation to mesh."""
        if any(r != 0 for r in rotation_degrees):
            rot = self._Rotation.from_euler(
                'xyz', rotation_degrees, degrees=True
            ).as_matrix()
            transform = self._np.eye(4)
            transform[:3, :3] = rot
            mesh.apply_transform(transform)
        mesh.apply_translation(center)
        return mesh
    
    def create_sphere(
        self,
        radius: float,
        center: Tuple[float, float, float],
        subdivisions: int = 2
    ) -> MeshData:
        mesh = self._trimesh.creation.icosphere(
            subdivisions=subdivisions, 
            radius=radius
        )
        mesh.apply_translation(center)
        return MeshData(
            vertices=mesh.vertices,
            faces=mesh.faces,
            native=mesh
        )
    
    def create_cylinder(
        self,
        radius: float,
        height: float,
        center: Tuple[float, float, float],
        rotation_degrees: Tuple[float, float, float] = (90, 0, 0),  # Default vertical
        sections: int = 16
    ) -> MeshData:
        mesh = self._trimesh.creation.cylinder(
            radius=radius,
            height=height,
            sections=sections
        )
        mesh = self._apply_transform(mesh, rotation_degrees, center)
        return MeshData(
            vertices=mesh.vertices,
            faces=mesh.faces,
            native=mesh
        )
    
    def create_box(
        self,
        extents: Tuple[float, float, float],
        center: Tuple[float, float, float],
        rotation_degrees: Tuple[float, float, float] = (0, 0, 0)
    ) -> MeshData:
        mesh = self._trimesh.creation.box(extents=extents)
        mesh = self._apply_transform(mesh, rotation_degrees, center)
        return MeshData(
            vertices=mesh.vertices,
            faces=mesh.faces,
            native=mesh
        )
    
    def export(
        self,
        meshes: List[MeshData],
        filepath: str,
        file_format: Optional[str] = None
    ) -> None:
        scene = self._trimesh.Scene()
        for mesh in meshes:
            if mesh.native is not None:
                geom = mesh.native
            else:
                geom = self._trimesh.Trimesh(
                    vertices=mesh.vertices,
                    faces=mesh.faces
                )
            scene.add_geometry(geom, node_name=mesh.name, geom_name=mesh.name)
        scene.export(filepath, file_type=file_format)
    
    def get_supported_formats(self) -> List[str]:
        return ["glb", "gltf", "obj", "stl", "ply", "off", "dae"]


class Open3DBackend(MeshBackend):
    """Mesh backend using Open3D library."""
    
    def __init__(self):
        import open3d as o3d
        import numpy as np
        self._o3d = o3d
        self._np = np
    
    @property
    def name(self) -> str:
        return "open3d"
    
    def create_sphere(
        self,
        radius: float,
        center: Tuple[float, float, float],
        subdivisions: int = 2
    ) -> MeshData:
        # Open3D uses resolution parameter instead of subdivisions
        resolution = 10 * (subdivisions + 1)
        mesh = self._o3d.geometry.TriangleMesh.create_sphere(
            radius=radius,
            resolution=resolution
        )
        mesh.translate(center)
        mesh.compute_vertex_normals()
        return MeshData(
            vertices=self._np.asarray(mesh.vertices),
            faces=self._np.asarray(mesh.triangles),
            native=mesh
        )
    
    def create_cylinder(
        self,
        radius: float,
        height: float,
        center: Tuple[float, float, float],
        rotation_degrees: Tuple[float, float, float] = (0, 0, 0),
        sections: int = 16
    ) -> MeshData:
        mesh = self._o3d.geometry.TriangleMesh.create_cylinder(
            radius=radius,
            height=height,
            resolution=sections
        )
        # Apply rotation
        R = mesh.get_rotation_matrix_from_xyz(
            self._np.radians(rotation_degrees)
        )
        mesh.rotate(R, center=(0, 0, 0))
        mesh.translate(center)
        mesh.compute_vertex_normals()
        return MeshData(
            vertices=self._np.asarray(mesh.vertices),
            faces=self._np.asarray(mesh.triangles),
            native=mesh
        )
    
    def create_box(
        self,
        extents: Tuple[float, float, float],
        center: Tuple[float, float, float],
        rotation_degrees: Tuple[float, float, float] = (0, 0, 0)
    ) -> MeshData:
        mesh = self._o3d.geometry.TriangleMesh.create_box(
            width=extents[0],
            height=extents[1],
            depth=extents[2]
        )
        # Center the box (Open3D creates at origin corner)
        mesh.translate((-extents[0]/2, -extents[1]/2, -extents[2]/2))
        # Apply rotation
        if any(r != 0 for r in rotation_degrees):
            R = mesh.get_rotation_matrix_from_xyz(
                self._np.radians(rotation_degrees)
            )
            mesh.rotate(R, center=(0, 0, 0))
        mesh.translate(center)
        mesh.compute_vertex_normals()
        return MeshData(
            vertices=self._np.asarray(mesh.vertices),
            faces=self._np.asarray(mesh.triangles),
            native=mesh
        )
    
    def export(
        self,
        meshes: List[MeshData],
        filepath: str,
        file_format: Optional[str] = None
    ) -> None:
        # Open3D doesn't have scene support, merge meshes
        combined = self._o3d.geometry.TriangleMesh()
        for mesh in meshes:
            if mesh.native is not None:
                combined += mesh.native
            else:
                m = self._o3d.geometry.TriangleMesh()
                m.vertices = self._o3d.utility.Vector3dVector(mesh.vertices)
                m.triangles = self._o3d.utility.Vector3iVector(mesh.faces)
                combined += m
        self._o3d.io.write_triangle_mesh(filepath, combined)
    
    def get_supported_formats(self) -> List[str]:
        return ["obj", "stl", "ply", "off", "gltf", "glb"]


class BlenderBackend(MeshBackend):
    """
    Mesh backend using Blender's Python API (bpy).

    This backend creates native Blender objects directly in the scene,
    making it ideal for use within Blender's scripting environment.

    Note: This backend only works when running inside Blender.
    """

    def __init__(self):
        import bpy
        import bmesh
        import numpy as np
        from mathutils import Matrix, Vector
        self._bpy = bpy
        self._bmesh = bmesh
        self._np = np
        self._Matrix = Matrix
        self._Vector = Vector
        self._created_objects: List[Any] = []

    @property
    def name(self) -> str:
        return "blender"

    def _get_or_create_collection(self, name: str = "FigureGenerator"):
        """Get or create a collection for generated meshes."""
        bpy = self._bpy
        if name in bpy.data.collections:
            return bpy.data.collections[name]
        collection = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(collection)
        return collection

    def _create_mesh_object(self, mesh_data, name: str):
        """Create a Blender object from mesh data."""
        bpy = self._bpy
        mesh = bpy.data.meshes.new(name)
        mesh.from_pydata(mesh_data['vertices'], [], mesh_data['faces'])
        mesh.update()

        obj = bpy.data.objects.new(name, mesh)
        collection = self._get_or_create_collection()
        collection.objects.link(obj)
        self._created_objects.append(obj)
        return obj

    def create_sphere(
        self,
        radius: float,
        center: Tuple[float, float, float],
        subdivisions: int = 2
    ) -> MeshData:
        bpy = self._bpy
        bmesh = self._bmesh

        # Create icosphere using bmesh
        bm = bmesh.new()
        bmesh.ops.create_icosphere(
            bm,
            subdivisions=subdivisions,
            radius=radius
        )

        # Get vertices and faces
        vertices = [list(v.co) for v in bm.verts]
        bm.verts.ensure_lookup_table()
        faces = [[v.index for v in f.verts] for f in bm.faces]

        # Apply translation
        vertices = [[v[0] + center[0], v[1] + center[1], v[2] + center[2]]
                   for v in vertices]

        bm.free()

        # Create Blender object
        obj = self._create_mesh_object(
            {'vertices': vertices, 'faces': faces},
            "Sphere"
        )

        return MeshData(
            vertices=self._np.array(vertices),
            faces=self._np.array(faces),
            native=obj
        )

    def create_cylinder(
        self,
        radius: float,
        height: float,
        center: Tuple[float, float, float],
        rotation_degrees: Tuple[float, float, float] = (0, 0, 0),
        sections: int = 16
    ) -> MeshData:
        bpy = self._bpy
        bmesh = self._bmesh
        np = self._np

        # Create cylinder using bmesh
        bm = bmesh.new()
        bmesh.ops.create_cone(
            bm,
            cap_ends=True,
            cap_tris=False,
            segments=sections,
            radius1=radius,
            radius2=radius,
            depth=height
        )

        # Get vertices and faces
        vertices = np.array([list(v.co) for v in bm.verts])
        bm.verts.ensure_lookup_table()
        faces = [[v.index for v in f.verts] for f in bm.faces]

        bm.free()

        # Apply rotation
        if any(r != 0 for r in rotation_degrees):
            from scipy.spatial.transform import Rotation
            R = Rotation.from_euler('xyz', rotation_degrees, degrees=True).as_matrix()
            vertices = vertices @ R.T

        # Apply translation
        vertices = vertices + np.array(center)

        # Create Blender object
        obj = self._create_mesh_object(
            {'vertices': vertices.tolist(), 'faces': faces},
            "Cylinder"
        )

        return MeshData(
            vertices=vertices,
            faces=np.array(faces),
            native=obj
        )

    def create_box(
        self,
        extents: Tuple[float, float, float],
        center: Tuple[float, float, float],
        rotation_degrees: Tuple[float, float, float] = (0, 0, 0)
    ) -> MeshData:
        bpy = self._bpy
        bmesh = self._bmesh
        np = self._np

        # Create box using bmesh
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=1.0)

        # Scale to extents
        for v in bm.verts:
            v.co.x *= extents[0]
            v.co.y *= extents[1]
            v.co.z *= extents[2]

        # Get vertices and faces
        vertices = np.array([list(v.co) for v in bm.verts])
        bm.verts.ensure_lookup_table()
        faces = [[v.index for v in f.verts] for f in bm.faces]

        bm.free()

        # Apply rotation
        if any(r != 0 for r in rotation_degrees):
            from scipy.spatial.transform import Rotation
            R = Rotation.from_euler('xyz', rotation_degrees, degrees=True).as_matrix()
            vertices = vertices @ R.T

        # Apply translation
        vertices = vertices + np.array(center)

        # Create Blender object
        obj = self._create_mesh_object(
            {'vertices': vertices.tolist(), 'faces': faces},
            "Box"
        )

        return MeshData(
            vertices=vertices,
            faces=np.array(faces),
            native=obj
        )

    def export(
        self,
        meshes: List[MeshData],
        filepath: str,
        file_format: Optional[str] = None
    ) -> None:
        """
        Export meshes to file using Blender's exporters.

        If filepath is empty or None, meshes are kept in scene without exporting.
        """
        bpy = self._bpy

        if not filepath:
            # Keep in scene, no export needed
            return

        # Determine format from extension
        if file_format is None:
            import os
            file_format = os.path.splitext(filepath)[1].lstrip('.').lower()

        # Select only our generated objects for export
        bpy.ops.object.select_all(action='DESELECT')
        for mesh in meshes:
            if mesh.native and hasattr(mesh.native, 'select_set'):
                mesh.native.select_set(True)

        # Set active object
        if meshes and meshes[0].native:
            bpy.context.view_layer.objects.active = meshes[0].native

        # Export based on format
        if file_format == 'blend':
            bpy.ops.wm.save_as_mainfile(filepath=filepath)
        elif file_format == 'glb':
            bpy.ops.export_scene.gltf(
                filepath=filepath,
                use_selection=True,
                export_format='GLB'
            )
        elif file_format == 'gltf':
            bpy.ops.export_scene.gltf(
                filepath=filepath,
                use_selection=True,
                export_format='GLTF_SEPARATE'
            )
        elif file_format == 'fbx':
            bpy.ops.export_scene.fbx(
                filepath=filepath,
                use_selection=True
            )
        elif file_format == 'obj':
            bpy.ops.wm.obj_export(
                filepath=filepath,
                export_selected_objects=True
            )
        elif file_format == 'stl':
            bpy.ops.export_mesh.stl(
                filepath=filepath,
                use_selection=True
            )
        elif file_format == 'ply':
            bpy.ops.export_mesh.ply(
                filepath=filepath,
                use_selection=True
            )
        elif file_format == 'dae':
            bpy.ops.wm.collada_export(
                filepath=filepath,
                selected=True
            )
        elif file_format == 'usd' or file_format == 'usdc' or file_format == 'usda':
            bpy.ops.wm.usd_export(
                filepath=filepath,
                selected_objects_only=True
            )
        else:
            raise ValueError(f"Unsupported export format: {file_format}")

    def get_supported_formats(self) -> List[str]:
        return ["blend", "glb", "gltf", "fbx", "obj", "stl", "ply", "dae", "usd", "usdc", "usda"]

    def get_created_objects(self) -> List[Any]:
        """Return list of Blender objects created by this backend."""
        return self._created_objects.copy()

    def clear_created_objects(self) -> None:
        """Remove all objects created by this backend from the scene."""
        bpy = self._bpy
        for obj in self._created_objects:
            if obj.name in bpy.data.objects:
                bpy.data.objects.remove(obj, do_unlink=True)
        self._created_objects.clear()


class NumpySTLBackend(MeshBackend):
    """Lightweight mesh backend using numpy-stl (STL output only)."""

    def __init__(self):
        from stl import mesh as stl_mesh
        import numpy as np
        self._stl_mesh = stl_mesh
        self._np = np
        self._meshes_cache: List[Any] = []
    
    @property
    def name(self) -> str:
        return "numpy-stl"
    
    def _create_sphere_vertices_faces(self, radius, subdivisions):
        """Create icosphere vertices and faces."""
        # Golden ratio
        t = (1.0 + self._np.sqrt(5.0)) / 2.0
        
        # Initial icosahedron vertices
        vertices = self._np.array([
            [-1, t, 0], [1, t, 0], [-1, -t, 0], [1, -t, 0],
            [0, -1, t], [0, 1, t], [0, -1, -t], [0, 1, -t],
            [t, 0, -1], [t, 0, 1], [-t, 0, -1], [-t, 0, 1]
        ], dtype=float)
        
        # Normalize to unit sphere
        vertices /= self._np.linalg.norm(vertices[0])
        
        # Initial icosahedron faces
        faces = self._np.array([
            [0, 11, 5], [0, 5, 1], [0, 1, 7], [0, 7, 10], [0, 10, 11],
            [1, 5, 9], [5, 11, 4], [11, 10, 2], [10, 7, 6], [7, 1, 8],
            [3, 9, 4], [3, 4, 2], [3, 2, 6], [3, 6, 8], [3, 8, 9],
            [4, 9, 5], [2, 4, 11], [6, 2, 10], [8, 6, 7], [9, 8, 1]
        ], dtype=int)
        
        # Subdivide
        for _ in range(subdivisions):
            new_faces = []
            midpoint_cache = {}
            
            for tri in faces:
                v = [vertices[tri[i]] for i in range(3)]
                mids = []
                for i in range(3):
                    edge = tuple(sorted([tri[i], tri[(i+1)%3]]))
                    if edge not in midpoint_cache:
                        mid = (v[i] + v[(i+1)%3]) / 2
                        mid /= self._np.linalg.norm(mid)
                        midpoint_cache[edge] = len(vertices)
                        vertices = self._np.vstack([vertices, mid])
                    mids.append(midpoint_cache[edge])
                
                new_faces.extend([
                    [tri[0], mids[0], mids[2]],
                    [tri[1], mids[1], mids[0]],
                    [tri[2], mids[2], mids[1]],
                    [mids[0], mids[1], mids[2]]
                ])
            faces = self._np.array(new_faces)
        
        return vertices * radius, faces
    
    def create_sphere(
        self,
        radius: float,
        center: Tuple[float, float, float],
        subdivisions: int = 2
    ) -> MeshData:
        vertices, faces = self._create_sphere_vertices_faces(radius, subdivisions)
        vertices = vertices + self._np.array(center)
        return MeshData(vertices=vertices, faces=faces)
    
    def create_cylinder(
        self,
        radius: float,
        height: float,
        center: Tuple[float, float, float],
        rotation_degrees: Tuple[float, float, float] = (90, 0, 0),
        sections: int = 16
    ) -> MeshData:
        # Create cylinder along Z axis, then rotate
        angles = self._np.linspace(0, 2*self._np.pi, sections, endpoint=False)
        
        # Bottom and top circles
        bottom = self._np.column_stack([
            radius * self._np.cos(angles),
            radius * self._np.sin(angles),
            self._np.full(sections, -height/2)
        ])
        top = self._np.column_stack([
            radius * self._np.cos(angles),
            radius * self._np.sin(angles),
            self._np.full(sections, height/2)
        ])
        
        # Center points for caps
        bottom_center = self._np.array([[0, 0, -height/2]])
        top_center = self._np.array([[0, 0, height/2]])
        
        vertices = self._np.vstack([bottom, top, bottom_center, top_center])
        
        # Build faces
        faces = []
        bc_idx = 2 * sections
        tc_idx = 2 * sections + 1
        
        for i in range(sections):
            ni = (i + 1) % sections
            # Side faces (two triangles per quad)
            faces.append([i, ni, sections + i])
            faces.append([ni, sections + ni, sections + i])
            # Bottom cap
            faces.append([bc_idx, ni, i])
            # Top cap
            faces.append([tc_idx, sections + i, sections + ni])
        
        faces = self._np.array(faces)
        
        # Apply rotation
        from scipy.spatial.transform import Rotation
        R = Rotation.from_euler('xyz', rotation_degrees, degrees=True).as_matrix()
        vertices = vertices @ R.T
        vertices = vertices + self._np.array(center)
        
        return MeshData(vertices=vertices, faces=faces)
    
    def create_box(
        self,
        extents: Tuple[float, float, float],
        center: Tuple[float, float, float],
        rotation_degrees: Tuple[float, float, float] = (0, 0, 0)
    ) -> MeshData:
        w, h, d = [e/2 for e in extents]
        
        vertices = self._np.array([
            [-w, -h, -d], [w, -h, -d], [w, h, -d], [-w, h, -d],
            [-w, -h, d], [w, -h, d], [w, h, d], [-w, h, d]
        ])
        
        faces = self._np.array([
            [0, 1, 2], [0, 2, 3],  # back
            [4, 6, 5], [4, 7, 6],  # front
            [0, 4, 5], [0, 5, 1],  # bottom
            [2, 6, 7], [2, 7, 3],  # top
            [0, 3, 7], [0, 7, 4],  # left
            [1, 5, 6], [1, 6, 2],  # right
        ])
        
        # Apply rotation
        if any(r != 0 for r in rotation_degrees):
            from scipy.spatial.transform import Rotation
            R = Rotation.from_euler('xyz', rotation_degrees, degrees=True).as_matrix()
            vertices = vertices @ R.T
        
        vertices = vertices + self._np.array(center)
        
        return MeshData(vertices=vertices, faces=faces)
    
    def export(
        self,
        meshes: List[MeshData],
        filepath: str,
        file_format: Optional[str] = None
    ) -> None:
        # Combine all meshes
        all_vertices = []
        all_faces = []
        vertex_offset = 0
        
        for mesh in meshes:
            all_vertices.append(mesh.vertices)
            all_faces.append(mesh.faces + vertex_offset)
            vertex_offset += len(mesh.vertices)
        
        vertices = self._np.vstack(all_vertices)
        faces = self._np.vstack(all_faces)
        
        # Create STL mesh
        stl = self._stl_mesh.Mesh(self._np.zeros(len(faces), dtype=self._stl_mesh.Mesh.dtype))
        for i, f in enumerate(faces):
            for j in range(3):
                stl.vectors[i][j] = vertices[f[j]]
        
        stl.save(filepath)
    
    def get_supported_formats(self) -> List[str]:
        return ["stl"]


def _check_available(module_name: str) -> bool:
    """Check if a module is available for import."""
    return importlib.util.find_spec(module_name) is not None


def get_available_backends() -> List[str]:
    """Return list of available backend names."""
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
    """Check if we're running inside Blender."""
    return _check_available("bpy")


def create_backend(name: Optional[str] = None) -> MeshBackend:
    """
    Create a mesh backend instance.

    Args:
        name: Backend name ("trimesh", "open3d", "numpy-stl", "blender").
              If None, selects best available.

    Returns:
        MeshBackend instance

    Raises:
        ImportError: If requested backend is not available
        ValueError: If no backends are available
    """
    available = get_available_backends()

    if not available:
        raise ValueError(
            "No mesh backends available. Install one of: "
            "trimesh, open3d, or numpy-stl"
        )

    if name is None:
        # Prefer blender if running inside Blender, otherwise trimesh > open3d > numpy-stl
        if is_running_in_blender():
            name = "blender"
        else:
            for preferred in ["trimesh", "open3d", "numpy-stl"]:
                if preferred in available:
                    name = preferred
                    break

    if name not in available:
        raise ImportError(
            f"Backend '{name}' not available. "
            f"Available backends: {available}"
        )

    if name == "trimesh":
        return TrimeshBackend()
    elif name == "open3d":
        return Open3DBackend()
    elif name == "numpy-stl":
        return NumpySTLBackend()
    elif name == "blender":
        return BlenderBackend()
    else:
        raise ValueError(f"Unknown backend: {name}")

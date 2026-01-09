bl_info = {
    "name": "Figure Generator",
    "author": "Figure Generator Contributors",
    "version": (1, 0, 0),
    "blender": (3, 0, 0),
    "location": "View3D > Add > Mesh > Figure",
    "description": "Generate anatomically-proportioned figure primitive meshes for sculpting",
    "category": "Add Mesh",
}

import math

import bmesh
import bpy
from bpy.props import (
    BoolProperty,
    EnumProperty,
    FloatProperty,
)
from bpy.types import Operator
from mathutils import Matrix

# Try to import from the package, fall back to inline definitions for standalone addon
try:
    from .presets import POSES, PRESETS
except ImportError:
    # Standalone addon installation - define presets inline
    POSES = {
        "apose": 45.0,
        "tpose": 90.0,
        "relaxed": 20.0,
    }

    PRESETS = {
        "female_adult": {
            "name": "Adult Female",
            "total_heads": 7.5,
            "head_radius": 0.5,
            "subdivisions": 2,
            "neck": {"radius": 0.11, "length": 0.35},
            "ribcage": {"width": 1.05, "height": 1.25, "depth": 0.55},
            "breasts": {"radius": 0.18, "offset_x": 0.22, "offset_z": 0.32, "offset_y": -0.1},
            "abdomen": {"radius": 0.30, "length": 0.55},
            "pelvis": {"width": 1.1, "height": 0.7, "depth": 0.5},
            "glutes": {"radius": 0.24, "offset_x": 0.2, "offset_y": -0.15, "offset_z": -0.22},
            "upper_arm": {"radius": 0.105, "length": 1.15},
            "forearm": {"radius": 0.08, "length": 1.0},
            "hand": {"width": 0.09, "length": 0.32, "depth": 0.04},
            "thigh": {"radius": 0.17, "length": 1.75},
            "calf": {"radius": 0.12, "length": 1.7},
            "foot": {"width": 0.14, "height": 0.1, "length": 0.38},
            "shoulder_width": 0.55,
            "hip_width": 0.28,
            "landmarks": {
                "shoulder_y": 5.9,
                "bust_y": 5.4,
                "waist_y": 4.6,
                "pelvis_y": 4.0,
                "crotch_y": 3.65,
                "knee_y": 1.9,
            },
        },
        "male_adult": {
            "name": "Adult Male",
            "total_heads": 8.0,
            "head_radius": 0.5,
            "subdivisions": 2,
            "neck": {"radius": 0.14, "length": 0.35},
            "ribcage": {"width": 1.25, "height": 1.35, "depth": 0.6},
            "breasts": None,
            "abdomen": {"radius": 0.38, "length": 0.55},
            "pelvis": {"width": 0.95, "height": 0.65, "depth": 0.48},
            "glutes": {"radius": 0.2, "offset_x": 0.18, "offset_y": -0.15, "offset_z": -0.2},
            "upper_arm": {"radius": 0.13, "length": 1.25},
            "forearm": {"radius": 0.095, "length": 1.1},
            "hand": {"width": 0.11, "length": 0.38, "depth": 0.05},
            "thigh": {"radius": 0.18, "length": 1.85},
            "calf": {"radius": 0.13, "length": 1.8},
            "foot": {"width": 0.16, "height": 0.12, "length": 0.42},
            "shoulder_width": 0.65,
            "hip_width": 0.26,
            "landmarks": {
                "shoulder_y": 6.3,
                "bust_y": 5.8,
                "waist_y": 4.9,
                "pelvis_y": 4.2,
                "crotch_y": 3.85,
                "knee_y": 2.0,
            },
        },
        "child": {
            "name": "Child (6-8 years)",
            "total_heads": 6.0,
            "head_radius": 0.55,
            "subdivisions": 2,
            "neck": {"radius": 0.09, "length": 0.25},
            "ribcage": {"width": 0.85, "height": 0.9, "depth": 0.45},
            "breasts": None,
            "abdomen": {"radius": 0.28, "length": 0.45},
            "pelvis": {"width": 0.75, "height": 0.5, "depth": 0.4},
            "glutes": {"radius": 0.16, "offset_x": 0.14, "offset_y": -0.1, "offset_z": -0.15},
            "upper_arm": {"radius": 0.07, "length": 0.8},
            "forearm": {"radius": 0.055, "length": 0.7},
            "hand": {"width": 0.07, "length": 0.22, "depth": 0.03},
            "thigh": {"radius": 0.11, "length": 1.1},
            "calf": {"radius": 0.08, "length": 1.0},
            "foot": {"width": 0.1, "height": 0.08, "length": 0.28},
            "shoulder_width": 0.45,
            "hip_width": 0.2,
            "landmarks": {
                "shoulder_y": 4.7,
                "bust_y": 4.3,
                "waist_y": 3.7,
                "pelvis_y": 3.3,
                "crotch_y": 3.0,
                "knee_y": 1.5,
            },
        },
        "heroic": {
            "name": "Heroic/Idealized (8.5 heads)",
            "total_heads": 8.5,
            "head_radius": 0.5,
            "subdivisions": 2,
            "neck": {"radius": 0.15, "length": 0.4},
            "ribcage": {"width": 1.4, "height": 1.45, "depth": 0.65},
            "breasts": None,
            "abdomen": {"radius": 0.42, "length": 0.6},
            "pelvis": {"width": 1.0, "height": 0.7, "depth": 0.5},
            "glutes": {"radius": 0.22, "offset_x": 0.2, "offset_y": -0.15, "offset_z": -0.22},
            "upper_arm": {"radius": 0.15, "length": 1.35},
            "forearm": {"radius": 0.11, "length": 1.2},
            "hand": {"width": 0.12, "length": 0.4, "depth": 0.05},
            "thigh": {"radius": 0.2, "length": 2.0},
            "calf": {"radius": 0.14, "length": 1.9},
            "foot": {"width": 0.17, "height": 0.13, "length": 0.45},
            "shoulder_width": 0.75,
            "hip_width": 0.28,
            "landmarks": {
                "shoulder_y": 6.7,
                "bust_y": 6.1,
                "waist_y": 5.2,
                "pelvis_y": 4.5,
                "crotch_y": 4.1,
                "knee_y": 2.1,
            },
        },
    }


# =============================================================================
# Mesh Generation Utilities (Z-up coordinate system)
# =============================================================================


def create_icosphere(radius, center, subdivisions=2):
    """Create an icosphere mesh at center (X, Y, Z) in Blender coords."""
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=subdivisions, radius=radius)
    bmesh.ops.translate(bm, verts=bm.verts, vec=center)
    return bm


def create_cylinder_z(radius, height, center, sections=16):
    """Create a cylinder along Z axis (vertical in Blender)."""
    bm = bmesh.new()
    bmesh.ops.create_cone(
        bm,
        cap_ends=True,
        cap_tris=False,
        segments=sections,
        radius1=radius,
        radius2=radius,
        depth=height,
    )
    # Cylinder is already along Z by default
    bmesh.ops.translate(bm, verts=bm.verts, vec=center)
    return bm


def create_cylinder_arm(radius, length, center, arm_angle_deg, is_left, sections=16):
    """Create a cylinder for an arm segment.

    arm_angle_deg: 0 = straight down, 90 = horizontal (T-pose)
    The cylinder tilts outward from vertical.

    The cylinder is created along Z axis. We need to rotate it to point
    DOWN and outward (toward +X for left, -X for right).

    Rotation around Y axis: (0,0,1) -> (sin(θ), 0, cos(θ))
    - To point down (-Z): θ = 180° gives (0, 0, -1)
    - To point right (+X): θ = 90° gives (1, 0, 0)
    - To point down-right at 45°: θ = 135° gives (0.707, 0, -0.707)

    Formula: rotation = 180° - arm_angle for left arm
             rotation = -(180° - arm_angle) for right arm
    """
    bm = bmesh.new()
    bmesh.ops.create_cone(
        bm,
        cap_ends=True,
        cap_tris=False,
        segments=sections,
        radius1=radius,
        radius2=radius,
        depth=length,
    )

    # Calculate rotation to point arm down and outward
    sign = 1 if is_left else -1
    rotation_deg = sign * (180.0 - arm_angle_deg)
    rot_mat = Matrix.Rotation(math.radians(rotation_deg), 4, "Y")
    bmesh.ops.transform(bm, matrix=rot_mat, verts=bm.verts)

    bmesh.ops.translate(bm, verts=bm.verts, vec=center)
    return bm


def create_box(size_x, size_y, size_z, center, rotation_y_deg=0):
    """Create a box with given dimensions at center.

    size_x: width (left-right)
    size_y: depth (front-back)
    size_z: height (up-down)
    """
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)

    # Scale to dimensions
    for v in bm.verts:
        v.co.x *= size_x
        v.co.y *= size_y
        v.co.z *= size_z

    # Rotate if needed
    if rotation_y_deg != 0:
        rot_mat = Matrix.Rotation(math.radians(rotation_y_deg), 4, "Y")
        bmesh.ops.transform(bm, matrix=rot_mat, verts=bm.verts)

    bmesh.ops.translate(bm, verts=bm.verts, vec=center)
    return bm


def bmesh_to_object(bm, name, collection):
    """Convert bmesh to Blender object and add to collection."""
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()

    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    return obj


# =============================================================================
# Figure Generator Core
# =============================================================================


def generate_figure(context, preset_name, arm_angle, scale=1.0, location=(0, 0, 0)):
    """Generate a figure in the scene using Blender's Z-up coordinate system."""
    preset = PRESETS[preset_name]

    # Create or get collection
    collection_name = "Figure"
    if collection_name in bpy.data.collections:
        collection = bpy.data.collections[collection_name]
    else:
        collection = bpy.data.collections.new(collection_name)
        context.scene.collection.children.link(collection)

    created_objects = []
    subdivisions = preset["subdivisions"]
    landmarks = preset["landmarks"]

    def s(value):
        """Scale a value."""
        return value * scale

    def pos(x, z, y=0):
        """Create position with offset. Note: preset uses Y for height, we use Z."""
        return (x * scale + location[0], y * scale + location[1], z * scale + location[2])

    # === HEAD ===
    head_height = preset["total_heads"] - preset["head_radius"]
    bm = create_icosphere(s(preset["head_radius"]), pos(0, head_height), subdivisions)
    obj = bmesh_to_object(bm, "Head", collection)
    created_objects.append(obj)

    # === NECK ===
    neck = preset["neck"]
    neck_height = head_height - preset["head_radius"] - neck["length"] / 2
    bm = create_cylinder_z(s(neck["radius"]), s(neck["length"]), pos(0, neck_height))
    obj = bmesh_to_object(bm, "Neck", collection)
    created_objects.append(obj)

    # === RIBCAGE ===
    ribcage = preset["ribcage"]
    ribcage_height = landmarks["shoulder_y"] - ribcage["height"] / 2 + 0.4
    bm = create_box(
        s(ribcage["width"]), s(ribcage["depth"]), s(ribcage["height"]), pos(0, ribcage_height)
    )
    obj = bmesh_to_object(bm, "Ribcage", collection)
    created_objects.append(obj)

    # === BREASTS (optional) ===
    if preset["breasts"] is not None:
        breasts = preset["breasts"]
        breast_height = landmarks["bust_y"]

        bm = create_icosphere(
            s(breasts["radius"]),
            pos(breasts["offset_x"], breast_height, breasts["offset_z"]),
            subdivisions,
        )
        obj = bmesh_to_object(bm, "Breast_Left", collection)
        created_objects.append(obj)

        bm = create_icosphere(
            s(breasts["radius"]),
            pos(-breasts["offset_x"], breast_height, breasts["offset_z"]),
            subdivisions,
        )
        obj = bmesh_to_object(bm, "Breast_Right", collection)
        created_objects.append(obj)

    # === ABDOMEN ===
    abdomen = preset["abdomen"]
    bm = create_cylinder_z(s(abdomen["radius"]), s(abdomen["length"]), pos(0, landmarks["waist_y"]))
    obj = bmesh_to_object(bm, "Abdomen", collection)
    created_objects.append(obj)

    # === PELVIS ===
    pelvis = preset["pelvis"]
    bm = create_box(
        s(pelvis["width"]), s(pelvis["depth"]), s(pelvis["height"]), pos(0, landmarks["pelvis_y"])
    )
    obj = bmesh_to_object(bm, "Pelvis", collection)
    created_objects.append(obj)

    # === GLUTES ===
    glutes = preset["glutes"]
    glute_height = landmarks["pelvis_y"] + glutes["offset_y"]

    bm = create_icosphere(
        s(glutes["radius"]), pos(glutes["offset_x"], glute_height, glutes["offset_z"]), subdivisions
    )
    obj = bmesh_to_object(bm, "Glute_Left", collection)
    created_objects.append(obj)

    bm = create_icosphere(
        s(glutes["radius"]),
        pos(-glutes["offset_x"], glute_height, glutes["offset_z"]),
        subdivisions,
    )
    obj = bmesh_to_object(bm, "Glute_Right", collection)
    created_objects.append(obj)

    # === ARMS ===
    shoulder_x = preset["shoulder_width"]
    shoulder_height = landmarks["shoulder_y"]

    upper_arm = preset["upper_arm"]
    forearm = preset["forearm"]
    hand = preset["hand"]

    angle_rad = math.radians(arm_angle)

    for side, sign, is_left in [("Left", 1, True), ("Right", -1, False)]:
        # Upper arm position: starts at shoulder, extends outward and down
        # At angle 0: straight down. At angle 90: horizontal (T-pose)
        ua_horizontal = math.sin(angle_rad) * upper_arm["length"] / 2
        ua_vertical = math.cos(angle_rad) * upper_arm["length"] / 2

        ua_center = pos(sign * (shoulder_x + ua_horizontal), shoulder_height - ua_vertical)

        bm = create_cylinder_arm(
            s(upper_arm["radius"]), s(upper_arm["length"]), ua_center, arm_angle, is_left
        )
        obj = bmesh_to_object(bm, f"UpperArm_{side}", collection)
        created_objects.append(obj)

        # Elbow position
        elbow_x = shoulder_x + math.sin(angle_rad) * upper_arm["length"]
        elbow_height = shoulder_height - math.cos(angle_rad) * upper_arm["length"]

        # Forearm
        fa_horizontal = math.sin(angle_rad) * forearm["length"] / 2
        fa_vertical = math.cos(angle_rad) * forearm["length"] / 2

        fa_center = pos(sign * (elbow_x + fa_horizontal), elbow_height - fa_vertical)

        bm = create_cylinder_arm(
            s(forearm["radius"]), s(forearm["length"]), fa_center, arm_angle, is_left
        )
        obj = bmesh_to_object(bm, f"Forearm_{side}", collection)
        created_objects.append(obj)

        # Wrist position
        wrist_x = elbow_x + math.sin(angle_rad) * forearm["length"]
        wrist_height = elbow_height - math.cos(angle_rad) * forearm["length"]

        # Hand
        hand_horizontal = math.sin(angle_rad) * hand["length"] / 2
        hand_vertical = math.cos(angle_rad) * hand["length"] / 2

        hand_center = pos(sign * (wrist_x + hand_horizontal), wrist_height - hand_vertical)

        # Hand box rotated to align with arm (same rotation as arm cylinders)
        hand_rotation = sign * (180.0 - arm_angle)
        bm = create_box(
            s(hand["width"]),
            s(hand["depth"]),
            s(hand["length"]),
            hand_center,
            rotation_y_deg=hand_rotation,
        )
        obj = bmesh_to_object(bm, f"Hand_{side}", collection)
        created_objects.append(obj)

    # === LEGS ===
    hip_x = preset["hip_width"]
    crotch_height = landmarks["crotch_y"]

    thigh = preset["thigh"]
    calf = preset["calf"]
    foot = preset["foot"]

    for side, sign in [("Left", 1), ("Right", -1)]:
        # Thigh
        thigh_center = pos(sign * hip_x, crotch_height - thigh["length"] / 2)
        bm = create_cylinder_z(s(thigh["radius"]), s(thigh["length"]), thigh_center)
        obj = bmesh_to_object(bm, f"Thigh_{side}", collection)
        created_objects.append(obj)

        # Knee position
        knee_height = crotch_height - thigh["length"]

        # Calf
        calf_center = pos(sign * hip_x, knee_height - calf["length"] / 2)
        bm = create_cylinder_z(s(calf["radius"]), s(calf["length"]), calf_center)
        obj = bmesh_to_object(bm, f"Calf_{side}", collection)
        created_objects.append(obj)

        # Foot - on the ground, extending forward (+Y in Blender)
        foot_center = pos(
            sign * hip_x,
            foot["height"] / 2,  # Height (Z)
            foot["length"] / 2 - 0.12,  # Forward offset (Y)
        )
        bm = create_box(s(foot["width"]), s(foot["length"]), s(foot["height"]), foot_center)
        obj = bmesh_to_object(bm, f"Foot_{side}", collection)
        created_objects.append(obj)

    return created_objects


# =============================================================================
# Blender Operators
# =============================================================================


class MESH_OT_figure_generator(Operator):
    """Generate an anatomically-proportioned figure mesh"""

    bl_idname = "mesh.figure_generator"
    bl_label = "Figure"
    bl_options = {"REGISTER", "UNDO"}

    preset: EnumProperty(
        name="Preset",
        description="Figure preset to use",
        items=[
            ("female_adult", "Female Adult", "Adult female proportions (7.5 heads)"),
            ("male_adult", "Male Adult", "Adult male proportions (8 heads)"),
            ("child", "Child", "Child proportions 6-8 years (6 heads)"),
            ("heroic", "Heroic", "Stylized heroic proportions (8.5 heads)"),
        ],
        default="female_adult",
    )

    pose: EnumProperty(
        name="Pose",
        description="Arm pose preset",
        items=[
            ("apose", "A-Pose", "45 degree arms, ideal for sculpting"),
            ("tpose", "T-Pose", "90 degree arms, ideal for rigging"),
            ("relaxed", "Relaxed", "15 degree arms, more natural pose"),
            ("custom", "Custom", "Use custom arm angle"),
        ],
        default="apose",
    )

    arm_angle: FloatProperty(
        name="Arm Angle",
        description="Custom arm angle in degrees (0=down, 90=horizontal)",
        default=45.0,
        min=0.0,
        max=180.0,
        subtype="ANGLE",
    )

    scale: FloatProperty(
        name="Scale", description="Overall scale of the figure", default=1.0, min=0.01, max=100.0
    )

    join_meshes: BoolProperty(
        name="Join Meshes", description="Join all parts into a single mesh", default=False
    )

    def execute(self, context):
        if self.pose == "custom":
            arm_angle = math.degrees(self.arm_angle)
        else:
            arm_angle = POSES[self.pose]

        location = context.scene.cursor.location.copy()

        objects = generate_figure(
            context, self.preset, arm_angle, scale=self.scale, location=tuple(location)
        )

        bpy.ops.object.select_all(action="DESELECT")
        for obj in objects:
            obj.select_set(True)

        if objects:
            context.view_layer.objects.active = objects[0]

        if self.join_meshes and len(objects) > 1:
            bpy.ops.object.join()
            context.active_object.name = f"Figure_{self.preset}"

        self.report({"INFO"}, f"Generated {len(objects)} figure parts")
        return {"FINISHED"}

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "preset")
        layout.separator()
        layout.prop(self, "pose")
        if self.pose == "custom":
            layout.prop(self, "arm_angle")
        layout.separator()
        layout.prop(self, "scale")
        layout.separator()
        layout.prop(self, "join_meshes")

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=300)


class MESH_OT_figure_female(Operator):
    """Generate female adult figure"""

    bl_idname = "mesh.figure_female"
    bl_label = "Female Adult"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        location = context.scene.cursor.location.copy()
        objects = generate_figure(context, "female_adult", 45.0, location=tuple(location))
        bpy.ops.object.select_all(action="DESELECT")
        for obj in objects:
            obj.select_set(True)
        if objects:
            context.view_layer.objects.active = objects[0]
        return {"FINISHED"}


class MESH_OT_figure_male(Operator):
    """Generate male adult figure"""

    bl_idname = "mesh.figure_male"
    bl_label = "Male Adult"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        location = context.scene.cursor.location.copy()
        objects = generate_figure(context, "male_adult", 45.0, location=tuple(location))
        bpy.ops.object.select_all(action="DESELECT")
        for obj in objects:
            obj.select_set(True)
        if objects:
            context.view_layer.objects.active = objects[0]
        return {"FINISHED"}


class MESH_OT_figure_child(Operator):
    """Generate child figure"""

    bl_idname = "mesh.figure_child"
    bl_label = "Child"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        location = context.scene.cursor.location.copy()
        objects = generate_figure(context, "child", 45.0, location=tuple(location))
        bpy.ops.object.select_all(action="DESELECT")
        for obj in objects:
            obj.select_set(True)
        if objects:
            context.view_layer.objects.active = objects[0]
        return {"FINISHED"}


class MESH_OT_figure_heroic(Operator):
    """Generate heroic/stylized figure"""

    bl_idname = "mesh.figure_heroic"
    bl_label = "Heroic"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        location = context.scene.cursor.location.copy()
        objects = generate_figure(context, "heroic", 45.0, location=tuple(location))
        bpy.ops.object.select_all(action="DESELECT")
        for obj in objects:
            obj.select_set(True)
        if objects:
            context.view_layer.objects.active = objects[0]
        return {"FINISHED"}


# =============================================================================
# Menu
# =============================================================================


class MESH_MT_figure_submenu(bpy.types.Menu):
    bl_idname = "MESH_MT_figure_submenu"
    bl_label = "Figure"

    def draw(self, context):
        layout = self.layout
        layout.operator("mesh.figure_generator", text="Figure (Custom)...", icon="ARMATURE_DATA")
        layout.separator()
        layout.operator("mesh.figure_female", icon="USER")
        layout.operator("mesh.figure_male", icon="USER")
        layout.operator("mesh.figure_child", icon="USER")
        layout.operator("mesh.figure_heroic", icon="USER")


def menu_func(self, context):
    self.layout.menu("MESH_MT_figure_submenu", icon="ARMATURE_DATA")


# =============================================================================
# Registration
# =============================================================================

classes = (
    MESH_OT_figure_generator,
    MESH_OT_figure_female,
    MESH_OT_figure_male,
    MESH_OT_figure_child,
    MESH_OT_figure_heroic,
    MESH_MT_figure_submenu,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.VIEW3D_MT_mesh_add.append(menu_func)


def unregister():
    bpy.types.VIEW3D_MT_mesh_add.remove(menu_func)
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()

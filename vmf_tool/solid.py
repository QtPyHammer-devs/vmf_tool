from __future__ import annotations

import re
from typing import List

from . import parser
from . import vector


class Brush:
    _source: parser.Namespace
    colour: List[float] = (1.0, 0.0, 1.0)
    faces: list[Face] = []
    id: int = 0
    is_displacement: bool = False  # change to property

    @staticmethod
    def from_bounds(mins: List[float], maxs: List[float], material: str = "TOOLS/TOOLSNODRAW") -> Brush:
        """Make cube"""
        mins, maxs = vector.vec3(*mins), vector.vec3(*maxs)
        brush = Brush()

        def face(*points):
            return Face.from_polygon([*map(lambda P: vector.vec3(*P), points)], material)
        z = maxs.z
        pos_Z = face((mins.x, maxs.y, z), (maxs.x, maxs.y, z), (maxs.x, mins.y, z), (mins.x, mins.y, z))
        z = mins.z
        neg_Z = face((mins.x, mins.y, z), (mins.x, maxs.y, z), (maxs.x, maxs.y, z), (maxs.x, mins.y, z))
        y = maxs.y
        pos_Y = face((mins.x, y, maxs.z), (mins.x, y, mins.z), (maxs.x, y, mins.z), (maxs.x, y, maxs.z))
        y = mins.y
        neg_Y = face((mins.x, y, mins.z), (mins.x, y, maxs.z), (maxs.x, y, maxs.z), (maxs.x, y, mins.z))
        x = maxs.x
        pos_X = face((x, maxs.y, maxs.z), (x, maxs.y, mins.z), (x, mins.y, mins.z), (x, mins.y, maxs.z))
        x = mins.x
        neg_X = face((x, mins.y, mins.z), (x, maxs.y, mins.z), (x, maxs.y, maxs.z), (x, mins.y, maxs.z))
        brush.faces = [pos_Z, neg_Z, pos_Y, neg_Y, pos_X, neg_X]
        return brush

    @staticmethod
    def from_namespace(solid: parser.Namespace) -> Brush:
        """Initialise from namespace (vmf import)"""
        brush = Brush()
        brush._source = solid  # preserved for debugging
        brush.id = int(solid.id)
        brush.colour = tuple(int(x) / 255 for x in solid.editor.color.split())

        brush.faces = [*map(Face.from_namespace, solid.side)]
        if any([hasattr(f, "displacement") for f in brush.faces]):
            brush.is_displacement = True
            # TODO: make this a property

        for i, f in enumerate(brush.faces):
            normal, distance = f.plane
            if abs(normal.z) != 1:
                non_parallel = vector.vec3(z=-1)
            else:
                non_parallel = vector.vec3(y=-1)
            local_y = (non_parallel * normal).normalise()
            local_x = (local_y * normal).normalise()
            center = sum(f.polygon, vector.vec3()) / 3
            # ^ centered on string triangle, but rounding errors abound
            # however, using vector.vec3 does mean math.fsum is utilitsed
            radius = 10 ** 4  # should be larger than any reasonable brush
            ngon = [center + ((-local_x + local_y) * radius),
                    center + ((local_x + local_y) * radius),
                    center + ((local_x + -local_y) * radius),
                    center + ((-local_x + -local_y) * radius)]
            for other_f in brush.faces:
                if other_f.plane == f.plane:  # skip yourself
                    continue
                ngon, offcut = clip(ngon, other_f.plane).values()
            brush.faces[i].polygon = ngon
            if hasattr(f, "displacement") and len(ngon) != 4:
                raise RuntimeError("face id {f.id}'s displacement is invalid (face has {len(ngon)} sides)")
                # solid is probably invalid
        return brush

    def as_namespace(self) -> parser.Namespace:
        self._source.id = str(self.id)
        self._source.side = [f.as_namespace() for f in self.faces]
        self._source.editor.color = " ".join([str(int(255 * x)) for x in self.colour])
        # TODO: update hidden state
        return self._source

    def __iter__(self):
        return iter(self.faces)

    def __repr__(self):
        return f"<Solid id={self.id}, {len(self.faces)} sides>"

    def translate(self, offset: vector.vec3, texture_lock=False, displacement_lock=False):
        # apply offset to plane & polygon of each face
        # if texture lock is ON, recalculate each face's UV axes
        # if displacement_lock is ON, recalculate all displacement normals & distances
        raise NotImplementedError()


class Displacement:
    alphas: List[List[vector.vec3]] = []
    distances: List[List[float]] = []
    elevation: int = 0
    flags: int = 0
    normals: List[List[vector.vec3]] = []
    power: int = 2
    start: vector.vec3
    subdivided: bool = False
    allowed_verts: List[int]  # "10" "-1 -1 -1 -1 -1 -1 -1 -1 -1 -1"
    offset_normals: List[List[vector.vec3]] = []
    offsets: List[List[vector.vec3]] = []
    triangle_tags: List[List[int]] = []  # walkable, buildable etc.

    @staticmethod
    def from_namespace(dispinfo: parser.Namespace) -> Displacement:
        disp = Displacement()
        disp.power = int(dispinfo.power)
        disp.start = vector.vec3(*map(float, re.findall(r"(?<=[\[\ ]).+?(?=[\ \]])", dispinfo.startposition)))
        disp.flags = int(dispinfo.flags)
        disp.elevation = int(dispinfo.elevation)
        disp.subdivided = bool(dispinfo.subdiv)
        def floats(s): return tuple(map(float, s.split(" ")))
        row_count = (2 ** disp.power) + 1
        for i in range(row_count):
            row = f"row{i}"
            row_normals, row_offsets, row_offset_normals = [], [], []
            normal_strings = dispinfo.normals[row].split(" ")
            offset_strings = dispinfo.offsets[row].split(" ")
            offset_normal_strings = dispinfo.offset_normals[row].split(" ")
            for i in range(0, row_count * 3, 3):  # get vectors
                normal = " ".join(normal_strings[i:i+3])
                row_normals.append(vector.vec3(*floats(normal)))
                offset = " ".join(offset_strings[i:i+3])
                row_offsets.append(vector.vec3(*floats(offset)))
                offset_normal = " ".join(offset_normal_strings[i:i+3])
                row_offset_normals.append(vector.vec3(*floats(offset_normal)))
            disp.alphas.append(floats(dispinfo.alphas[row]))
            disp.distances.append(floats(dispinfo.distances[row]))
            disp.normals.append(row_normals)
            disp.offset_normals.append(row_offset_normals)
            disp.offsets.append(row_offsets)
        for i in range(row_count - 1):
            row = f"row{i}"
            # there are (2 ** power) * 2 triangles per row
            disp.triangle_tags.append([*map(int, dispinfo.triangle_tags[row].split(" "))])
        return disp

    def as_namespace(self) -> parser.Namespace:
        dispinfo = parser.Namespace()
        dispinfo.power = str(self.power)
        dispinfo.startposition = f"[{self.start.x} {self.start.y} {self.start.z}]"
        dispinfo.flags = str(self.flags)
        dispinfo.elevation = str(self.elevation)
        dispinfo.subdiv = "1" if self.subdivided else "0"
        # rows
        dispinfo.alphas = parser.Namespace()
        dispinfo.distances = parser.Namespace()
        dispinfo.normals = parser.Namespace()
        dispinfo.offset_normals = parser.Namespace()
        dispinfo.offsets = parser.Namespace()
        dispinfo.triangle_tags = parser.Namespace()
        row_count = (2 ** self.power) + 1
        for i in range(row_count):
            row = f"row{i}"
            dispinfo.alphas[row] = " ".join(map(str, self.alphas[i]))
            dispinfo.triangle_tags[row] = " ".join(map(str, self.triangle_tags[i]))
            dispinfo.distances[row] = " ".join(map(str, self.distances[i]))
            dispinfo.normals[row] = " ".join([f"{n.x} {n.y} {n.z}" for n in self.normals[i]])
            dispinfo.offset_normals[row] = " ".join([f"{on.x} {on.y} {on.z}" for on in self.offset_normals[i]])
            dispinfo.offsets[row] = " ".join([f"{o.x} {o.y} {o.z}" for o in self.offsets[i]])
        dispinfo.allowed_verts = parser.Namespace(**{"10": " ".join(["-1"] * 10)})  # never changes, used for ???
        return dispinfo

    def change_power(self, new_power):
        """simplify / subdivide"""
        raise NotImplementedError()


class Face:
    displacement: Displacement  # optional
    id: int
    lightmap_scale: int
    material: str
    plane: List[float]  # (vec3 normal, float distane)
    polygon: List[vector.vec3] = []
    rotation: float
    smoothing_groups: int
    uaxis: TextureVector
    vaxis: TextureVector

    @staticmethod
    def from_polygon(polygon: List[vector.vec3] = [], material: str = "TOOLS/TOOLSNODRAW") -> Face:
        face = Face()
        if len(polygon) < 3:
            raise RuntimeError(f"{polygon} is not a valid polygon!")
        face.polygon = polygon
        A, B, C = polygon[:3]
        face.plane = plane_of(A, B, C)
        # calculate "face" texture projection
        face.uaxis = TextureVector(*(A - B), 0, 0.25)
        face.vaxis = TextureVector(*(A - polygon[-1]), 0, 0.25)
        face.id = 0  # TODO: each id must be unique
        face.material = material
        face.rotation = 0.0
        face.lightmap_scale = 16
        face.smoothing_groups = 0
        return face

    @staticmethod
    def from_namespace(side: parser.Namespace) -> Face:
        face = Face()
        face.id = int(side.id)
        A, B, C = triangle_of(side.plane)
        face.plane = plane_of(A, B, C)
        # ^ (vec3 normal, float distance)
        face.material = side.material
        face.uaxis = TextureVector.from_string(side.uaxis)
        face.vaxis = TextureVector.from_string(side.vaxis)
        face.rotation = float(side.rotation)
        face.lightmap_scale = int(side.lightmapscale)
        face.smoothing_groups = int(side.smoothing_groups)
        if hasattr(side, "dispinfo"):
            face.displacement = Displacement.from_namespace(side.dispinfo)
        # polygon must be calculated by clipping against other faces
        # Brush.from_namespace calculates polygons automatically
        return face

    def as_namespace(self) -> parser.Namespace:
        side = parser.Namespace()
        side.id = str(self.id)
        # # ON-GRID PLANE:
        # normal, distance = self.plane
        # plane_origin = normal * distance  # snap to grid
        # local_x = ...
        # local_y = ...
        # A, B, C = plane_origin, plane_origin + local_x, plane_origin + local_y
        # # ensure B & C are on grid ...
        # side.plane = " ".join(f"({P.x} {P.y} {P.z})" for P in (A, B, C))
        side.plane = " ".join([f"({P[0]} {P[1]} {P[2]})" for P in self.polygon[:3]])
        # ^ lazy method (accuracy will be lost, solid may become invalid over time)
        side.material = self.material
        side.uaxis = str(self.uaxis)
        side.vaxis = str(self.vaxis)
        side.rotation = str(self.rotation)
        side.lightmapscale = str(self.lightmap_scale)
        side.smoothing_groups = str(self.smoothing_groups)
        if hasattr(self, "displacement"):
            side.dispinfo = self.displacement.as_namespace()
        return side

    def extrude(self, depth) -> Brush:
        """Extrude into a brush"""
        raise NotImplementedError()

    def sew_displacements(self, *others):
        # TODO: .vmf with subdivided disps and .obj model of compiled disp for comparison
        # iirc selecting sewable disps affects the subdivision around the edges, how is this stored in the .vmf?
        # will require a method for represtenting displacement vertices
        raise NotImplementedError()

    def uv_at(self, position: vector.vec3) -> vector.vec2:
        u = self.uaxis.linear_pos(position)
        v = self.vaxis.linear_pos(position)
        return vector.vec2(u, v)


class TextureVector:  # pairing uaxis and vaxis together would be nice
    """Takes uaxis or vaxis"""
    vector: vector.vec3
    offset: float
    scale: float

    def __init__(self, x, y, z, offset, scale):
        self.vector = vector.vec3(x, y, z)
        self.offset = offset
        self.scale = scale

    def __str__(self) -> str:
        return f"[{self.vector.x} {self.vector.y} {self.vector.z} {self.offset}] {self.scale}"

    def align_to_normal(self, normal):
        raise NotImplementedError()

    @staticmethod
    def from_string(texvec: str) -> TextureVector:
        """expects: '[X Y Z Offset] Scale'"""
        x, y, z, offset = map(float, re.findall(r"(?<=[\[\ ]).+?(?=[\ \]])", texvec))
        scale = float(re.search(r"(?<=\ )[^\ ]+$", texvec).group(0))
        return TextureVector(x, y, z, offset, scale)

    def linear_pos(self, position: vector.vec3):
        """half a uv, need 2 TextureVectors for the full uv"""
        return (vector.dot(position, self.vector) + self.offset) / self.scale

    def wrap(self, plane):  # alt + right click
        raise NotImplementedError()


def clip(poly, plane):
    normal, distance = plane
    split_verts = {"back": [], "front": []}  # allows for 3 cutting modes
    for i, A in enumerate(poly):
        B = poly[(i + 1) % len(poly)]
        A_distance = vector.dot(normal, A) - distance
        B_distance = vector.dot(normal, B) - distance
        A_behind = round(A_distance, 6) < 0
        B_behind = round(B_distance, 6) < 0
        if A_behind:
            split_verts["back"].append(A)
        else:  # A is in front of the clipping plane
            split_verts["front"].append(A)
        # does the edge AB intersect the clipping plane?
        if (A_behind and not B_behind) or (B_behind and not A_behind):
            t = A_distance / (A_distance - B_distance)
            cut_point = vector.lerp(A, B, t)
            cut_point = [round(a, 2) for a in cut_point]
            # .vmf floating-point accuracy sucks
            split_verts["back"].append(cut_point)
            split_verts["front"].append(cut_point)
            # ^ won't one of these points be added twice?
    return split_verts


def plane_of(A, B, C):
    """returns the plane (vec3 normal, float distance) the triangle ABC represents"""
    normal = ((A - B) * (C - B)).normalise()
    return (normal, vector.dot(normal, A))


def triangle_of(string):
    """"'(X Y Z) (X Y Z) (X Y Z)' --> (vec3(X, Y, Z), vec3(X, Y, Z), vec3(X, Y, Z))"""
    points = re.findall(r"(?<=\().+?(?=\))", string)
    # print("!~", string, points)
    def vector_of(P): return vector.vec3(*map(float, P.split(" ")))
    return tuple(map(vector_of, points))

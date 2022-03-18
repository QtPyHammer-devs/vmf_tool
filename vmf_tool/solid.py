from __future__ import annotations
import itertools
from typing import Dict, List

import valvevmf

from . import vector


# NOTE: it'd be cool to have type conversion for Quake-based .map files (need parser)
# -- same with GoldSrc .rmf files (also need parser)

_id = 0  # for globally incrementing solid, side & entity ids
# TODO: verify all _ids are unique
# NOTE: users should be allowed to override defaults with their own
# -- expected use is to grab settings from Hammer's GameInfo.txt or QtPyHammer / Hammer++'s .ini files
default = {"allowed_verts": [-1] * 10,
           "color": (1.0, 0, 1.0),
           "lightmap_scale": 16,
           "material": "TOOLS/TOOLSNODRAW",
           "texture_scale": 0.25}


class Brush:
    _source: valvevmf.VmfNode | None  # only present if loaded from / saved to file
    colour: (float, float, float) = default["color"]
    faces: List[Face] = list()
    id: int = 0

    def __iter__(self):
        """for face in brush:"""
        return iter(self.faces)

    def __repr__(self):
        return f"<Solid id={self.id} with {len(self.faces)} sides>"

    @classmethod
    def from_bounds(cls: Brush, mins: List[float], maxs: List[float], material: str = default["material"]) -> Brush:
        """Make a cube"""
        mins = vector.vec3(*mins)
        maxs = vector.vec3(*maxs)
        brush = cls()
        global _id
        _id += 1
        brush.id = _id
        # NOTE: we could do a directional palette... would just need a way to set it in UI...
        # -- palette zoning would also be neat...

        def face(*points):
            return Face.from_polygon([*map(lambda P: vector.vec3(*P), points)], material)

        # NOTE: while it's tempting to generate these points with a loop, it's easier to debug like this
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

    # TODO: extrude from face

    @classmethod
    def from_node(cls: Brush, solid: valvevmf.VmfNode) -> Brush:
        """Initialise from namespace (vmf import)"""
        brush = cls()
        brush._source = solid
        brush.id = dict(solid.properties)["id"]
        # quick & dirty child-node collection
        if not (all([n.name == "side" for n in solid.nodes[:-1]]) and solid.nodes[-1].name == "editor"):
            raise RuntimeError("Invalid Solid; Unexpected / absent child node(s)")
        brush.faces = list(map(Face.from_node, solid.nodes[:-1]))
        brush.colour = tuple(x / 255 for x in dict(solid.nodes[-1].properties)["color"])
        # faces to ngons
        # TODO: detect & use Hammer++'s precision vertices
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
            # TODO: use globals to set this radius to 2x the maximum extents of the map
            radius = 10 ** 4
            ngon = [center + ((-local_x + local_y) * radius),
                    center + ((local_x + local_y) * radius),
                    center + ((local_x + -local_y) * radius),
                    center + ((-local_x + -local_y) * radius)]
            for j, other_f in enumerate(brush.faces):
                if j == i:
                    continue  # skip yourself
                ngon, offcut = clip(ngon, other_f.plane).values()
            brush.faces[i].polygon = ngon
            if hasattr(f, "displacement") and len(ngon) != 4:
                raise RuntimeError("face id {f.id}'s displacement is invalid (face has {len(ngon)} sides)")
                # solid is probably invalid
        return brush

    def as_node(self) -> valvevmf.VmfNode:
        # TODO: update autovisgroup hidden state in editor node
        if not hasattr(self, "_source"):  # generate base
            editor_node = valvevmf.VmfNode("editor",
                                           properties=[("color", None)])
            self._source = valvevmf.VmfNode("solid",
                                            properties=[("id", self.id)],
                                            nodes=[editor_node])
        # trying to edit editor node without discarding anything
        editor_node = self._source.nodes[-1]
        assert editor_node.name == "editor"
        assert all([n.name == "side" for n in self._source.nodes[:-1]]), "unexpected solid node"
        # NOTE: ^ also passes if no sides are present, so the above lazy generator works
        assert len({k for k, v in editor_node.properties}) == len(editor_node.properties), "duplicate keys"
        editor_properties = dict(editor_node.properties)
        editor_properties["color"] = [(int(255 * x)) for x in self.colour]
        editor_node.properties = list(editor_properties.items())
        self._source.nodes = list()
        for face in self.faces:
            try:
                self._source.nodes.append(face.as_node())
            except Exception as exc:
                raise RuntimeError(f"Invalid Brush (solid id: {self.id}, side id: {face.id}); {exc}")
        self._source.nodes.append(editor_node)
        return self._source

    def is_displacement(self) -> bool:
        return any([hasattr(f, "displacement") for f in self.faces])

    # Operations
    # TODO: clip(self, plane): -> (Brush, Brush), new faces on plane use default["material"]

    def translate(self, offset: vector.vec3, texture_lock=False, displacement_lock=False):
        # apply offset (arrow keys nudge) to plane & polygon of each face
        # TODO: break the folowing into utility functions:
        # -- texture lock: recalculate each face's UV vectors / offsets
        # --- could be used for Alt+RMB texture wrapping?
        # -- displacement_lock: recalculate all displacement normals & distances (force apply subdiv?)
        raise NotImplementedError()


class Displacement:
    _source: valvevmf.VmfNode | None  # only present if loaded from / saved to file
    alphas: List[List[vector.vec3]] = list()
    distances: List[List[float]] = list()
    elevation: int = 0
    flags: int = 0
    normals: List[List[vector.vec3]] = list()
    power: int = 2
    start: vector.vec3
    subdivided: bool = False
    allowed_verts: List[int] = list()  # default: "10" "-1 -1 -1 -1 -1 -1 -1 -1 -1 -1" ?
    offset_normals: List[List[vector.vec3]] = list()
    offsets: List[List[vector.vec3]] = list()
    triangle_tags: List[List[int]] = list()  # walkable, buildable etc.

    @classmethod
    def from_node(cls: Displacement, dispinfo: valvevmf.VmfNode) -> Displacement:
        disp = cls()
        disp._source = dispinfo
        dispinfo_properties = dict(dispinfo.properties)
        disp.power = dispinfo_properties["power"]
        disp.start = vector.vec3(*dispinfo_properties["startposition"])
        disp.flags = dispinfo_properties["flags"]
        disp.elevation = dispinfo_properties["elevation"]
        disp.subdivided = dispinfo_properties["subdiv"]
        # Power 1 Displacement:
        # A -- AB - B
        # |\ 2 | 3 /|
        # | 1 \|/ 4 |
        # DA - X - BC
        # | 5 /|\ 8 |
        # |/ 6 | 7 \|
        # D -- CD - C
        row_count = (2 ** disp.power) + 1  # rows of vertices
        dispinfo_rows = {n.name: n.properties[0][1] for n in dispinfo.nodes}
        # ^ {"node.name": List[List[float]] | List[float]}
        # one float per vertex
        disp.alphas = dispinfo_rows["alphas"]
        disp.distances = dispinfo_rows["distances"]
        # one int per triangle (2 ^ disp.power * 2 tris per row over 2 ^ disp.power rows)
        disp.triangle_tags = dispinfo_rows["triangle_tags"]  # walkable, buildable, collsions etc.?
        # collect vectors (3 floats per row)
        for i in range(row_count):
            disp.normals.append(list())
            disp.offsets.append(list())
            disp.offset_normals.append(list())
            for j in range(0, row_count * 3, 3):
                _slice = slice(j, j + 3)
                disp.normals[-1].append(vector.vec3(*dispinfo_rows["normals"][i][_slice]))
                disp.offsets[-1].append(vector.vec3(*dispinfo_rows["offsets"][i][_slice]))
                disp.offset_normals[-1].append(vector.vec3(*dispinfo_rows["offset_normals"][i][_slice]))
        return disp

    def as_node(self) -> valvevmf.VmfNode:
        properties = {"power": self.power,
                      "startposition": tuple(self.start),
                      "flags": self.flags,
                      "elevation": self.elevation,
                      "subdiv": 1 if self.subdivided else 0}
        nodes = {a: dict() for a in ("alphas", "distances", "normals", "offset_normals", "offsets", "triangle_tags")}
        nodes = {"alphas": self.alphas,
                 "distances": self.distances,
                 "triangle_tags": self.triangle_tags}
        nodes["normals"] = [list(itertools.chain(*map(tuple, row))) for row in self.normals]
        nodes["offsets"] = [list(itertools.chain(*map(tuple, row))) for row in self.offsets]
        nodes["offset_normals"] = [list(itertools.chain(*map(tuple, row))) for row in self.offset_normals]
        dispinfo = valvevmf.VmfNode("dispinfo",
                                    properties=list(properties.items()),
                                    nodes=[valvevmf.Vmf(k, properties=("rows", v)) for k, v in nodes])
        dispinfo.nodes.append(valvevmf.VmfNode("allowed_verts",
                                               properties=[("10", self.allowed_verts)]))
        return dispinfo

    # Operations
    def change_power(self, new_power):
        """simplify / subdivide"""
        raise NotImplementedError()
        # either lerp the points on existing edges or average local points together

    def sew(self, other: Face):
        """Sew edge to meet other face"""
        # TODO: if other is a disp, meet halfway
        # TODO: if other is not a disp, snap to a valid edge
        # TODO: if invalid, do nothing
        raise NotImplementedError()


Plane = (vector.vec3, float)
# ^ (normal, distance)


class Face:
    # NOTE: Brushes will frequently mutate Faces (mappers know what I mean)
    _source: valvevmf.VmfNode | None  # only present if loaded from / saved to file
    displacement: Displacement | None
    id: int
    lightmap_scale: int
    material: str = default["material"]
    plane: List[Plane]
    polygon: List[vector.vec3] = list()
    # NOTE: face vertices are dependant on the intersection of faces in the parent brush
    # -- however, a face can exist independantly of a brush, for convenience
    rotation: float
    smoothing_groups: int
    uaxis: TextureVector
    vaxis: TextureVector

    @classmethod
    def from_polygon(cls: Face, polygon: List[vector.vec3], material: str = default["material"]) -> Face:
        face = cls()
        if len(polygon) < 3:
            raise RuntimeError(f"Cannot generate a {cls.__name__} from {len(polygon)} sided polygon!")
        face.polygon = polygon
        A, B, C = polygon[:3]
        face.plane = plane_of(A, B, C)
        # calculate "face" texture projection
        face.uaxis = TextureVector(*(A - B), 0, 0.25)
        face.vaxis = TextureVector(*(A - polygon[-1]), 0, 0.25)
        # NOTE: vaxis is not guaranteed to be perpendicular to uaxis, textures may skew
        global _id
        face.id = _id
        _id += 1
        face.material = material
        face.rotation = 0.0
        face.lightmap_scale = default["lightmap_scale"]
        face.smoothing_groups = 0
        return face

    @classmethod
    def from_node(cls: Face, side: valvevmf.VmfNode) -> Face:
        f"""whoever calls this function must calculate the polygon of this {cls.__name__}"""
        # NOTE: face.polygon can be calculated by clipping against the other planes in a parent brush
        # -- Brush.from_node(...) does this automatically after calling this method on each side_node
        face = cls()
        face._source = side
        side_properties = dict(side.properties)
        face.id = side_properties["id"]
        face.plane = plane_of(*[vector.vec3(*P) for P in side_properties["plane"]])
        # ^ (vec3 normal, float distance)
        face.material = side_properties["material"]
        face.uaxis = TextureVector(*side_properties["uaxis"])
        face.vaxis = TextureVector(*side_properties["vaxis"])
        face.rotation = float(side_properties["rotation"])
        face.lightmap_scale = side_properties["lightmapscale"]
        face.smoothing_groups = side_properties["smoothing_groups"]
        if hasattr(side_properties, "dispinfo"):
            face.displacement = Displacement.from_node(side_properties["dispinfo"])
        return face

    def as_node(self) -> valvevmf.VmfNode:
        if hasattr(self, "_source"):
            side_properties = dict(self._source.properties)
        else:
            side_properties = dict()
        if len(self.polygon) < 3:
            raise RuntimeError(f"Invalid Face (side id: {self.id})")
        side_properties.update({"id": self.id,
                                "plane": [tuple(P) for P in self.polygon[:3]],
                                # NOTE: plane will drift over time due to floating point precision loss
                                # -- forcing the 3 points to be "on grid" (integers only) could mitigate this
                                "material": self.material,
                                "uaxis": (*self.uaxis.vector, self.uaxis.offset, self.uaxis.scale),
                                "vaxis": (*self.vaxis.vector, self.vaxis.offset, self.vaxis.scale),
                                "rotation": self.rotation,
                                "lightmapscale": self.lightmap_scale,
                                "smoothing_groups": self.smoothing_groups})
        self._source = valvevmf.VmfNode("side",
                                        properties=[*side_properties.items()])
        if hasattr(self, "displacement"):
            self._source.nodes.insert(0, self.displacement.as_node())
        return self._source

    # TODO: lightmap uv
    def uv_at(self, position: vector.vec3) -> vector.vec2:
        """TextureVecs -> UVs"""
        u = self.uaxis.linear_pos(position)
        v = self.vaxis.linear_pos(position)
        return vector.vec2(u, v)


class TextureVector:
    vector: vector.vec3
    offset: float
    scale: float

    def __init__(self, x=0, y=0, z=0, offset=0, scale=default["texture_scale"]):
        self.vector = vector.vec3(x, y, z)
        self.offset = offset
        self.scale = scale

    # u or v at world space position
    def linear_pos(self, position: vector.vec3) -> float:
        """half a uv, need 2 TextureVectors for the full uv"""
        return (vector.dot(position, self.vector) + self.offset) / self.scale

    # TODO: reproject against face (world / face projection)
    # TODO: reproject from selection (alt+rmb texture wrapping)


def clip(poly: List[vector.vec3], plane: Plane) -> Dict[str, List[vector.vec3]]:
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


def plane_of(A: vector.vec3, B: vector.vec3, C: vector.vec3) -> (vector.vec3, float):
    """returns the plane (vec3 normal, float distance) the triangle ABC represents"""
    normal = ((A - B) * (C - B)).normalise()
    return (normal, vector.dot(normal, A))

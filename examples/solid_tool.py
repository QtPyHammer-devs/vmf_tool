import itertools
import vector
import sys
sys.path.insert(0, '../')
import vmf_tool
sys.path.insert(0, 'render/')
import physics

def triangle_of(side):
    "extract triangle from string (returns 3 vec3)"
    triangle = [[float(i) for i in xyz.split()] for xyz in side.plane[1:-1].split(') (')]
    return tuple(map(vector.vec3, triangle))

def plane_of(A, B, C):
    """returns plane the triangle defined by A, B & C lies on"""
    normal = ((A - B) * (C - B)).normalise()
    return (normal, vector.dot(normal, A))

def loop_fan(vertices):
    "ploygon to triangle fan"
    out = vertices[:3]
    for vertex in vertices[3:]:
        out += [out[0], out[-1], vertex]
    return out

def loop_fan_indices(vertices):
    "polygon to triangle fan (indices only) by Exactol"
    indices = []
    for i in range(1, len(vertices) - 1):
        indices += [0, i, i + 1]
    return indices


class solid:
    def __init__(self, string_solid):
        """Initialise from string, nested dict or namespace"""
        if isinstance(string_solid, vmf_tool.namespace):
            pass
        elif isinstance(string_solid, dict):
            source = vmf_tool.namespace(string_solid)
        elif isinstance(string_solid, str):
            source = vmf_tool.namespace_from(string_solid)
        else:
            raise RuntimeError(f'Tried to create solid from invalid type: {type(string_solid)}')
        self.string_solid = string_solid # preserve for debug & export
        self.colour = tuple(int(x) / 255 for x in string_solid.editor.color.split())
        self.string_triangles = [triangle_of(s) for s in string_solid.sides]
        self.string_vertices = list(itertools.chain(*self.string_triangles))
        # does not contain every point, some will be missing
        # goldrush contains an example (start of stage 2, arch behind cart)
        self.planes = [plane_of(*t) for t in self.string_triangles] # ((Normal XYZ), Dist)

        # faces namespace
        # face([plane, texture_data([material, uvs, lightmap_scale]), vertices])
        self.faces = []
        for i, tri in enumerate(self.string_triangles):
            plane = self.planes[i]
            face = list(tri)
            for vertex in self.string_vertices:
                if vertex not in face:
                    if plane[1] - 1 < vector.dot(vertex, plane[0]) < plane[1] + 1:
                        face.append(vertex)
            face = vector.sort_clockwise(face, plane[0])
            self.faces.append(face)

        # displacements next
        # loop fan OR disp pattern
        self.triangles = tuple(itertools.chain(*[loop_fan(f) for f in self.faces]))

        self.indices = []
        self.vertices = [] # [((position), (normal), (uv)), ...]
        # put all formatted vertices in list
        # record indices for each face loop
        # convert face loops to triangle fans
        # store (start, len) for each face [index buffer range mapping]
        # store full index strip
        self.index_map = []
        start_index = 0
        for face, side, plane in zip(self.faces, string_solid.sides, self.planes):
            face_indices = []
            normal = plane[0]
            for i, vertex in enumerate(face):
                u_axis = side.uaxis.rpartition(' ')[0::2]
                u_vector = [float(x) for x in u_axis[0][1:-1].split()]
                u_scale = float(u_axis[1])
                v_axis = side.vaxis.rpartition(' ')[0::2]
                v_vector = [float(x) for x in v_axis[0][1:-1].split()]
                v_scale = float(v_axis[1])
                uv = [vector.dot(vertex, u_vector[:3]) + u_vector[-1],
                      vector.dot(vertex, v_vector[:3]) + v_vector[-1]]
                uv[0] /= u_scale
                uv[1] /= v_scale

                assembled_vertex = tuple(itertools.chain(*zip(vertex, normal, uv, self.colour)))
                if assembled_vertex not in self.string_vertices:
                    self.vertices.append(assembled_vertex)
                    face_indices.append(len(self.vertices) - 1)
                else:
                    face_indices.append(self.vertices.index(assembled_vertex))
            face_indices = loop_fan_indices(face_indices)
            self.index_map.append((start_index, len(face_indices)))
            start_index += len(face_indices)
            self.indices += face_indices
        
        all_x = [v[0] for v in self.string_vertices]
        all_y = [v[1] for v in self.string_vertices]
        all_z = [v[2] for v in self.string_vertices]
        min_x, max_x = min(all_x), max(all_x)
        min_y, max_y = min(all_y), max(all_y)
        min_z, max_z = min(all_z), max(all_z)
        self.aabb = physics.aabb([min_x, min_y, min_z], [max_x, max_y, max_z])
        self.center = (self.aabb.min + self.aabb.max) / 2

        # DISPLACEMENTS (IF PRESENT)
        # {side_index: displacement}
        # SEE HAMMER DISP DRAW MODES
        # DRAW BRUSH FACES
        # DISP ONLY
        # DISP FACES AS DISP + SOLID FACES AS SOLID
        # DRAW WALKABLE (calculate tri normals)
        self.displacements = {}
        for i, side in enumerate(string_solid):
            if hasattr(solid, 'dispinfo'):
                self.displacements[i] = solid.dispinfo

        self.disp_tris = {} # {side_index: [vertex, ...], ...}        

    def flip(self, center, axis):
        """axis is a vector"""
        # flip along axis
        # maintain outward facing plane normals
        # invert all plane normals along axis, flip along axis
        ...

    def recalculate(self):
        """update self.string_solid to match vertices"""
        # foreach face
        #   solid.sides.append(vmf_tool.namespace(...))
        #   solid.sides.[-1].plane = '({:.f}) ({:.f}) ({:.f})'.format(*face[:3])
        ...

    def rotate(self, pivot_point=None):
        # if pivot_point == None:
        #     pivot_point = self.center
        # foreach plane
        #     rotate normal
        #     recalculate distance
        # foreach vertex
        #     translate -(self.center - origin)
        #     rotate
        #     translate back
        ...

    def translate(self, offset):
        """offset is a vector"""
        # for plane in self.planes
        #     plane.distance += dot(plane.normal, offset)
        # for vertex in self.vertices
        #     vertex += offset
        ...

    def make_valid(self):
        """take all faces and ensure their verts lie on shared planes"""
        # ideally split if not convex
        # can be very expensive to correct
        # recalculate planes from tris if possible
        # if any verts not on correct planes, throw warning
        # check if solid has holes / is inverted
        ...

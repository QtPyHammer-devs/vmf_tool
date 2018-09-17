#TODO: !!! render each plane of a solid within it's bounding box !!!
#TODO: custom format with .vmf export
#TODO: auto-saves & auto-version numbering (Alpha, Beta, sub-version & RC buttons)
#TODO: compilepal button
#TODO: preview cubemaps (load from .bsp copy in /maps)
#TODO: export to obj (one object per solid)
#TODO: obj import (each object is a solid)
#TODO: multiple 2D viewports
#------- totally customisable:
#------- position, size, ortho/perspective etc. (like blender)
#TODO: less hassle overlay copy & paste
#TODO: materials
#TODO: LIVE skybox & sun preview
#TODO: lighting preview
#TODO: displacement face copying (fusing brushes)
#TODO: render effects preview
#TODO: forest fill (prop family, density, falloff side, sort by tricount)
#TODO: blend modulate preview
#TODO: transparency & alpha sorting
#TODO: render modes (wireframe, flat, textured etc)
#TODO: settings that can be changed without restarting & SETTINGS FILES
#TODO: vpk browser
#TODO: script I/O (MvM Previews, including BOSS & TANK sizes)
#TODO: .nav viewer & editor, auto-generated I/O tracking
#TODO: output to addoutput and vice-versa (show AddOutputs in entity Outputs)
#TODO: brush group to .smd/.dmx (live model editing with Save-as)
#------- fast .vmt translation & .qc generation
#------- compile .mdl on next map compile
#TODO: motion previews (animation tools for brush objects)
#TODO: rulers (jump curves, rocket tracks)
#TODO: material proxy previews (animated .vmts)
#TODO: Twister-esque quick displacements / arches
#------- quick sattelite dish
#------- quick spiral staircase
#TODO: stairs with slope & step fields, like a blender modifier
#TODO: mirror team (flip or rotate)
#TODO: sightline spotter
#------- point out the longest and narrowest sightlines to a given point
#------- hardest to spot (lighting or size) should be prioritised
#TODO: quick gamemode (Ctrl+N Menu)
#TODO: better I/O autocomplete, copy & addoutput tools
#------- typed activator (check flags etc. to know what will/may trigger)
#TODO: displacement rounding with preserve edges optional
#TODO: lightmode (blender-like colour scheming with presets)
#TODO: displacement sculpt curve tools
#------- guide frames for displacements (NURBS OR point cloud)
import camera
import colorsys
import ctypes
import enum
import itertools
from OpenGL.GL import * #Installed via pip (PyOpenGl 3.1.0)
from OpenGL.GLU import * #PyOpenGL-accelerate 3.1.0 requires specific MSVC builds for Cython
#get precompiled binaries if you can, it's much less work
#for vertex buffers Numpy is needed (also available through pip)
import physics
from sdl2 import * #Installed via pip (PySDL2 0.9.5)
#requires SDL2.dll (steam has a copy in it's main directory)
#and an Environment Variable (PYSDL2_DLL_PATH) holding it's location
import time

import sys
sys.path.insert(0, '../')
import vector
sys.path.insert(0, '../../')
import vmf_tool


def planes_intersect_at(p0, p1, p2):
    p0 = p0[0] * p0[1]
    p1 = p1[0] * p1[1]
    p2 = p2[0] * p2[1]
    X = p0.x + p1.x + p2.x
    Y = p0.y + p1.y + p2.y
    Z = p0.z + p1.z + p2.z
    return vector.vec3(X, Y, Z)

class pivot(enum.Enum): # for selections of more than one brush / entity
    """like blender pivot point"""
    median = 0
    active = 1
    cursor = 2
    individual = 3

def draw_aabb(aabb):
    """"Precede with "glBegin(GL_QUADS)"\nExpects glPolygonMode to be GL_LINE"""
    glVertex(aabb.min.x, aabb.max.y, aabb.max.z)
    glVertex(aabb.max.x, aabb.max.y, aabb.max.z)
    glVertex(aabb.max.x, aabb.min.y, aabb.max.z)
    glVertex(aabb.min.x, aabb.min.y, aabb.max.z)

    glVertex(aabb.min.x, aabb.max.y, aabb.max.z)
    glVertex(aabb.max.x, aabb.max.y, aabb.max.z)
    glVertex(aabb.max.x, aabb.max.y, aabb.min.z)
    glVertex(aabb.min.x, aabb.max.y, aabb.min.z)

    glVertex(aabb.min.x, aabb.min.y, aabb.max.z)
    glVertex(aabb.max.x, aabb.min.y, aabb.max.z)
    glVertex(aabb.max.x, aabb.min.y, aabb.min.z)
    glVertex(aabb.min.x, aabb.min.y, aabb.min.z)

    glVertex(aabb.min.x, aabb.max.y, aabb.min.z)
    glVertex(aabb.max.x, aabb.max.y, aabb.min.z)
    glVertex(aabb.max.x, aabb.min.y, aabb.min.z)
    glVertex(aabb.min.x, aabb.min.y, aabb.min.z)

class solid:
    # __slots__ = ['string_solid', 'colour', 'planes', 'vertices', 'faces']

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
        self.colour = tuple(int(x) / 255 for x in string_solid.editor.color.split())
        self.string_triangles = [triangle_of(s) for s in string_solid.sides]
        self.string_vertices = list(itertools.chain(*self.string_triangles))
        self.planes = [plane_of(*t) for t in self.string_triangles]
        intersects = {}
        unchecked_planes = {i: plane for i, plane in enumerate(self.planes)}
        for i, a_plane in enumerate(self.planes):
            intersects[i] = []
            unchecked_planes.pop(i)
            for j, b_plane in unchecked_planes.items():
                if vector.dot(a_plane[0], b_plane[0]) >= 0:
                    intersects[i].append(j)
            for key in intersects.keys():
                if i in intersects[key]:
                    intersects[i].append(key)

        intersections = []
        others = dict(intersects)
        for i in intersects.keys():
            others.pop(i)
            other_others = dict(others)
            for j in others.keys():
                if j in intersects[i]:
                    other_others.pop(j)
                    for k in other_others:
                        if k in intersects[i] and k in intersects[j]:
                            intersections.append([i, j, k])

        self.faces = {i: [] for i, p in enumerate(self.planes)} # sort CLOCKWISE
        self.vertices = []
        for i, ps in enumerate(intersections):
            for plane_index in ps:
                self.faces[plane_index].append(i)
            self.vertices.append(planes_intersect_at(*[self.planes[p] for p in ps]))

        all_x = [v.x for v in self.vertices]
        all_y = [v.y for v in self.vertices]
        all_z = [v.z for v in self.vertices]
        min_x, max_x = min(all_x), max(all_x)
        min_y, max_y = min(all_y), max(all_y)
        min_z, max_z = min(all_z), max(all_z)
        self.aabb = physics.aabb([min_x, min_y, min_z], [max_x, max_y, max_z])

        all_x = [v[0] for v in self.string_vertices]
        all_y = [v[1] for v in self.string_vertices]
        all_z = [v[2] for v in self.string_vertices]
        min_x, max_x = min(all_x), max(all_x)
        min_y, max_y = min(all_y), max(all_y)
        min_z, max_z = min(all_z), max(all_z)
        self.string_aabb = physics.aabb([min_x, min_y, min_z], [max_x, max_y, max_z])

    def draw(self):
        glColor(1, 1, 1)
        glBegin(GL_POINTS)
        for vertex in self.string_vertices:
            glVertex(*vertex)
        glEnd()

        glPolygonMode(GL_FRONT, GL_LINE)
        glBegin(GL_QUADS)
        draw_aabb(self.string_aabb)
        glEnd()
        glPolygonMode(GL_FRONT, GL_FILL)

        glColor(*self.colour)
        glBegin(GL_TRIANGLES)
        for triangle in self.string_triangles:
            for vertex in triangle:
                glVertex(*vertex)
        glEnd()
        

    def export(self):
        """returns a dict resembling an imported solid"""
        # foreach face
        #   solid.sides.append(vmf_tool.namespace(...))
        #   solid.sides.[-1].plane = '({:.f}) ({:.f}) ({:.f})'.format(*face[:3])
        ...

    def flip(self, center, axis):
        """axis is a vector"""
        # flip along axis
        # maintain outward facing plane normals
        # invert all plane normals along axis, flip along axis
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

def triangle_of(side):
    triangle = [[float(i) for i in xyz.split()] for xyz in side.plane[1:-1].split(') (')]
    return tuple(map(vector.vec3, triangle))

def plane_of(A, B, C):
    """returns plane the triangle defined by A, B & C lies on"""
    normal = ((A - B) * (C - B)).normalise()
    return (normal, vector.dot(normal, A))

def loop_fan(vertices):
    out = vertices[:3]
    for vertex in vertices[3:]:
        out += [out[0], out[-1], vertex]
    return out

def loop_fan_indices(vertices, start_index):
    "polygon to triangle fan (indices only) by Exactol"
    indices = []
    for i in range(1, len(vertices) - 1):
        indices += [startIndex, startIndex + i, startIndex + i + 1]
    return indices

def main(vmf_path, width=1024, height=576):
    SDL_Init(SDL_INIT_VIDEO)
    window = SDL_CreateWindow(b'SDL2 OpenGL', SDL_WINDOWPOS_CENTERED,  SDL_WINDOWPOS_CENTERED, width, height, SDL_WINDOW_OPENGL | SDL_WINDOW_BORDERLESS)
    glContext = SDL_GL_CreateContext(window)
    SDL_GL_SetSwapInterval(0)
    glClearColor(0.1, 0.1, 0.1, 0.0)
    glColor(1, 1, 1)
    gluPerspective(90, width / height, 0.1, 4096 * 4)
    glPolygonMode(GL_BACK, GL_LINE)
    glFrontFace(GL_CW)
    glPointSize(4)

    start_import = time.time()
    imported_vmf = vmf_tool.namespace_from(open(vmf_path))

    global solid
    s40 = solid(imported_vmf.world.solids[40])
    print('import took {:.2f} seconds'.format(time.time() - start_import))

    CAMERA = camera.freecam(None, None, 128)
    rendered_ray = []

    SDL_SetRelativeMouseMode(SDL_TRUE)
    SDL_CaptureMouse(SDL_TRUE)

    mousepos = vector.vec2()
    keys = []

    tickrate = 1 / 0.015
    old_time = time.time()
    event = SDL_Event()
    while True:
        while SDL_PollEvent(ctypes.byref(event)) != 0:
            if event.type == SDL_QUIT or event.key.keysym.sym == SDLK_ESCAPE and event.type == SDL_KEYDOWN:
                SDL_GL_DeleteContext(glContext)
                SDL_DestroyWindow(window)
                SDL_Quit()
                return False
            if event.type == SDL_KEYDOWN:
                if event.key.keysym.sym not in keys:
                    keys.append(event.key.keysym.sym)
            if event.type == SDL_KEYUP:
                while event.key.keysym.sym in keys:
                    keys.remove(event.key.keysym.sym)
            if event.type == SDL_MOUSEBUTTONDOWN:
                keys.append(event.button.button)
            if event.type == SDL_MOUSEBUTTONUP:
                while event.button.button in keys:
                    keys.remove(event.button.button)
            if event.type == SDL_MOUSEMOTION:
                mousepos += vector.vec2(event.motion.xrel, event.motion.yrel)
                SDL_WarpMouseInWindow(window, width // 2, height // 2)
            if event.type == SDL_MOUSEWHEEL:
                CAMERA.speed += event.wheel.y * 32

        dt = time.time() - old_time
        while dt >= 1 / tickrate:
            CAMERA.update(mousepos, keys, 1 / tickrate)
            if SDLK_r in keys:
                CAMERA = camera.freecam(None, None, 128)
            if SDL_BUTTON_LEFT in keys:
                ray_start = CAMERA.position
                ray_dir = vector.vec3(0, 1, 0).rotate(*-CAMERA.rotation)
                rendered_ray = [ray_start, ray_start + (ray_dir * 4096)]
                #calculate collisions
            dt -= 1 / tickrate
            old_time = time.time()

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glPushMatrix()
        CAMERA.set()

        # CENTER MARKER
        glLineWidth(1)
        glBegin(GL_LINES)
        glColor(1, 0, 0)
        glVertex(0, 0, 0)
        glVertex(128, 0, 0)
        glColor(0, 1, 0)
        glVertex(0, 0, 0)
        glVertex(0, 128, 0)
        glColor(0, 0, 1)
        glVertex(0, 0, 0)
        glVertex(0, 0, 128)
        glEnd()

        # RAYCAST
        glColor(1, .25, 0)
        glBegin(GL_LINES)
        for point in rendered_ray:
            glVertex(*point)
        glEnd()

        # GRID
        glLineWidth(2)
        glBegin(GL_LINES)
        for x in range(-16, 17):
            x = x * 64
            glColor(1, 0 , 0)
            glVertex(x, -1024, 0)
            glColor(.25, .25, .25)
            glVertex(x, 0, 0)
            glVertex(x, 0, 0)
            glColor(1, 0 , 0)
            glVertex(x, 1024, 0)
        for y in range(-16, 17):
            y = y * 64
            glColor(0, 1 , 0)
            glVertex(-1024, y, 0)
            glColor(.25, .25, .25)
            glVertex(0, y, 0)
            glVertex(0, y, 0)
            glColor(0, 1 , 0)
            glVertex(1024, y, 0)
        glEnd()

        # SOLID OBJECT
        s40.draw()

        glPopMatrix()
        SDL_GL_SwapWindow(window)

if __name__ == '__main__':
    try:
        main('../../mapsrc/test2.vmf')
    except Exception as exc:
        SDL_Quit()
        raise exc
##    import sys
##    for file in sys.argv[1:]:
##        main(file)

#TODO: export to obj (one object per solid)
#TODO: obj import (each object is a solid)
#TODO: render each plane of a solid as it intersects that solids bounding box
# make that bounding box from verts supplied by the vmf
<<<<<<< HEAD:examples/render_vmf.py
import sys
sys.path.insert(0, '../')
=======
# 2D VIEWPORTS

>>>>>>> f885727d86ac30fb28a8e4b004b8360efe1fce29:render_vmf.py
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
#requires SDL2.dll (steam has one in it's main directory) & an Environment Variable holding it's location
import time
import vector
import vmf_tool

class pivot(enum.Enum):
    """like blender pivot point"""
    median = 0
    active = 1
    cursor = 2
    individual = 3

class solid:
    def __init__(self, source):
        """expects a dictionary, strings are also acceptable"""
        if isinstance(source, string):
            source = vmf_tool.vmf(source).dict
        if isinstance(source, dict):
            #use/store as many key-values as posible
            self.dict = source #retained for accuracy / debug
<<<<<<< HEAD:examples/render_vmf.py
            self.colour = tuple(map(lambda x: int(x) / 255, source['editor']['color'].split()))
            self.planes = []
            self.vertices = []
            ### wait how does this work again? ###
            # for side in source['sides']:
            #     self.planes.append(extract_str_plane(side['plane']))
            # planes = itertools.chain([s['plane'] for s in source['sides']])
            # planes = [*map(extract_str_plane, planes)]
            intersects = {}
            #stores planes & their indices
            unchecked_planes = {i: plane for i, plane in enumerate(planes)}
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

            face_points = {i: [] for i, p in enumerate(self.planes)}
            for i, j, k in intersections:
                p0 = planes[i]
                p1 = planes[j]
                p2 = planes[k]
                p0 = p0[0] * p0[1]
                p1 = p1[0] * p1[1]
                p2 = p2[0] * p2[1]
                X = p0.x + p1.x + p2.x
                Y = p0.y + p1.y + p2.y
                Z = p0.z + p1.z + p2.z
                V = vector.vec3(X, Y, Z)
                #check if each one is above another plane in the solid
                face_points[i].append(V)
                face_points[j].append(V)
                face_points[k].append(V)

            for plane_index, points in face_points.items():
                loop = vector.CW_sort(points, planes[plane_index][0])
                face_points[key] = loop
                fan = loop_to_fan(loop)
                all_tris += fan
                all_solid_polys[-1].append(fan)

            #utilise verts from source (good for debug)
            all_x = [v.x for v in self.vertices]
            all_y = [v.y for v in self.vertices]
            all_z = [v.z for v in self.vertices]
            min_x, max_x = min(all_x), max(all_x)
            min_y, max_y = min(all_y), max(all_y)
            min_z, max_z = min(all_z), max(all_z)
            self.aabb = physics.aabb([min_x, min_y, min_z], [max_x, max_y, max_z])
            self.center = sum(self.vertices, vector.vec3) / len(self.vertices)
            self.faces = {plane: [edgeloop]} #indexed clockwise edge loops
=======
>>>>>>> f885727d86ac30fb28a8e4b004b8360efe1fce29:render_vmf.py
        else:
            raise RuntimeError(f'Tried to create solid from invalid type: {type(source)}')
        self.colour = tuple(map(lambda x: int(x) / 255, source['editor']['color'].split()))
        self.planes = []
        self.vertices = []
        ### wait how does this work again? ###
        # for side in source['sides']:
        #     self.planes.append(extract_str_plane(side['plane']))
        # planes = itertools.chain([s['plane'] for s in source['sides']])
        # planes = [*map(extract_str_plane, planes)]
        intersects = {}
        #stores planes & their indices
        unchecked_planes = {i: plane for i, plane in enumerate(planes)}
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

        face_points = {i: [] for i, p in enumerate(self.planes)}
        for i, j, k in intersections:
            p0 = planes[i]
            p1 = planes[j]
            p2 = planes[k]
            p0 = p0[0] * p0[1]
            p1 = p1[0] * p1[1]
            p2 = p2[0] * p2[1]
            X = p0.x + p1.x + p2.x
            Y = p0.y + p1.y + p2.y
            Z = p0.z + p1.z + p2.z
            V = vector.vec3(X, Y, Z)
            #check if each one is above another plane in the solid
            face_points[i].append(V)
            face_points[j].append(V)
            face_points[k].append(V)

        for plane_index, points in face_points.items():
            loop = vector.CW_sort(points, planes[plane_index][0])
            face_points[key] = loop
            fan = loop_to_fan(loop)
            all_tris += fan
            all_solid_polys[-1].append(fan)

        source_verts = []
        for side in source['sides']:
            tri = side['plane'][1:-1].split(') (')
            tri = [float(v.split()) for v in tri]
            source_verts.append(tri)
        all_x = [v[0] for v in source_verts]
        all_y = [v[1] for v in source_verts]
        all_z = [v[2] for v in source_verts]
        min_x, max_x = min(all_x), max(all_x)
        min_y, max_y = min(all_y), max(all_y)
        min_z, max_z = min(all_z), max(all_z)
        self.source_aabb = physics.aabb([min_x, min_y, min_z], [max_x, max_y, max_z])

        all_x = [v.x for v in self.vertices]
        all_y = [v.y for v in self.vertices]
        all_z = [v.z for v in self.vertices]
        min_x, max_x = min(all_x), max(all_x)
        min_y, max_y = min(all_y), max(all_y)
        min_z, max_z = min(all_z), max(all_z)
        self.aabb = physics.aabb([min_x, min_y, min_z], [max_x, max_y, max_z])
        self.center = sum(self.vertices, vector.vec3) / len(self.vertices)
        self.faces = {plane: [edgeloop]} #indexed clockwise edge loops

    def make_valid(self):
        """take all faces and ensure their verts lie on shared planes"""
        #ideally split if not convex
        #can be very expensive to correct
        #just recalc planes
        #if any verts not on correct planes, throw warning
        #check if solid is open
        ...

    def export(self):
        """returns a dict resembling an imported solid"""
        #foreach face
        #  solid['sides'].append({})
        #  solid['sides'][-1]['plane'] = '({v1}) ({v2}) ({v3})'
        ...

    def rotate(self, pivot_point=pivot.median):
        #foreach plane
        #  rotate normal
        #  recalculate distance
        #foreach vertex
        #  translate -(self.center - origin)
        #  rotate
        #  translate back
        ...

    def flip(self, center, axis):
        """axis is a vector"""
        #flip along axis
        #maintain outward facing plane normals
        #invert all plane normals along axis, flip along axis
        ...

    def translate(self, offset):
        """offset is a vector"""
        #for plane in self.planes
        #    plane.distance += dot(plane.normal, offset)
        #for vertex in self.vertices
        #    vertex += offset
        ...

def extract_str_plane(string):
    points = string[1:-1].split(') (')
    points = [x.split() for x in points]
    points = [[*map(float, x)] for x in points]
    A, B, C = map(vector.vec3, points)
    normal = ((A - B) * (C - B)).normalise()
    return (normal, vector.dot(normal, A))

def loop_to_fan(verts):
    out = verts[:3]
    verts = verts[3:]
    for vert in verts:
        out += [out[0], out[-1], vert]
    return out

def main(width, height):
    SDL_Init(SDL_INIT_VIDEO)
    window = SDL_CreateWindow(b'SDL2 OpenGL', SDL_WINDOWPOS_CENTERED,  SDL_WINDOWPOS_CENTERED, width, height, SDL_WINDOW_OPENGL | SDL_WINDOW_BORDERLESS)
    glContext = SDL_GL_CreateContext(window)
    SDL_GL_SetSwapInterval(0)
    glClearColor(0.1, 0.1, 0.1, 0.0)
    glColor(1, 1, 1)
    gluPerspective(90, width / height, 0.1, 4096 * 4)
##    glPolygonMode(GL_FRONT, GL_LINE)
##    glPolygonMode(GL_BACK, GL_POINT)
    glPolygonMode(GL_BACK, GL_LINE)
    glFrontFace(GL_CW)
    glPointSize(4)

    start_import = time.time()
    v = vmf_tool.vmf(open('test2.vmf'))
    # SOLIDS TO CONVEX TRIS
    all_solids = v.dict['world']['solids'] #multiple brushes
    all_solids = [all_solids[40]] #single out single brushed
    #MAP > SHOW SELECTED BRUSH NUMBER in hammer is very useful for this
    #dict.get(key) means you don't need a try for keys that a dict may not have
##    all_solids = [v.dict['world']['solid']] #single brush
    #create compares, each key hold the indices of it's intersecting planes
    all_tris = []
    all_solid_polys = []
    for solid in all_solids:
        colour = tuple(map(lambda x: int(x) / 255, solid['editor']['color'].split()))
        all_solid_polys.append([colour])
        planes = itertools.chain([s['plane'] for s in solid['sides']])
        planes = [*map(extract_str_plane, planes)]
        intersects = {}
        unchecked_planes = {i: plane for i, plane in enumerate(planes)}
        for i, a_plane in enumerate(planes):
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

        face_points = {i: [] for i, p in enumerate(planes)}
        for i, j, k in intersections:
            p0 = planes[i]
            p1 = planes[j]
            p2 = planes[k]
            p0 = p0[0] * p0[1]
            p1 = p1[0] * p1[1]
            p2 = p2[0] * p2[1]
            X = p0.x + p1.x + p2.x
            Y = p0.y + p1.y + p2.y
            Z = p0.z + p1.z + p2.z
            V = vector.vec3(X, Y, Z)
            # all_ok = True
            # print(f'*** {V:.2f} ***')
            # for plane in planes:
            #     V_dot, V_dot_max = vector.dot(V, plane[0]), plane[1]
            #     if V_dot_max < 0:
            #         V_dot, V_dot_max = -V_dot, -V_dot_max
            #     if V_dot > V_dot_max:
            #         all_ok = False
            #         print(f'{V_dot:.2f} > {V_dot_max:.2f} on axis {plane[0]:.3f}')
            # if all_ok:
            face_points[i].append(V)
            face_points[j].append(V)
            face_points[k].append(V)

        for plane_index, points in face_points.items():
            if points != []:
                loop = vector.CW_sort(points, planes[plane_index][0])
                face_points[key] = loop
                fan = loop_to_fan(loop)
                all_tris += fan
                all_solid_polys[-1].append(fan)

        #fans should be made via indices
        #each face's verts must unique if format holds more than position data
        #BUILD TO BE MUTABLE
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

        for solid in all_solid_polys:
            # glColor(*solid[0])
            for loop, p_index in zip(solid[1:], face_points.keys()):
                glColor(*[i / 2 + .5 for i in planes[p_index][0]])
                glBegin(GL_POLYGON)
                for vertex in loop:
                    glVertex(*vertex)
                glEnd()

        glColor(1, 1, 1)
        glBegin(GL_POINTS)
        for solid in all_solid_polys:
            for loop in solid[1:]:
                for vertex in loop:
                    glVertex(*vertex)
        glEnd()

        glDisable(GL_DEPTH_TEST)
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

        glColor(1, .25, 0)
        glBegin(GL_LINES)
        for point in rendered_ray:
            glVertex(*point)
        glEnd()

        glEnable(GL_DEPTH_TEST)
        glPopMatrix()
        SDL_GL_SwapWindow(window)

if __name__ == '__main__':
    import getopt
    import sys
    options = getopt.getopt(sys.argv[1:], 'w:h:')
    width = 1024
    height = 576
    for option in options:
        for key, value in option:
            if key == '-w':
                width = int(value)
            elif key == '-h':
                height = int(value)
    main(width, height)

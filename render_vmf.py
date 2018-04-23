#TODO: export to obj (one object per solid)
#TODO: obj import (each object is a solid)

﻿import camera
import ctypes
import enum
import itertools
from OpenGL.GL import * #Installed via pip (PyOpenGl 3.1.0)
from OpenGL.GLU import * #PyOpenGL-accelerate 3.1.0 requires specific MSVC builds for Cython
#get precompiled binaries if you can, it's much less work
#for vertex buffers Numpy is also needed (available through pip)
from sdl2 import * #Instaleld via pip (PySDL2 0.9.5)
#requires SDL2.dll (steam has one in it's main directory) & a specific Environment Variable Pointing to it's location
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
        if isinstance(source, string):
            source = vmf_tool.vmf(source).dict
        if isinstance(source, dict):
            #use as many keyvalues as posible
            self.dict = source #retained for accuracy / debug
            self.planes = []
            for side in source['sides']:
                ...
                self.planes.append(...)
            self.vertices = [...]
            self.center = sum(self.vertices, vector.vec3) / len(self.vertices)
            self.faces = {plane: [edgeloop]} #indexed clockwise edge loops
        else:
            raise RuntimeError('Bad Source')

    def check_convexity(self):
        """take all faces and ensure their verts lie on shared planes"""
        #ideally split if not convex
        #can be very expensive to correct
        #just recalc planes
        #if any verts not on correct planes, throw warning
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

    def flip(self, axis):
        """axis is a vector"""
        #flip along axis
        #maintain outward facing plane normals
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

    start_import = time.time()
    v = vmf_tool.vmf(open('test2.vmf'))
    # SOLIDS TO CONVEX TRIS
    ## CAN'T HANDLE SINGLE BRUSHES
    all_solids = v.dict['world']['solids'] #multiple brushes
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
        #stores planes & their indices
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

        #now find all mutual triples & their intersecting points
        #calculate each triple once
        # -- to check for duplicates: all([i in b for i in a])
        intersections = []
        #some plane's intersections are prevented by other intersections
        #do two full passes per solid
        #foreach plane
        #  if one of the intersecting plane intersects 2 others intersecting the initial plane
        #  and there are more than 2 interscting planes (not a triangle)
        #    remove this plane from intersections
        #IS THERE A MORE EFFICIENT SINGLE-PASS METHOD?
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
            face_points[i].append(V)
            face_points[j].append(V)
            face_points[k].append(V)

        for plane_index, points in face_points.items():
            loop = vector.CW_sort(points, planes[plane_index][0])
            #z axis are inverted?
            #everything is inverted?
            #CW_sort may need center to be plane aligned
            face_points[key] = loop
            fan = loop_to_fan(loop)
            all_tris += fan
            all_solid_polys[-1].append(fan)

        #these are added to a vertexbuffer
        #their indexes are associated with each face
        #these indexes are then sorted clockwise relative to each faces normal
        #these edgeloops are then assembled into triangle loops

        #this is something vbsp.exe does, it just also splits the faces afterwards
        #do t-juncts affect origfaces?

        #if uvs are included in the vertex specification
        #then indexing only prevents calcuating intersections more than once

##    all_sides = [x['sides'] for x in all_solids]
##    all_sides = list(itertools.chain(*all_sides))
##    all_sides = list(filter(lambda x: x['material'] is not 'TOOLS/TOOLSNODRAW', all_sides))
##    all_tris = [x['plane'] for x in all_sides]
##    all_tris = [x[1:-1].split(') (') for x in all_tris]
##    all_tris = [list(map(float, y.split())) for x in all_tris for y in x]
##    print(all_sides[0])
##    all_colours = [x['color'] for x in all_solids]
##    all_colours = [int(y) / 255 for x in all_colours for y in x]
    print('import took {:.2f} seconds'.format(time.time() - start_import))

    CAMERA = camera.freecam(None, None, 128)

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
            if event.type == SDL_MOUSEMOTION:
                mousepos += vector.vec2(event.motion.xrel, event.motion.yrel)
                SDL_WarpMouseInWindow(window, width // 2, height // 2)
            if event.type == SDL_MOUSEWHEEL:
                CAMERA.speed += event.wheel.y * 32

        dt = time.time() - old_time
        while dt >= 1 / tickrate:
            CAMERA.update(mousepos, keys, 1 / tickrate)
            dt -= 1 / tickrate
            old_time = time.time()

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glPushMatrix()
        CAMERA.set()
        glColor(1, 1, 1)
##        glBegin(GL_TRIANGLES)
##        for vertex in all_tris:
##            glVertex(*vertex)
##        glEnd()
        for solid in all_solid_polys:
            glColor(*solid[0])
            for loop in solid[1:]:
                glBegin(GL_POLYGON)
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
        glEnable(GL_DEPTH_TEST)
        glPopMatrix()
        SDL_GL_SwapWindow(window)

if __name__ == '__main__':
    import getopt
    import sys
    options = getopt.getopt(sys.argv[1:], 'w:h:')
    width = 1366
    height = 768
    for option in options:
        for key, value in option:
            if key == '-w':
                width = int(value)
            elif key == '-h':
                height = int(value)
    main(width, height)

import colorsys
import ctypes
import math
from OpenGL.GL import *
from OpenGL.GLU import *
import random
from sdl2 import *
import time
import vector

def clockwise_sort(points, N):
    points = [vector.vec3(*point, 0) for point in points]
    O = sum(points, vector.vec3()) / len(points) # 0, 0, 0
    centered_points = [(point - O).normalise() for point in points]
    north = centered_points[0].normalise()
    east = north.rotate(*(N * -90))
    north_east = (north + east).normalise()
    print(f'NORTH       {north:.3f}')
    print(f'NORTH-EAST  {north_east:.3f}')
    print(f'EAST        {east:.3f}\n')
    
    thetas = {}
    for i, B in enumerate(centered_points):
        # -- ORTHOGONAL == 0 (90 between)
        # -- INSERT BETWEEN CLOSEST POINTS
        # -- codirectional == mag(a) * mag(b) == 1
        thetas[i] = [vector.dot(north, B),
                     vector.dot(north_east, B),
                     vector.dot(east, B)]
        # merge into degrees from NORTH
        # use as sorting index / function
        
    for index in thetas:
        print('[', ' '.join([f'{x:.3f}' for x in points[index]]), ']', sep='')
        print(' '.join([f'{x:.3f}' for x in thetas[index]]))
        print()

    return O, north, north_east, east
        
##    sorted_points = [points[0]]
##    sorted_vectors += [indexed_thetas[key] for key in sorted(indexed_thetas)]
##    return sorted_vectors

def main(width, height):
    SDL_Init(SDL_INIT_VIDEO)
    window = SDL_CreateWindow(b'SDL2 OpenGL', SDL_WINDOWPOS_CENTERED,  SDL_WINDOWPOS_CENTERED, width, height, SDL_WINDOW_OPENGL | SDL_WINDOW_BORDERLESS)
    glContext = SDL_GL_CreateContext(window)
    SDL_GL_SetSwapInterval(0)
    glClearColor(0.1, 0.1, 0.1, 0.0)
    scale = 2
    glOrtho(-scale, scale, -scale, scale, 0, 1)
    glPointSize(4)

    points = [[0, 1], [1, 0], [0, -1], [-1, 0]]

    for i, point in enumerate(points[:]):
        points.insert(2 * i + 1, vector.vec2(point).rotate(45))

    points2 = points[1:] # preserve start for easier debug
    random.shuffle(points2)
    points = [points[0]] + points2
    del points2

    guides = clockwise_sort(points, vector.vec3(0, 0, 1))

    mousepos = vector.vec2()
    keys = dict()

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
                    keys[event.key.keysym.sym] = 0
            if event.type == SDL_KEYUP:
                keys.pop(event.key.keysym.sym)
            if event.type == SDL_MOUSEMOTION:
                mousepos = vector.vec2(event.motion.x, event.motion.y)
            if event.type == SDL_MOUSEBUTTONDOWN:
                if event.button.button not in keys:
                    keys[event.button.button] = 0
            if event.type == SDL_MOUSEBUTTONUP:
                keys.pop(event.button.button)
                    
            dt = time.time() - old_time
        while dt >= 1 / tickrate:
            for key in keys:
                keys[key] += 1
            dt -= 1 / tickrate
            old_time = time.time()
            
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        glColor(1, 1, 1)
        glBegin(GL_POINTS)
        glVertex(0, 0)
        glEnd()

        glLineWidth(4)
        glBegin(GL_LINE_STRIP)
        for i, point in enumerate(points):
            glColor(*colorsys.hsv_to_rgb(i / 8, 1, 1))
            glVertex(*point)
        glEnd()

        glColor(.75, .75, .75)
        glBegin(GL_POINTS)
        for point in points:
            glVertex(*point)
        glEnd()

        glColor(1, 1, 1)
        glLineWidth(3)
        glBegin(GL_LINES)
        glVertex(*guides[0])
        glVertex(*guides[1])
        glEnd()
        glLineWidth(1)
        glBegin(GL_LINES)
        for point in guides[2:]:
            glVertex(*guides[0])
            glVertex(*point)
        glEnd()

        glPushMatrix()
        glScale(.125, .125, 1)
        glTranslate(*(guides[1] * 10))
        glBegin(GL_LINE_STRIP)
        glVertex(-1, -1)
        glVertex(-1, 1)
        glVertex(1, -1)
        glVertex(1, 1)
        glEnd()
        glPopMatrix()

        glPushMatrix()
        glScale(.125, .125, 1)
        glTranslate(*(guides[2] * 10))
        glBegin(GL_LINE_STRIP)
        glVertex(-1.5, -1)
        glVertex(-1.5, 1)
        glVertex(-.5, -1)
        glVertex(-.5, 1)
        glEnd()
        glBegin(GL_LINES)
        glVertex(.5, -1)
        glVertex(.5, 1)
        glVertex(.5, 1)
        glVertex(1.5, 1)
        glVertex(.5, 0)
        glVertex(1.5, 0)
        glVertex(.5, -1)
        glVertex(1.5, -1)
        glEnd()
        glPopMatrix()

        glPushMatrix()
        glScale(.125, .125, 1)
        glTranslate(*(guides[3] * 10))
        glBegin(GL_LINES)
        glVertex(-1, -1)
        glVertex(-1, 1)
        glVertex(-1, 1)
        glVertex(1, 1)
        glVertex(-1, 0)
        glVertex(1, 0)
        glVertex(-1, -1)
        glVertex(1, -1)
        glEnd()
        glPopMatrix()
        
        SDL_GL_SwapWindow(window)
        

if __name__ == '__main__':
    import getopt
    import sys
    options = getopt.getopt(sys.argv[1:], 'w:h:')
    width = 256
    height = 256
    for option in options:
        for key, value in option:
            if key == '-w':
                width = int(value)
            elif key == '-h':
                height = int(value)
    main(width, height)

import colorsys
import ctypes
import math
from OpenGL.GL import *
from OpenGL.GLU import *
import random
from sdl2 import *
import time
import sys
sys.path.insert(0, 'examples/')
import vector

def sort_clockwise(vec3s, normal):
    C = sum(vec3s, vector.vec3()) / len(vec3s)
    score = lambda A, B: vector.dot(normal, (A - C) * (B - C))
    left = []
    right = []
    for index, point in enumerate(vec3s[1:]):
        (left if score(vec3s[0], point) >= 0 else right).append(index + 1)
    
    proximity = dict() # number of points between self and start
    for i, p in enumerate(vec3s[1:]):
        i += 1
        if i in left:
            proximity[i] = len(right)
            for j in left:
                if score(p, vec3s[j]) >= 0:
                    proximity[i] += 1
        else:
            proximity[i] = 0
            for j in right:
                if score(p, vec3s[j]) >= 0:
                    proximity[i] += 1
        
    sorted_vec3s = [vec3s[0]] + [vec3s[i] for i in sorted(proximity.keys(), key=lambda k: proximity[k])]
    return sorted_vec3s

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

    points = [vector.vec3(*p, 0) for p in points]
    sorted_points = sort_clockwise(points, vector.vec3(0, 0, 1))

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
            glColor(*colorsys.hsv_to_rgb(i / 8, .5, 1))
            glVertex(*(point * 1.25))
        glEnd()

        glLineWidth(2)
        glBegin(GL_LINE_STRIP)
        for i, point in enumerate(sorted_points):
            glColor(*colorsys.hsv_to_rgb(i / 8, 1, 1))
            glVertex(*point)
        glEnd()
        
        SDL_GL_SwapWindow(window)
        

if __name__ == '__main__':
    try:
        while True:
            main(512, 512)
    except Exception as exc:
        SDL_Quit()
        raise exc

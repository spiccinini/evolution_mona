#!/usr/bin/env python
# -*- coding: UTF-8 -*-

# Copyright (c) 2009 Piccinini Santiago
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import pygame
from pygame.locals import QUIT, KEYDOWN, K_ESCAPE
import numpy # Only working with numpy
import sys, random, time

try:
    pygame.surfarray.use_arraytype("numpy")
except ValueError:
    print "You need numpy to run this program."

NUM_POLY = 50
NUM_VERTEX = 6
RES = (200,200)
SIZE = (200, 200)

def rnd_8b():
    return random.getrandbits(8)

def rand_point():
    return [random.randint(0, SIZE[0]-1), random.randint(0, SIZE[1]-1)]

def rand_color_RGBA():
    return [rnd_8b(), rnd_8b(), rnd_8b(), rnd_8b()]

def rand_triang(center,sup_bound):
    r = random.triangular(0, sup_bound, center)
    if r >sup_bound:
        r = sup_bound
    elif r < 0:
        r = 0
    return r

def rand_gauss(mu, sigma, sup_bound):
    r = random.gauss(mu, sigma)
    if r >sup_bound:
        r = sup_bound
    elif r < 0:
        r = 0
    return r


class Polygon(object):
    def __init__(self, points, color_RGBA):
        self.points = points
        self.color_RGBA = color_RGBA

    def mutate(self):
        """ Random mutation of one element of the polygon.
        """
        self.mutate_medium()


    def mutate_medium(self):
        r = random.uniform(0, 2)
        if r < 1:
            if r < 0.25:
                self.color_RGBA[0] = random.getrandbits(8)
            elif r < 0.5:
                self.color_RGBA[1] = random.getrandbits(8)
            elif r < 0.75:
                self.color_RGBA[2] = random.getrandbits(8)
            else:
                self.color_RGBA[3] = random.getrandbits(8)
        else:
            point = self.points[random.randint(0, NUM_VERTEX-1)]
            if r <1.5:
                point[0] =  random.randint(0, SIZE[0]-1)
            else:
                point[1] =  random.randint(0, SIZE[0]-1)

    def mutate_triang(self):
        r = random.uniform(0, 2)
        if r < 1:
            if r < 0.25:
                self.color_RGBA[0] = rand_triang(self.color_RGBA[0],255)
            elif r < 0.5:
                self.color_RGBA[1] = rand_triang(self.color_RGBA[1],255)
            elif r < 0.75:
                self.color_RGBA[2] = rand_triang(self.color_RGBA[2],255)
            else:
                self.color_RGBA[3] = rand_triang(self.color_RGBA[3],255)
        else:
            point = self.points[random.randint(0, NUM_VERTEX-1)]
            if r <1.5:
                point[0] =  rand_triang(point[0],SIZE[0]-1)
            else:
                point[1] =  rand_triang(point[1],SIZE[1]-1)

    def mutate_gauss(self, sigma = 20):
        r = random.uniform(0, 2)
        if r < 1:
            if r < 0.25:
                self.color_RGBA[0] = rand_gauss(self.color_RGBA[0], sigma, 255)
            elif r < 0.5:
                self.color_RGBA[1] = rand_gauss(self.color_RGBA[1], sigma, 255)
            elif r < 0.75:
                self.color_RGBA[2] = rand_gauss(self.color_RGBA[2], sigma, 255)
            else:
                self.color_RGBA[3] = rand_gauss(self.color_RGBA[3], sigma, 255)
        else:
            point = self.points[random.randint(0, NUM_VERTEX-1)]
            if r <1.5:
                point[0] =  rand_gauss(point[0], sigma, SIZE[0]-1)
            else:
                point[1] =  rand_gauss(point[1], sigma, SIZE[1]-1)

    def deep_copy(self):
        return Polygon([point[:] for point in self.points],self.color_RGBA[:])

    def __str__(self):
        return  repr(self.points) + repr(self.color_RGBA)


def diff_2d(goal, test):
    """ Returns the difference of two pygame.surfarray.array2d matrix.
    To use only in 32 bit!
    """
    # Doing a workarround numpy's fucking interpretation of alpha chanell.
    goal.dtype = "uint32" # Special shake of bits to get the alpha channel
    test.dtype = "uint32" # because using int32 interprets the alpha channel
    s1 = (goal & 0xFF000000) >> 24 # in 2's complement when using numpy.
    s2 = (test & 0xFF000000) >> 24
    s1.dtype, s2.dtype, goal.dtype, test.dtype = "int32", "int32","int32","int32"
    d1 = numpy.absolute(s1 - s2)
    d2 = numpy.absolute(((goal & 0x00FF0000) >> 16) - ((test & 0x00FF0000) >> 16))
    d3 = numpy.absolute(((goal & 0x0000FF00) >> 8)  - ((test & 0x0000FF00) >> 8 ))
    d4 = numpy.absolute((goal & 0x000000FF )      - (test & 0x000000FF      ))
    return numpy.sum(d2)+numpy.sum(d3)+numpy.sum(d4) + numpy.sum(d1)

def diff_3d(goal_color,goal_alpha, test_color, test_alpha, rect=None):
    """ Returns the difference of two pygame.surfarray.array3d and two
    pygame.surfarray.array_alpha matrix. If rect, an optional pygame.Rect
    object, is supplyed diff_3d will take the difference only to that rectangle area.
    To use only with "int64" (TODO: check this).
    """
    if rect:
        x = rect.left
        xf = rect.left + rect.width+1
        y = rect.top
        yf = rect.height + rect.top+1

        r1 = numpy.sum(numpy.absolute(goal_color[x:xf][y:yf] - test_color[x:xf][y:yf]))
        r2 = numpy.sum(numpy.absolute(goal_alpha[x:xf][y:yf] - test_alpha[x:xf][y:yf]))
    else:
        r1 = numpy.sum(numpy.absolute(goal_color - test_color))
        r2 = numpy.sum(numpy.absolute(goal_alpha - test_alpha))
    return r1 + r2

def build_svg(polygons):
    import itertools

    svg ="""<?xml version="1.0" encoding="utf-8"?>
    <!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN" "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">
    <svg xmlns="http://www.w3.org/2000/svg"
    xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:ev="http://www.w3.org/2001/xml-events"
    version="1.1" baseProfile="full"
    width="800mm" height="600mm">
    """
    def to_svg_points(polygon):
        return "%d " *2*NUM_VERTEX % tuple([x for x in itertools.chain.from_iterable(polygon.points)])

    def to_svg_color(polygon):
        return ' fill="rgb(%d,%d,%d)" opacity="%f" />'  % (polygon.color_RGBA[0],polygon.color_RGBA[1],polygon.color_RGBA[2],polygon.color_RGBA[3]/255.0)

    def to_svg(polygon):
        return '<polygon points="' + to_svg_points(polygon)+'"' + to_svg_color(polygon) +'\n'

    for poly in polygons:
        svg += to_svg(poly)

    svg += "</svg>"

    f = open("evolved_mona.svg","w")
    f.write(svg)
    f.close()




if __name__ == '__main__':

    #Initialize polygons
    polygons = [Polygon([rand_point() for k in range(NUM_VERTEX)], rand_color_RGBA()) for n in range(NUM_POLY)]

    # Pygame init
    screen = pygame.display.set_mode(RES, pygame.SRCALPHA, 32)
    test_surf = pygame.Surface(SIZE, pygame.SRCALPHA, 32)
    #test_surf2 = pygame.Surface(SIZE, pygame.SRCALPHA)


    goal_img = pygame.image.load("mona.png").convert_alpha()
    goal_2d    = pygame.surfarray.array2d(goal_img)

    #screen.blit(mona_img,(0,0))
    #pygame.display.update()


    MAX_DIFF = 255 * 4 * SIZE[0]*SIZE[1]
    lowest_diff = MAX_DIFF
    n_intentos = 0
    n_mejoras = 0
    quit = False
    clock = pygame.time.Clock()
    clock.tick()
    while 1:
        event_list = pygame.event.get()
        for event in event_list:
            if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                quit = True
        if quit:
            break

        n_intentos +=1

        screen.fill((255,255,255,0))
        selected_poly_n = random.randint(0, NUM_POLY-1)
        selected_poly = polygons[selected_poly_n]
        selected_poly_copy = selected_poly.deep_copy() # To preserve the unmutated polygon.

        for poly in polygons:
            test_surf.fill((255,255,255,0))
            if poly == selected_poly:
                poly.mutate()
                changed_rectangle = pygame.draw.polygon(test_surf, poly.color_RGBA, poly.points, 0)

            changed_rectangle = pygame.draw.polygon(test_surf, poly.color_RGBA, poly.points, 0)
            screen.blit(test_surf,(0,0), changed_rectangle)

        difference = diff_2d(goal_2d, pygame.surfarray.array2d(screen))

        if difference < lowest_diff:
            lowest_diff = difference
            n_mejoras += 1
            print "mejora N %d, intentos %d, equal %%%f " % (n_mejoras, n_intentos, MAX_DIFF/float(difference)*10,)

        else: # recover the mutated poly
            polygons[selected_poly_n] = selected_poly_copy.deep_copy()

        # Display time
        if n_intentos % 100 == 0:
            time = clock.get_time()
            if time:
                print "%d intentos por segundo" % (100000/time, )


            clock.tick()


        pygame.display.update()


    build_svg(polygons)


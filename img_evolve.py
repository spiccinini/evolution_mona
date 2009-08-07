from pygame.locals import QUIT, KEYDOWN, K_ESCAPE
import sys, pygame
from pygame import Surface
import pygame.gfxdraw
import itertools
import random
import time
import numpy

NUM_POLY = 25
NUM_VERTEX = 6
RES = (200,200)
SIZE = (200, 200)

def rnd_8b():
    return random.getrandbits(8)

def rand_point():
    return [random.randint(0, SIZE[0]-1), random.randint(0, SIZE[1]-1)]

def rand_color_RGBA():
    return [rnd_8b(), rnd_8b(), rnd_8b(), rnd_8b()]
    

class Polygon(object):
    def __init__(self, points, color_RGBA):
        self.points = points
        self.color_RGBA = color_RGBA

    def mutate(self):
        """ Random mutation of one element of the polygon.
        """
        r = random.uniform(0, 2)
        if r < 1:
            if r < 0.25:
                self.color_RGBA[0] = rnd_8b()
            elif r < 0.5:
                self.color_RGBA[1] = rnd_8b()
            elif r < 0.75:
                self.color_RGBA[2] = rnd_8b()
            else:
                self.color_RGBA[3] = rnd_8b()
        else:
            point = self.points[random.randint(0, NUM_VERTEX-1)]
            if r <1.5:
                point[0] =  random.randint(0, SIZE[0]-1)
            else:
                point[1] =  random.randint(0, SIZE[0]-1)

    def deep_copy(self):
        return Polygon([point[:] for point in self.points],self.color_RGBA[:])

    def __str__(self):
        return  repr(self.points) + repr(self.color_RGBA)

    def _to_svg_points(self):
        return "%d " *2*NUM_VERTEX % tuple([x for x in itertools.chain.from_iterable(self.points)])

    def _to_svg_color(self):
        return ' fill="rgb(%d,%d,%d)" opacity="%f" />'  % (poly.color_RGBA[0],poly.color_RGBA[1],poly.color_RGBA[2],poly.color_RGBA[3]/255.0)
    def to_svg(self):
        return '<polygon points="' + self._to_svg_points()+'"' + self._to_svg_color() +'\n'


polygons = [Polygon([rand_point() for k in range(NUM_VERTEX)], rand_color_RGBA()) for n in range(NUM_POLY)]


# Pygame init
screen = pygame.display.set_mode(RES, pygame.SRCALPHA)
test_surf = pygame.Surface(SIZE, pygame.SRCALPHA)
test_surf2 = pygame.Surface(SIZE, pygame.SRCALPHA)


goal_img = pygame.image.load("mona.png").convert_alpha()
goal_2d    = pygame.surfarray.array2d(goal_img)
#mona_array = pygame.surfarray.array2d(mona_img).astype("int64")

#screen.blit(mona_img,(0,0))
#pygame.display.update()

def diff_2d(goal, test):
    """ Returns the difference of two pygame.surfarray.array2d matrix.
    To use only in 32 bit! 
    """
    goal.dtype = "uint32"
    test.dtype = "uint32"
    s1 = (goal & 0xFF000000) >> 24
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
    To use only in 32 bit! 
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

"""
goal_color = pygame.surfarray.array3d(goal_img).astype("int64")
goal_alpha = pygame.surfarray.array_alpha(goal_img).astype("int64")
test_surf.fill((255,0,0,5))
test_color = pygame.surfarray.array3d(test_surf).astype("int64")
test_alpha = pygame.surfarray.array_alpha(test_surf).astype("int64")
goal_2d    = pygame.surfarray.array2d(goal_img)
test_2d    = pygame.surfarray.array2d(test_surf)

print time.time()
print diff_3d(goal_color,goal_alpha, test_color, test_alpha)
print time.time()
print diff_2d(goal_2d,test_2d)
print time.time()
print diff_2d(goal_2d,test_2d)
print time.time()
"""

MAX_DIFF = 255 * 4 *SIZE[0]*SIZE[1]
lowest_diff = MAX_DIFF
n_intentos = 0
n_mejoras = 0
quit = False
while 1:
    n_intentos +=1
    event_list = pygame.event.get()
    for event in event_list:
        if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
            quit = True
    if quit:
        break

    screen.fill((255,255,255,0))
    selected_poly_n = random.randint(0, NUM_POLY-1)
    selected_poly = polygons[selected_poly_n]
    selected_poly_copy = selected_poly.deep_copy()
    
    for poly in polygons:
        test_surf.fill((255,255,255,0))
        if poly == selected_poly:
            poly.mutate()
            changed_rectangle = pygame.draw.polygon(test_surf, poly.color_RGBA, poly.points, 0)

        changed_rectangle = pygame.draw.polygon(test_surf, poly.color_RGBA, poly.points, 0)
        screen.blit(test_surf,(0,0), changed_rectangle)

    #difference = diff_3d(goal_color,goal_alpha, pygame.surfarray.array3d(screen).astype("int64"),  pygame.surfarray.array_alpha(screen).astype("int64"))
    difference = diff_2d(goal_2d, pygame.surfarray.array2d(screen))

    if difference < lowest_diff:
        lowest_diff = difference
        n_mejoras += 1
        print "mejora N %d, intentos %d, equal %%%f " % (n_mejoras, n_intentos, MAX_DIFF/float(difference)*10,)

    else: # recover the mutated poly
        polygons[selected_poly_n] = selected_poly_copy.deep_copy()
    pygame.display.update()


svg ="""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN" "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">
<svg xmlns="http://www.w3.org/2000/svg"
xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:ev="http://www.w3.org/2001/xml-events"
version="1.1" baseProfile="full"
width="800mm" height="600mm">
"""

import itertools
for poly in polygons:
    print poly
    svg += poly.to_svg()

svg += "</svg>"

f = open("evolved_mona.svg","w")
f.write(svg)
f.close()


time.sleep(1)

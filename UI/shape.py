import pygame as pg

def isoceles_triangle(dimensions: tuple[int, int], color = (0,0,0,255)) -> pg.Surface:
    surf = pg.Surface(dimensions, pg.SRCALPHA)
    surf.fill((255,255,255,0))
    pg.draw.polygon(
        surf,
        color,
        (
            (dimensions[0], dimensions[1] / 2),
            (0,0),
            (0, dimensions[1])
        )
    )
    return surf

def circle(radius, color: tuple[int,int,int,int] = (0,0,0,255)) -> pg.Surface:
    surf = pg.Surface((radius, radius), pg.SRCALPHA)
    surf.fill((255,255,255,0))
    pg.draw.circle(surf, color, (radius / 2, radius / 2), radius)
    return surf

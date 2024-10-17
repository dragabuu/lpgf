from typing import Any
import pygame as pg
from math import ceil
from shape import circle, isoceles_triangle

class Pane(pg.Surface):

    on_click = lambda self, m_pos: None
    on_click_release = lambda self, m_pos: None
    on_click_held = lambda self, m_pos: None
    on_middle_click = lambda self, m_pos: None
    on_middle_click_release = lambda self, m_pos: None
    on_middle_click_held = lambda self, m_pos: None
    on_right_click = lambda self, m_pos: None
    on_right_click_release = lambda self, m_pos: None
    on_right_click_held = lambda self, m_pos: None
    on_mouse_move = lambda self, l_m_pos, m_pos: None
    on_mouse_enter = lambda self, m_pos: None
    on_mouse_exit = lambda self, m_pos: None

    def get_screen_position(self):
        if isinstance(self._parent, Pane):
            screen_position = self._parent.get_screen_position()
            return (
                self.position[0] + screen_position[0],
                self.position[1] + screen_position[1]
            )
        return self.position
    
    
    def get_screen_rect(self):
        return self.get_rect().move(self.get_screen_position())

    def get_rect(self) -> pg.Rect:
        return super().get_rect().move(*self.position)
    
    def get_rect_position_zero(self) -> pg.Rect:
        return super().get_rect()

    def master_pane(dimensions: tuple[int,int], blanking_color: tuple[int,int,int] = (0,0,0), **kwargs) -> 'Pane':
        return Pane(
            dimensions,
            (0,0),
            pg.display.set_mode(dimensions, **kwargs),
            blanking_color=blanking_color,
            **kwargs
        )

    def __init__(
        self,
        dimensions: tuple[int,int], 
        position: tuple[int, int], 
        parent: pg.Surface,
        blanking_color: tuple[int,int,int] = (0,0,0),
        background_image: pg.Surface | None = None,
        flags=0      
    ):
        self._m_last_state = [False,False,False]
        self._m_last_inframe = False
        self._m_last_pos = pg.mouse.get_pos()
        self.position = position
        self.blanking_color = blanking_color
        self._background_image = background_image
        self._subpanes: list['Pane'] = []
        if isinstance(parent, Pane):
            parent.add_subpane(self)
        else:
            self._parent = parent
        super().__init__(dimensions, flags)

    def add_subpane(self, subpane: 'Pane') -> None:
        subpane._parent = self
        self._subpanes.append(subpane)

    def blank(self) -> None:
        self.fill(self.blanking_color)
        if self._background_image:
            self.blit(self._background_image, (0,0))
        for subpane in self._subpanes:
            subpane.blank() 
    
    #TODO: integrate this with the pg event system rather than polling
    def poll_mouse(self, _m_upper_pane_position: tuple[int,int] | None = None, _occluded: bool = False) -> None:
        if not _m_upper_pane_position:
            _m_upper_pane_position = pg.mouse.get_pos()
        m_pos = (
            _m_upper_pane_position[0] - self.position[0],
            _m_upper_pane_position[1] - self.position[1]
        )

        for subpane in self._subpanes[::-1]:
            subpane.poll_mouse(m_pos, _occluded)
            if not _occluded and subpane.get_rect().collidepoint(m_pos): _occluded = True

        m_state = pg.mouse.get_pressed()
        m_inframe = not _occluded and pg.mouse.get_focused() and self.get_rect_position_zero().collidepoint(m_pos)

        if not m_state[0] and self._m_last_state[0]:
            self.on_click_release(m_pos)
            self._m_last_state[0] = False
        if not m_state[1] and self._m_last_state[1]:
            self.on_middle_click_release(m_pos)
            self._m_last_state[1] = False
        if not m_state[2] and self._m_last_state[2]:
            self.on_right_click_release(m_pos)
            self._m_last_state[2] = False

        if m_inframe:
            if m_state[0]:
                self.on_click_held(m_pos)
                if not self._m_last_state[0]: self.on_click(m_pos)
            if m_state[1]:
                self.on_middle_click_held(m_pos)
                if not self._m_last_state[1]: self.on_middle_click(m_pos)
            if m_state[2]:
                self.on_right_click_held(m_pos)
                if not self._m_last_state[2]: self.on_right_click(m_pos)
            if m_pos != self._m_last_pos:
                self.on_mouse_move(self._m_last_pos, m_pos)

        for index, state in enumerate(m_state):
            if state: self._m_last_state[index] = True
        
        #this is done so the on_click_release callback is still called if mouse is out of frame

        if m_inframe and not self._m_last_inframe:
            self.on_mouse_enter(m_pos)
        elif not m_inframe and self._m_last_inframe:
            self.on_mouse_exit(m_pos)

        self._m_last_inframe = m_inframe
        self._m_last_pos = m_pos
        
    def update(self, **draw_options):
        for subpane in self._subpanes:
            subpane.update()

    def move_to_front(self, item):
        if item not in self._subpanes:
            return
        self._subpanes.remove(item)
        self._subpanes.append(item)
    
    def draw(self, special_flags: int = 0):
        for subpane in self._subpanes:
            subpane.draw()
        self._parent.blit(self, self.position, special_flags=special_flags)

class DynamicPane(Pane):

    @property
    def content_pane(self):
        return self._content_pane

    def _stick(self, _):
        self._stuck = True
        self._parent.move_to_front(self)

    def _unstick(self, _):
        self._stuck = False
        parent_rect = self._parent.get_rect()
        self_rect = self.get_rect()
        if not parent_rect.collidepoint(self_rect.center):
            self.position = (
                parent_rect.center[0] - ceil(self_rect.width / 2),
                parent_rect.center[1] - ceil(self_rect.height / 2)
            )

    def __init__(
            self,
            dimensions: tuple[int,int],
            position: tuple[int,int,int],
            parent: Pane,
            ribbon_height: int,
            ribbon_color: tuple[int,int,int] = (255,255,255),
            blanking_color: tuple[int,int,int] = (0,0,0),
            background_image: pg.Surface | None = None,
            content_flags=0,
            ribbon_flags=0
    ):
        super().__init__(
            dimensions,
            position,
            parent,
            (255,255,255,0),
            flags=pg.SRCALPHA
        )
        self._ribbon: Pane = Pane(
            (dimensions[0], ribbon_height),
            (0,0),
            self,
            ribbon_color,
            flags=ribbon_flags
        )
        self._content_pane: Pane = Pane(
            (dimensions[0], dimensions[1] - ribbon_height),
            (0, ribbon_height),
            self,
            blanking_color=blanking_color,
            background_image=background_image,
            flags=content_flags
        )
        self._stuck = False
        self._ribbon.on_click = self._stick
        self._ribbon.on_click_release = self._unstick

    def update(self):
        m_pos = pg.mouse.get_pos()
        s_pos = self.get_screen_position()
        m_pane_pos = (
            m_pos[0] - s_pos[0],
            m_pos[1] - s_pos[1]
        )
        if self._stuck:
            delta = (
                m_pane_pos[0] - self._m_last_pos[0],
                m_pane_pos[1] - self._m_last_pos[1]
            )
            self.position = (
                self.position[0] + delta[0],
                self.position[1] + delta[1]
            )

        super().update()
    
#this isn't done I just wanted to get this in version control
class Slider(Pane):

    def __init__(
            self,
            dimensions: tuple[int,int],
            parent: Pane,
            knob_size: int,
            bar_thickness: int,
            knob_color: tuple[int,int,int] = (255,255,255),
            bar_color: tuple[int,int,int] = (150,150,150)
    ):
        self._bar = Pane(
            (dimensions[0], bar_thickness),
            (0, ceil(dimensions[1] / 2) + ceil(bar_thickness / 2)),
            self,
            bar_color
        )
        self._knob = Pane(
            (knob_size, knob_size),
            (0, ceil(dimensions[1] / 2) + ceil(knob_size / 2)),
            self,
            (0,0,0,0),
            background_image=circle(knob_size, knob_color)
        )
        
from math import log, sqrt
from random import randint
from tkinter import Tk
from typing import Tuple, Optional, List, Dict, Callable, Union

import pygame

from engine import Engine
from physics import Particle
from utils import Number


class CachedPropertiesMixin:
    def get_or_create(self, attr: str):
        try:
            return getattr(self, f"_{attr}")
        except AttributeError:
            return self.get_updated(attr)

    def get_cached(self, attr: str):
        return getattr(self, f"_{attr}", None)

    def get_updated(self, attr: str):
        value = getattr(self, f"compute_{attr}")()
        setattr(self, f"_{attr}", value)
        return value


class GraphicalOptions:
    def __init__(self, window_size: Tuple[Number, Number] = None):
        self.size = self.get_window_size(window_size)
        self.zoom_level: Number = 5
        self.represented_dimensions: Tuple[Number, Number] = (0, 1)
        self.background_color = (0, 0, 0)
        self.shift_level = [0, 0]
        self.draw_trajectories = False

    @staticmethod
    def get_window_size(window_size: Optional[Tuple[Number, Number]] = None) -> Tuple[Number, Number]:
        if window_size:
            return window_size
        screen = Tk()
        return screen.winfo_screenwidth(), screen.winfo_screenheight()


class GraphicalParticle(Particle, CachedPropertiesMixin):
    def __init__(self, mass: Number, position: List[Number], velocity: List[Number], options: GraphicalOptions):
        super().__init__(mass, position, velocity)
        self.options = options
        self.old_position: List[Number]

    @staticmethod
    def compute_color():
        return randint(0, 255), randint(0, 255), randint(0, 255)

    def compute_size(self) -> int:
        return round(log(sqrt(self.mass)))

    def compute_graphical_position(self) -> Tuple[Number, Number]:
        return (
            (self._position[self.options.represented_dimensions[0]] / self.options.zoom_level)
            + (self.options.size[0] / 2)
            + self.options.shift_level[0],
            (self._position[self.options.represented_dimensions[1]] / self.options.zoom_level)
            + (self.options.size[1] / 2)
            + self.options.shift_level[1],
        )


class GraphicalEngine2D(Engine):
    def __init__(self, window_size: Tuple[Number, Number] = None):
        self._event_listeners: Dict[int, Union[Callable, Dict[int, Tuple[Callable, Tuple]]]] = {
            pygame.QUIT: self.quit,
            pygame.KEYDOWN: {
                pygame.K_KP_PLUS: (self.zoom, (1.1,)),
                pygame.K_KP_MINUS: (self.zoom, (0.9,)),
                pygame.K_UP: (self.shift_view, ((0, 100),)),
                pygame.K_DOWN: (self.shift_view, ((0, -100),)),
                pygame.K_LEFT: (self.shift_view, ((100, 0),)),
                pygame.K_RIGHT: (self.shift_view, ((-100, 0),)),
            },
        }
        self.particles: List[GraphicalParticle]
        self.options = GraphicalOptions(window_size)
        self._window = pygame.display.set_mode(self.options.size)
        self._must_erase = False
        super().__init__(GraphicalParticle, {"options": self.options})

    def run_custom_engine_features(self):
        if self._must_erase:
            self.erase_particles()
        self._must_erase = not self.options.draw_trajectories
        self.update_particles()
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                self.dispatch_keydown(event)
            elif event.type == pygame.QUIT:
                self.quit()
        pygame.display.flip()

    def dispatch_keydown(self, event):
        function, parameters = self._event_listeners[pygame.KEYDOWN].get(event.key, (None, None))
        if function is not None:
            function(*parameters)

    def quit(self):
        self._keep_running = False

    def zoom(self, factor: Number):
        self.options.zoom_level *= factor
        self._must_erase = True

    def shift_view(self, shift: Tuple[Number, Number]):
        self.options.shift_level[0] += shift[0]
        self.options.shift_level[1] += shift[1]
        self._must_erase = True

    def update_particles(self):
        particle: GraphicalParticle
        for particle in self.particles:
            pygame.draw.circle(
                self._window,
                particle.get_or_create("color"),
                [int(i) for i in particle.get_updated("graphical_position")],
                particle.get_updated("size"),
                particle.get_cached("size"),
            )

    def erase_particles(self):
        self._window.fill(self.options.background_color)


if __name__ == "__main__":
    engine = GraphicalEngine2D()
    engine.run()

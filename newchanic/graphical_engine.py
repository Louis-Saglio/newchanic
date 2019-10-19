from random import randint
from tkinter import Tk
from typing import Tuple, Optional, List

import pygame

from engine import Engine
from physics import Particle
from utils import Number


class CachedPropertiesMixin:
    def get_cached(self, attr: str):
        return getattr(self, f"_{attr}", None)

    def get_updated(self, attr: str):
        value = getattr(self, f"compute_{attr}")()
        setattr(self, f"_{attr}", value)
        return value


class GraphicalOptions:
    def __init__(self, window_size: Tuple[Number, Number] = None):
        self.size = self.get_window_size(window_size)
        self.zoom_level: Number = 1
        self.represented_dimensions: Tuple[Number, Number] = (0, 1)
        self.background_color = (0, 0, 0)

    @staticmethod
    def get_window_size(window_size: Optional[Tuple[Number, Number]] = None):
        if window_size:
            return window_size
        screen = Tk()
        return screen.winfo_screenheight(), screen.winfo_screenwidth()


class GraphicalParticle(Particle, CachedPropertiesMixin):
    def __init__(self, mass: Number, position: List[Number], velocity: List[Number], options: GraphicalOptions):
        super().__init__(mass, position, velocity)
        self.options = options

    @property
    def color(self):
        return randint(0, 255), randint(0, 255), randint(0, 255)

    def compute_size(self) -> int:
        return 3

    def compute_graphical_position(self) -> Tuple[Number, Number]:
        return (
            (self._position[self.options.represented_dimensions[0]] / self.options.zoom_level)
            + (self.options.size[0] / 2),
            (self._position[self.options.represented_dimensions[1]] / self.options.zoom_level)
            + (self.options.size[1] / 2),
        )


class GraphicalEngine(Engine):
    def __init__(self, window_size: Tuple[Number, Number] = None):
        self.particles: List[GraphicalParticle]
        self.options = GraphicalOptions(window_size)
        self._window = pygame.display.set_mode(self.options.size)
        super().__init__(GraphicalParticle, {"options": self.options})

    def run_custom_engine_features(self):
        self.update_particles()

    def update_particles(self):
        particle: GraphicalParticle
        for particle in self.particles:
            pygame.draw.circle(
                self._window,
                particle.color,
                particle.get_updated("graphical_position"),
                particle.get_updated("size"),
                particle.get_cached("size"),
            )

    def erase_particles(self):
        particle: GraphicalParticle
        for particle in self.particles:
            pygame.draw.circle(
                self._window,
                self.options.background_color,
                particle.get_cached("graphical_position"),
                particle.get_cached("size"),
                particle.get_cached("size"),
            )


if __name__ == "__main__":
    engine = GraphicalEngine()
    engine.run()

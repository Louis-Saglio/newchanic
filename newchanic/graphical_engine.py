from itertools import combinations
from math import sqrt
from random import randint
from time import time
from typing import Tuple, List, Dict, Callable, Union, Any

import pygame

from engine import Engine
from physics import Particle
from utils import Number


class CachedPropertiesMixin:
    def get_or_create(self, attr: str):
        try:
            return self.get_cached(attr)
        except AttributeError:
            return self.get_updated(attr)

    def get_cached(self, attr: str):
        return getattr(self, f"_{attr}")

    def get_updated(self, attr: str):
        value = getattr(self, f"compute_{attr}")()
        setattr(self, f"_{attr}", value)
        return value


class GraphicalOptions:
    def __init__(
        self, represented_dimensions: Tuple[int, int] = (0, 1), window_size: Tuple[Number, Number] = None,
    ):
        self.represented_dimensions: Tuple[Number, Number] = represented_dimensions
        self.size = window_size or self.get_window_size()
        self.shift_level = [0, 0]
        self.zoom_level: Number = 1

    @staticmethod
    def get_window_size() -> Tuple[Number, Number]:
        from tkinter import Tk

        screen = Tk()
        return screen.winfo_screenwidth(), screen.winfo_screenheight()


class GraphicalParticle(Particle, CachedPropertiesMixin):
    def __init__(self, mass: Number, position: List[Number], velocity: List[Number], options: GraphicalOptions):
        super().__init__(mass, position, velocity)
        self.options = options
        self.old_position: List[Number]

    @staticmethod
    def compute_color():
        return randint(50, 255), randint(50, 255), randint(50, 255)

    def compute_size(self) -> int:
        return round(sqrt(self.mass / (self.options.zoom_level * 7)))

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
    def __init__(self, graphical_options: Dict[str, Any] = None, *args, **kwargs):
        self._event_listeners: Dict[int, Union[Callable, Dict[int, Tuple[Callable, Tuple]]]] = {
            pygame.QUIT: self.quit,
            pygame.KEYDOWN: {
                pygame.K_KP_MINUS: (self.zoom, (1.1,)),
                pygame.K_KP_PLUS: (self.zoom, (0.9,)),
                pygame.K_UP: (self.shift_view, ((0, 100),)),
                pygame.K_DOWN: (self.shift_view, ((0, -100),)),
                pygame.K_LEFT: (self.shift_view, ((100, 0),)),
                pygame.K_RIGHT: (self.shift_view, ((-100, 0),)),
                pygame.K_SPACE: (self.reset_camera, ()),
                pygame.K_t: (self.toggle_trajectories_drawing, ()),
                pygame.K_r: (self.rotate_camera, ()),
            },
        }
        self.particles: List[GraphicalParticle]
        self._must_erase = False
        self._represented_dimensions_generator = self._build_represented_dimensions_generator()
        self.background_color = (0, 0, 0)
        self.draw_trajectories = True
        self.options = GraphicalOptions(**(graphical_options if graphical_options else {}),)
        self._window = pygame.display.set_mode(self.options.size)
        super().__init__(*args, particle_type=GraphicalParticle, particle_kwargs={"options": self.options}, **kwargs)
        self.options.represented_dimensions = next(self._represented_dimensions_generator)

    def detect_dimensions_number(self):
        if not self.particles:
            raise RuntimeError(
                "Unable to detect the number of dimensions because no particle has been added to the engine"
            )
        return max([len(p.position) for p in self.particles])

    def run_custom_engine_features(self):
        if self._must_erase:
            self.erase_particles()
        self._must_erase = not self.draw_trajectories
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

    def reset_camera(self):
        self.options.shift_level[0], self.options.shift_level[1], self.options.zoom_level = 0, 0, 1
        self._must_erase = True

    def toggle_trajectories_drawing(self):
        self.draw_trajectories = not self.draw_trajectories

    def rotate_camera(self):
        self.options.represented_dimensions = next(self._represented_dimensions_generator)
        self._must_erase = True

    def _build_represented_dimensions_generator(self):
        while True:
            for represented_dimensions in combinations(range(self.detect_dimensions_number()), 2):
                yield represented_dimensions

    def update_particles(self):
        particle: GraphicalParticle
        for particle in self.particles:
            pygame.draw.circle(
                self._window,
                particle.get_or_create("color"),
                [int(i) for i in particle.get_updated("graphical_position")],
                particle.get_updated("size"),
                particle.get_updated("size"),
            )

    def erase_particles(self):
        self._window.fill(self.background_color)


if __name__ == "__main__":

    def main():
        engine = GraphicalEngine2D(graphical_options={}, particle_number=50)
        start = time()
        turn_number = engine.run()
        print(f"{round((time() - start) / turn_number, 3)} seconds by turn")

    main()

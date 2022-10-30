from collections.abc import Sequence
from itertools import zip_longest


class DelayedUpdateMixin:
    NEXT_VALUES_ATTR_NAME = "_next_values"

    def __init__(self):
        super().__setattr__(self.NEXT_VALUES_ATTR_NAME, {})

    def __setattr__(self, key, value):
        super().__getattribute__(self.NEXT_VALUES_ATTR_NAME)[key] = value

    def update(self):
        for key, value in getattr(self, self.NEXT_VALUES_ATTR_NAME).items():
            self.__dict__[key] = value


class Particle:
    MASS: float
    _position: list[float]
    _speed: list[float]
    position: Sequence[float]

    def __init__(self):
        super().__init__()
        super().__setattr__("manager", DelayedUpdateMixin())
        self.MASS = 0
        self._position = []
        self.position = self._position
        self._speed = []
        self.update()

    def __getattr__(self, item):
        return getattr(super().__getattribute__("manager"), item)

    def __setattr__(self, key, value):
        setattr(super().__getattribute__("manager"), key, value)

    def receive_force(self, force: list[float]) -> None:
        pass

    def __hash__(self):
        return id(self)


class Law:
    def compute_force_intensity_from_interaction_between(self, particle_0: Particle, particle_1: Particle) -> float:
        raise NotImplementedError


class Engine:
    particles: list[Particle]
    laws: list[Law]
    _already_computed_interactions: set[frozenset[Particle]]

    def __init__(self):
        self.particles = []
        self.laws = []
        self._already_computed_interactions = set()

    def run(self):
        while True:
            for particle_0 in self.particles:
                for particle_1 in self.particles:
                    if particle_0 is particle_1:
                        continue
                    total_force: list[float] = []
                    for law in self.laws:

                        force_intensity = law.compute_force_intensity_from_interaction_between(particle_0, particle_1)

                        force_vector = []
                        for p0_dim_pos, p1_dim_pos in zip_longest(particle_0.position, particle_1.position):
                            if p0_dim_pos is None or p1_dim_pos is None:
                                force_vector.append(0.0)
                            else:
                                force_vector.append((p0_dim_pos - p1_dim_pos) * force_intensity)

                        for i, dimensional_force in enumerate(force_vector):
                            if i >= len(total_force):
                                total_force.append(0)
                            total_force[i] += dimensional_force

                    particle_1.receive_force(total_force)

            for particle in self.particles:
                particle.update()

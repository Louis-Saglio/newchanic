from typing import List, Dict, Set

from utils import Number


class DelayedUpdateMixin:
    # todo : move to utils
    def __init__(self):
        self._next_values = {}

    def delay_update(self, field: str, value):
        self._next_values[field] = value

    def update(self):
        for field, value in self._next_values.items():
            try:
                setattr(self, field, value)
            except AttributeError as e:
                raise e


class ReadOnlyParticle:
    @property
    def mass(self) -> Number:
        raise NotImplementedError

    @property
    def position(self):
        raise NotImplementedError


class Particle(DelayedUpdateMixin, ReadOnlyParticle):
    def __init__(self, mass: Number, position: List[Number], velocity: List[Number], *args, **kwargs):
        assert len(position) == len(velocity)
        super().__init__()
        self._mass = mass
        self._position = position
        self._velocity = velocity

    @property
    def mass(self):
        return self._mass

    @property
    def position(self):
        return self._position

    @position.setter
    def position(self, value):
        self._position = value

    def _receive_dimensional_force(self, dimensional_force: Number, dimension: int):
        # todo : delayed update
        self._velocity[dimension] += dimensional_force / self._mass

    def apply_force(self, force: List[Number], other: "Particle"):
        assert len(force) == len(self._velocity)
        for dimension, dimensional_force in enumerate(force):
            other._receive_dimensional_force(dimensional_force, dimension)
            self._receive_dimensional_force(-dimensional_force, dimension)

    def run(self):
        next_position = self._position.copy()
        for i, (dimensional_position, dimensional_velocity) in enumerate(zip(self._position, self._velocity)):
            next_position[i] = dimensional_position + dimensional_velocity
        self.delay_update("position", next_position)

    def __repr__(self):
        velocity = [round(v, 3) for v in self._velocity]
        position = [round(p, 3) for p in self._position]
        return f"{self.__class__.__name__}(mass={self.mass}, velocity={velocity}, position={position})"


class ForceGenerator:
    def compute_force(self, particle: ReadOnlyParticle, other_particle: ReadOnlyParticle) -> List[Number]:
        raise NotImplementedError


class ArbitraryLaw:
    def apply(self, particle: Particle, other_particle: Particle, engine) -> Dict[str, Set[Particle]]:
        raise NotImplementedError

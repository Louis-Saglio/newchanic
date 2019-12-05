from math import sqrt
from random import random
from typing import List, Type, Dict, Set, Generic, TypeVar, Any, Callable

from physics import Particle, ForceGenerator, ReadOnlyParticle, ArbitraryLaw
from utils import Number


def dist(delta_x, delta_y):
    return sqrt(delta_x ** 2 + delta_y ** 2)


def compute_multi_dimensional_distance(position_1, position_2):
    first = dist(position_1[0] - position_2[0], position_2[1] - position_1[1])
    for p1, p2 in zip(position_1[2:], position_2[2:]):
        first = dist(first, p1 - p2)
    return first


def random_between(param, param1):
    assert param < param1
    return random() * abs(param - param1) + param


T = TypeVar("T")


class Feature(Generic[T]):
    key = None

    def update(self, data: T):
        raise NotImplementedError

    def __call__(self, engine: "Engine"):
        raise NotImplementedError


class RemoveFeature(Feature[Set]):
    def __init__(self):
        self.particles_to_remove = set()

    def update(self, data: Set[Particle]):
        self.particles_to_remove.update(data)

    def __call__(self, engine: "Engine"):
        engine.particles -= self.particles_to_remove  # May cause not null total force sum
        self.particles_to_remove.clear()


class Engine:
    def __init__(
        self,
        particle_number: int,
        particle_type: Type[Particle] = Particle,
        particle_kwargs: Dict[str, Any] = None,
        get_mass: Callable[[int], Number] = lambda _: random_between(10, 100),
        get_position: Callable[[int], List[Number]] = lambda _: [
            random_between(-1000, 1000),
            random_between(-500, 500),
            random_between(-500, 500),
        ],
        get_velocity: Callable[[int], List[Number]] = lambda _: [0, 0, 0],
    ):
        self.particles: Set[Particle] = self.init_particles(
            particle_number, particle_type, particle_kwargs, get_mass, get_position, get_velocity
        )
        self.force_generators = self.init_force_generators()
        self.arbitrary_laws = self.init_arbitrary_laws()
        self.features = {"remove": RemoveFeature()}
        self._keep_running = True

    @staticmethod
    def init_particles(
        particle_nbr: int,
        particle_type: Type[Particle],
        particle_kwargs: Dict[str, Any],
        get_mass: Callable[[int], Number],
        get_position: Callable[[int], List[Number]],
        get_velocity: Callable[[int], List[Number]],
    ) -> Set[Particle]:
        return {
            particle_type(
                mass=get_mass(i), position=get_position(i), velocity=get_velocity(i), **(particle_kwargs or {})
            )
            for i in range(particle_nbr)
        }

    def run_custom_engine_features(self):
        pass

    def run(self):
        while self._keep_running:
            for particle_1 in self.particles:
                for particle_2 in self.particles:
                    if particle_1 is not particle_2:
                        self.manage_particle_interaction(particle_1, particle_2)
            for feature in self.features.values():
                feature(self)
            for particle in self.particles:
                particle.update()
            self.run_custom_engine_features()

    def manage_particle_interaction(self, particle_1: Particle, particle_2: Particle):
        for law in self.arbitrary_laws:
            output = law.apply(particle_1, particle_2, self)
            for feature_name, data in output.items():
                self.features[feature_name].update(data)
        total_force = None
        for force_generator in self.force_generators:
            force = force_generator.compute_force(particle_1, particle_2)
            if total_force is None:
                total_force = force
            for dimension, (dimensional_total_force, dimensional_force) in enumerate(zip(total_force, force)):
                total_force[dimension] = dimensional_total_force + dimensional_force
        particle_1.apply_force(total_force, particle_2)
        particle_1.run()

    @staticmethod
    def init_force_generators() -> List[ForceGenerator]:
        class Gravity(ForceGenerator):
            g = 0.005

            def compute_force(self, particle: ReadOnlyParticle, other_particle: ReadOnlyParticle) -> List[Number]:
                distance = compute_multi_dimensional_distance(particle.position, other_particle.position)
                force = self.g * particle.mass * other_particle.mass / distance ** 2
                vector_force = []
                for p1_dimensional_position, p2_dimensional_position in zip(particle.position, other_particle.position):
                    vector_force.append((p1_dimensional_position - p2_dimensional_position) * force / distance)
                return vector_force

        return [Gravity()]

    @staticmethod
    def init_arbitrary_laws() -> List[ArbitraryLaw]:
        umd = 3  # universal minimum distance

        class Merge(ArbitraryLaw):
            def apply(self, particle: Particle, other_particle: Particle, engine: "Engine") -> Dict[str, Set[Particle]]:
                if particle.mass > other_particle.mass:
                    particle, other_particle = other_particle, particle
                if (
                    other_particle not in engine.features["remove"].particles_to_remove
                    and compute_multi_dimensional_distance(particle.position, other_particle.position) < umd
                    # < other_particle.compute_size() + particle.compute_size()
                ):
                    total_mass = particle.mass + other_particle.mass
                    p_share = particle.mass / total_mass
                    o_share = other_particle.mass / total_mass
                    # todo : Move position to the weighted mean of the two particles
                    other_particle.delay_update("_mass", total_mass)
                    # noinspection PyProtectedMember
                    other_particle.delay_update(
                        "_velocity",
                        [
                            p_velocity * p_share + o_velocity * o_share
                            for p_velocity, o_velocity in zip(particle._velocity, other_particle._velocity)
                        ],
                    )
                    particles_to_remove = {particle}
                else:
                    particles_to_remove = {}

                return {"remove": particles_to_remove}

        return [Merge()]

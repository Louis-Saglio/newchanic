from math import sqrt
from random import random
from typing import List, Type, Dict, Set

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


class EngineParticle(Particle):
    def __init__(self, mass: Number, position: List[Number], velocity: List[Number], *args, **kwargs):
        super().__init__(mass, position, velocity, *args, **kwargs)
        self.to_remove = False


class Engine:
    def __init__(self, particle_type: Type[Particle] = Particle, particle_kwargs=None):
        self.particle_kwargs = particle_kwargs
        self.particle_type = particle_type
        self.particles: Set[Particle] = self.init_particles()
        self.force_generators = self.init_force_generators()
        self.arbitrary_laws = self.init_arbitrary_laws()
        self._keep_running = True

    def init_particles(self, particle_nbr=200) -> Set[Particle]:
        # todo : carefully think this generic
        return {
            self.particle_type(
                random_between(1, 100),
                [random_between(-1000, 1000), random_between(-500, 500)],
                [0, 0],
                **(self.particle_kwargs or {})
            )
            for _ in range(particle_nbr)
        }

    def run_custom_engine_features(self):
        pass

    def run(self):
        while self._keep_running:
            particles_to_remove = set()
            for particle_1 in self.particles:
                for particle_2 in self.particles:
                    if particle_1 is not particle_2:
                        for law in self.arbitrary_laws:
                            output = law.apply(particle_1, particle_2)  # May cause not null total force sum
                            particles_to_remove.update(output["remove"])
                        total_force = None
                        for force_generator in self.force_generators:
                            force = force_generator.compute_force(particle_1, particle_2)
                            if total_force is None:
                                total_force = force
                            for dimension, (dimensional_total_force, dimensional_force) in enumerate(
                                zip(total_force, force)
                            ):
                                total_force[dimension] = dimensional_total_force + dimensional_force
                        particle_1.apply_force(total_force, particle_2)
                        particle_1.run()
            self.remove_particles(particles_to_remove)
            for particle in self.particles:
                particle.update()
            self.run_custom_engine_features()

    def remove_particles(self, particles: Set[Particle]):
        self.particles -= particles

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
            def apply(self, particle: Particle, other_particle: Particle) -> Dict[str, Set[Particle]]:
                if particle.mass > other_particle.mass:
                    particle, other_particle = other_particle, particle
                if (
                    compute_multi_dimensional_distance(particle.position, other_particle.position)
                    < umd
                    # < other_particle.compute_size() + particle.compute_size()
                ):
                    total_mass = particle.mass + other_particle.mass
                    p_share = particle.mass / total_mass
                    o_share = other_particle.mass / total_mass
                    # Move position to the weighted mean of the two particles
                    other_particle.delay_update("_mass", other_particle.mass + particle.mass)
                    # noinspection PyProtectedMember
                    other_particle.delay_update(
                        "_velocity",
                        [
                            particle._velocity[0] * p_share + other_particle._velocity[0] * o_share,
                            particle._velocity[1] * p_share + other_particle._velocity[1] * o_share,
                        ],
                    )
                    particles_to_remove = {particle}
                else:
                    particles_to_remove = {}

                return {"remove": particles_to_remove}

        return [Merge()]

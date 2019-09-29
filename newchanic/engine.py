from math import sqrt
from random import random
from typing import List

from physics import Particle, ForceGenerator, ReadOnlyParticle

import itertools

from utils import Number


def dist(delta_x, delta_y):
    return sqrt(delta_x ** 2 + delta_y ** 2)


def compute_multi_dimensional_distance(position_1, position_2):
    first = dist(position_1[0] - position_2[0], position_2[1] - position_1[1])
    for p1, p2 in zip(position_1[2:], position_2[2:]):
        first = dist(first, p1 - p2)
    return first


def random_between(param, param1):
    return random() * param + abs(param - param1)


class Engine:
    def __init__(self):
        self.particles = self.init_particles()
        self.force_generators = self.init_force_generators()

    @staticmethod
    def init_particles(particle_nbr=100) -> List[Particle]:
        return [Particle(random_between(0, 20), [random_between(-100, 100), random_between(-100, 100)], [0, 0]) for _ in range(particle_nbr)]

    def run(self):
        while True:
            for particle_1, particle_2 in itertools.combinations(self.particles, 2):
                total_force = None
                for force_generator in self.force_generators:
                    force = force_generator.compute_force(particle_1, particle_2)
                    if total_force is None:
                        total_force = force
                    for dimension, (dimensional_total_force, dimensional_force) in enumerate(zip(total_force, force)):
                        total_force[dimension] = dimensional_total_force + dimensional_force
            for particle in self.particles:
                particle.update()

    @staticmethod
    def init_force_generators() -> List[ForceGenerator]:
        class Gravity(ForceGenerator):
            def compute_force(self, particle: ReadOnlyParticle, other_particle: ReadOnlyParticle) -> List[Number]:
                distance = compute_multi_dimensional_distance(particle.position, other_particle.position)
                force = particle.mass * other_particle.mass / distance ** 2
                vector_force = []
                for p1_dimensional_position, p2_dimensional_position in zip(particle.position, other_particle.position):
                    vector_force.append((p2_dimensional_position - p1_dimensional_position) * force / distance)
                return vector_force

        return [Gravity()]


Engine().run()

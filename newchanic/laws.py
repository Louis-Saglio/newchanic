from typing import List, Dict, Set

from newchanic.engine import Engine
from newchanic.physics import ForceGenerator, ReadOnlyParticle, ArbitraryLaw, Particle
from newchanic.utils import Number, compute_multi_dimensional_distance


class Gravity(ForceGenerator):
    g = 0.005

    def compute_force(self, particle: ReadOnlyParticle, other_particle: ReadOnlyParticle) -> List[Number]:
        distance = compute_multi_dimensional_distance(particle.position, other_particle.position)
        force = self.g * particle.mass * other_particle.mass / distance ** 2
        vector_force = []
        for p1_dimensional_position, p2_dimensional_position in zip(particle.position, other_particle.position):
            vector_force.append((p1_dimensional_position - p2_dimensional_position) * force / distance)
        return vector_force


class Merge(ArbitraryLaw):
    umd = 3

    def apply(self, particle: Particle, other_particle: Particle, engine: "Engine") -> Dict[str, Set[Particle]]:
        if particle.mass > other_particle.mass:
            particle, other_particle = other_particle, particle
        if (
            other_particle not in engine.features["remove"].particles_to_remove
            and compute_multi_dimensional_distance(particle.position, other_particle.position) < self.umd
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

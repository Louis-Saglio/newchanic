from __future__ import annotations

from multiprocessing import Process, Queue
from typing import List, Type, Dict, Set, Generic, TypeVar, Any, Callable, Tuple

from newchanic.physics import ForceGenerator
from newchanic.utils import split_into_lists, random_between
from physics import Particle, ArbitraryLaw
from utils import Number

T = TypeVar("T")


class Feature(Generic[T]):
    def update(self, data: T):
        raise NotImplementedError

    def __call__(self, engine: Engine):
        raise NotImplementedError


class RemoveFeature(Feature[Set]):
    def __init__(self):
        self.particles_to_remove = set()

    def update(self, data: Set[Particle]):
        self.particles_to_remove.update(data)

    def __call__(self, engine: Engine):
        engine.particles -= self.particles_to_remove  # May cause not null total force sum
        self.particles_to_remove.clear()


class Engine:
    STOP_FLAG = "stop_flag"

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
        force_generators: Tuple[ForceGenerator] = (),
        arbitrary_laws: Tuple[ArbitraryLaw] = (),
    ):
        self.particles: Set[Particle] = self.init_particles(
            particle_number, particle_type, particle_kwargs, get_mass, get_position, get_velocity
        )
        self.force_generators = force_generators
        self.arbitrary_laws = arbitrary_laws
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

    def run_multicore(self, core_nbr: int) -> int:
        # todo : find out how many cores are best
        workers = []
        input_queue, output_queue = Queue(), Queue()
        for i in range(core_nbr):
            workers.append(
                Process(
                    target=process_particle_interaction,
                    args=(input_queue, output_queue, self.force_generators),
                )
            )
        [worker.start() for worker in workers]
        i = 0
        while self._keep_running:
            items_by_worker = split_into_lists(list(self.particles), core_nbr)
            for items in items_by_worker:
                input_queue.put((items, self.particles))
            particles = set()
            for _ in items_by_worker:
                particles.update(output_queue.get())
            self.particles = particles
            self.run_custom_engine_features()
            i += 1
        [input_queue.put(Engine.STOP_FLAG) for _ in workers]
        return i

    def run(self) -> int:
        i = 0
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
            i += 1
        return i

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


def process_particle_interaction(input_queue: Queue, output_queue: Queue, force_generators: Tuple[ForceGenerator]):
    while True:
        data = input_queue.get()
        if data == Engine.STOP_FLAG:
            break
        particles_to_process: List[Particle] = data[0]
        particles: Set[Particle] = data[1]
        for particle_1 in particles_to_process:
            for particle_2 in particles:
                if particle_1 is not particle_2:
                    total_force = None
                    for force_generator in force_generators:
                        force = force_generator.compute_force(particle_1, particle_2)
                        if total_force is None:
                            total_force = force
                        for dimension, (dimensional_total_force, dimensional_force) in enumerate(
                            zip(total_force, force)
                        ):
                            total_force[dimension] = dimensional_total_force + dimensional_force
                    particle_1.apply_force(total_force, particle_2)
                    particle_1.run()
        for particle in particles_to_process:
            particle.update()
        output_queue.put(particles_to_process)

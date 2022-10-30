from collections.abc import Sequence
from math import sqrt


def dist(delta_x: float, delta_y: float) -> float:
    return sqrt(delta_x**2 + delta_y**2)


def compute_multi_dimensional_distance(position_1: Sequence[float], position_2: Sequence[float]) -> float:
    # todo : make work with unidimensional positions
    first = dist(position_1[0] - position_2[0], position_2[1] - position_1[1])
    for p1, p2 in zip(position_1[2:], position_2[2:]):
        first = dist(first, p1 - p2)
    return first

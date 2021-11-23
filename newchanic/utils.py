from itertools import cycle
from math import sqrt
from random import random
from typing import Union, TypeVar, List

Number = Union[int, float]


def dist(delta_x, delta_y):
    return sqrt(delta_x ** 2 + delta_y ** 2)


def compute_multi_dimensional_distance(position_1, position_2):
    first = dist(position_1[0] - position_2[0], position_2[1] - position_1[1])
    for p1, p2 in zip(position_1[2:], position_2[2:]):
        first = dist(first, p1 - p2)
    return first


T = TypeVar("T")


def split_into_lists(items: List[T], nbr: int) -> List[List[T]]:
    assert nbr > 0, "nbr must be > 0"
    item_nbr_by_list = len(items) // nbr
    lists = []
    for i in range(nbr):
        upper_bound = (i + 1) * item_nbr_by_list
        lower_bound = i * item_nbr_by_list
        lists.append(items[lower_bound:upper_bound])
    # noinspection PyUnboundLocalVariable
    if upper_bound != len(items):
        for item, list_ in zip(items[upper_bound:], cycle(lists)):
            list_.append(item)
    return lists


def random_between(param, param1):
    assert param < param1
    return random() * abs(param - param1) + param

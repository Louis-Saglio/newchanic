from newchanic.utils import distance_between


def test_distance_between1():
    assert distance_between((0, 0), (3, 4)) == 5

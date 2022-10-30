from newchanic.v2.engine import DelayedUpdateMixin, Particle

import pytest


def test_delayed_update_mixin():
    class A(DelayedUpdateMixin):
        pass

    a = A()
    a.test = 5
    with pytest.raises(AttributeError):
        a.test

    a.update()
    assert a.test == 5

    a.test = 8
    assert a.test == 5

    a.update()
    assert a.test == 8


def test_particle_delayed_update():
    p = Particle()
    p.MASS = 8
    assert p.MASS == 0
    p.update()
    assert p.MASS == 8

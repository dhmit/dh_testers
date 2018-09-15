# -*- coding: utf-8 -*-


def test_memory(test_function):
    try:
        import guppy
    except ImportError:
        raise ImportError("memoryUsage.py requires guppy")

    hp = guppy.hpy()
    hp.setrelheap()
    test_function()
    h = hp.heap()
    return h


if __name__ == '__main__':
    pass

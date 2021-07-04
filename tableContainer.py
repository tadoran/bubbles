from itertools import chain

import numpy as np


class NpTableContainer:

    def __init__(self,  height: int,width: int):
        self.height = height
        self.width = width
        self._container = np.empty((height, width), dtype=object)

    def __len__(self):
        return len(self._container)

    def __setitem__(self, key, value):
        self._container[key] = value

    def __getitem__(self, key):
        return self._container[key]

    def __call__(self):
        return self._container


class PythonTableContainer:

    def __init__(self, height: int, width: int):
        self.height = height
        self.width = width
        self._container = [None for _ in range(self.height * self.width)]

    def __call__(self, *args, **kwargs):
        pos, y, x = None, None, None

        if len(args) == 1:
            pos = args[0]
        elif "position" in kwargs:
            pos = kwargs["position"]

        elif len(args) == 2:
            y = args[0]
            x = args[1]

        elif "y" in kwargs and "x" in kwargs:
            y = kwargs["y"]
            x = kwargs["x"]

        else:
            return self._container

        # Define position in container if y and x were provided
        if not x is None and not y is None:
            assert 0 <= x < self.width
            assert 0 <= y < self.height
            pos = (y * self.height) + x

        if pos:
            if not 0 <= pos < len(self._container):
                raise ValueError(
                    f"Position {pos:1.} is out of boundaries 0-{len(self._container)} ({self.height}x{self.width})")
            else:
                return self._container[pos]

    def __setitem__(self, key, value):
        self._container[key] = value

    def __getitem__(self, key):
        return self._container[key]

    def __len__(self):
        return len(self._container)


class SlicesTableContainer(PythonTableContainer):
    def __call__(self, *args, **kwargs):
        pos, y, x = None, None, None

        if len(args) == 1:
            pos = args[0]
        elif "position" in kwargs:
            pos = kwargs["position"]

        elif len(args) == 2:
            y = args[0]
            x = args[1]

        elif "y" in kwargs and "x" in kwargs:
            y = kwargs["y"]
            x = kwargs["x"]

        else:
            raise ValueError("Neither position nor x,y were provided.")

        # Define position in container if y and x were provided
        if not x is None and not y is None:
            if isinstance(x, slice) or isinstance(y, slice):
                y_slice = list(range(self.height))[y]
                if isinstance(y_slice, int):
                    y_slice = [y_slice]
                x_slice = list(range(self.width))[x]
                if isinstance(x_slice, int):
                    x_slice = [x_slice]

                sliced_container = [[self._container[self.width * i:self.width * (i + 1)][x] for i in y_slice] for x in
                                    x_slice]
                return sliced_container

            else:
                assert 0 <= x < self.width
                assert 0 <= y < self.height
                pos = (y * self.height) + x

        if pos:
            if not 0 <= pos < len(self._container):
                raise ValueError(
                    f"Position {pos:1.} is out of boundaries 0-{len(self._container)} ({self.height}x{self.width})")
            else:
                return self._container[pos]

    def __setitem__(self, key, value):
        if isinstance(key, int):
            self._container[key] = value
        elif isinstance(key, tuple):
            keys = self(*key)
            for k in chain.from_iterable(keys):
                k = value

    def __getitem__(self, key):
        if isinstance(key, int):
            return self._container[key]
        elif isinstance(key, tuple):
            return self(*key)

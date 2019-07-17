
class Range:
    def __init__(self, min=None, max=None, range=None):
        self._min = min
        self._max = max
        if range:
            self._min = range[0]
            self._max = range[1]

    def get_min(self):
        return self._min

    def get_max(self):
        return self._max

    def get_array(self):
        return [self._min, self._max]

    def reset(self):
        self._min = None
        self._max = None

    def update(self, val):
        if self._min is None:
            self._min = val
        elif val < self._min:
            self._min = val
        if self._max is None:
            self._max = val
        elif val > self._max:
            self._max = val

    def merge(self, range):
        if range.is_valid():
            self.update(range._min)
            self.update(range._max)

    def is_valid(self):
        if self._min is None or self._max is None:
            return False
        else:
            return self._min < self._max

    def __repr__(self):
        return "[%r,%r]" % (self._min, self._max)


class RangeXY:
    def __init__(self, x_range=None, y_range=None):
        self._x = Range(range=x_range)
        self._y = Range(range=y_range)

    def reset(self):
        self._x.reset()
        self._y.reset()

    def update(self, x, y):
        self._x.update(x)
        self._y.update(y)

    def merge(self, range_xy):
        self._x.merge(range_xy._x)
        self._y.merge(range_xy._y)

    def get_x_range(self):
        return self._x

    def get_y_range(self):
        return self._y

    def is_valid(self):
        return self._x.is_valid() and self._y.is_valid()

    def __repr__(self):
        return "x=%r,y=%r" % (self._x, self._y)


class RangeXYZ(RangeXY):
    def __init__(self, x_range=None, y_range=None, z_range=None):
        super().__init__(x_range, y_range)
        self._z = Range(z_range)

    def reset(self):
        super().reset()
        self._z.reset()

    def update(self, x, y, z):
        super().update(x, y)
        self._z.update(z)

    def merge(self, range_xyz):
        super().merge(range_xyz)
        self._z.merge(range_xyz._z)

    def get_z_range(self):
        return self._z

    def is_valid(self):
        return super().is_valid() and self._z.is_valid()

    def __repr__(self):
        return "%r,z=%r" % (super().__repr__(), self._z)

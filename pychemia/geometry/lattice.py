import numpy as _np
from math import pi
import math
import itertools
from pychemia.utils.mathematics import length_vectors, angle_vectors, wrap2_pmhalf

__author__ = 'Guillermo Avendano-Franco'


class Lattice():
    """
    Routines to create and manipulate the lattice
    The lattice is sufficiently general to account for periodicity in 1, 2 or 3 directions.
    However many routines are only implemented for 3 directions
    The lattice contains 1, 2 or 3 vectors
    """

    def __init__(self, cell, periodicity=True):
        """
        Defines an object lattice that could live
        in arbitrary dimensions
        """
        if isinstance(periodicity, bool):
            self._periodicity = 3*[periodicity]
        elif isinstance(periodicity, list):
            self._periodicity = list(periodicity)
        else:
            raise ValueError("periodicity must be a boolean or list")

        self._dims = sum(self._periodicity)
        assert(_np.prod(_np.array(cell).shape) == self.periodic_dimensions**2)
        self._cell = _np.array(cell).reshape((self.periodic_dimensions, self.periodic_dimensions))
        self._lengths = length_vectors(self._cell)
        self._angles = angle_vectors(self._cell)
        self._metric = None
        self._inverse = None

    @staticmethod
    def parameters2cell(a, b, c, alpha, beta, gamma):
        pass

    @property
    def cell(self):
        """
        Return the cell as a numpy array

        :return:
        """
        return self._cell

    @property
    def periodic_dimensions(self):
        """
        Return the number of periodic dimensions

        :return: int
        """
        return self._dims

    @property
    def volume(self):
        """
        Computes the volume of the cell (3D),
        area (2D) or generalized volume for
        N dimensions

        :rtype : float
        """
        return abs(_np.linalg.det(self.cell))

    @property
    def metric(self):
        if self._metric is None:
            self._metric = _np.dot(self.cell, self.cell.T)
        return self._metric

    @property
    def inverse(self):
        if self._inverse is None:
            self._inverse = _np.linalg.inv(self.cell)
        return self._inverse

    def reciprocal(self):
        """
        Return the reciprocal cell

        :rtype : Lattice
        :return:
        """
        return self.__class__(_np.linalg.inv(self.cell.T))

    def copy(self):
        """
        Return a copy of the object
        """
        return self.__class__(self._cell, self._periodicity)

    def get_path(self):

        assert(self.periodic_dimensions == 3)

        zero3 = _np.zeros(3)
        x = self.cell[0, :]
        y = self.cell[1, :]
        z = self.cell[2, :]

        frame = _np.array([zero3, x, x+y, y, zero3, z, x+z, x+y+z, y+z, z])

        line1 = _np.array([x, x+z])
        line2 = _np.array([x+y, x+y+z])
        line3 = _np.array([y, y+z])

        return frame, line1, line2, line3

    @property
    def alpha(self):
        return self._angles[(1, 2)]

    @property
    def beta(self):
        return self._angles[(0, 2)]

    @property
    def gamma(self):
        return self._angles[(0, 1)]

    @property
    def angles(self):
        return self.alpha, self.beta, self.gamma

    @property
    def a(self):
        return self._lengths[0]

    @property
    def b(self):
        return self._lengths[1]

    @property
    def c(self):
        return self._lengths[2]

    @property
    def lengths(self):
        return self._lengths

    def cartesian2reduced(self, x):
        return _np.dot(x, self.inverse)

    def reduced2cartesian(self, x):
        return _np.dot(x, self.cell)

    def get_wigner_seitz(self):

        from pyhull.voronoi import VoronoiTess
        import itertools

        points = []
        for i, j, k in itertools.product((-1, 0, 1), repeat=3):
            points.append(i * self.cell[0] + j * self.cell[1] + k * self.cell[2])
        tess = VoronoiTess(points)
        ret = []
        for r in tess.ridges:
            if r[0] == 13 or r[1] == 13:
                ret.append([tess.vertices[i] for i in tess.ridges[r]])
        return ret

    def get_brillouin(self):
        return self.reciprocal().get_wigner_seitz()

    def get_wigner_seitz_container(self):
        """
        Compute the corners of the box that contains the Wigner-Seitz cell

        :return: dict : dictionary with values numpy arrays
        """
        ret = {}
        for i in itertools.product((-1, 1), repeat=3):
            ret[i] = _np.dot(self.reciprocal().metric, i*_np.diagonal(self.metric))
        return ret

    def distance2(self, x1, x2, option='reduced'):

        # Compute the vector from x1 to x2
        dv = _np.array(x2)-_np.array(x1)

        # If we are not in reduced coordinates,
        # Convert into them
        if option != 'reduced':
            dred = self.cartesian2reduced(dv)
        else:
            dred = dv

        dwrap = wrap2_pmhalf(dred)

        limits = _np.zeros(3)
        corners = self.get_wigner_seitz_container()
        #for key, value in corners.iteritems():
        #    print key, value
        limits[0] = int(math.ceil(max(1e-14+abs(_np.array([corners[x][0] for x in corners])))))
        limits[1] = int(math.ceil(max(1e-14+abs(_np.array([corners[x][1] for x in corners])))))
        limits[2] = int(math.ceil(max(1e-14+abs(_np.array([corners[x][2] for x in corners])))))
        #print limits
        ret = {}
        for i0 in _np.arange(-limits[0], limits[0]+1):
            for i1 in _np.arange(-limits[1], limits[1]+1):
                for i2 in _np.arange(-limits[2], limits[2]+1):
                    dtot = dwrap+_np.array([i0, i1, i2])
                    norm2 = _np.dot(_np.dot(dtot, self.metric), dtot)
                    ret[(i0, i1, i2)] = {'distance': math.sqrt(norm2), 'image': dtot}
        return ret

    def plot(self, points=None):
        from mayavi import mlab

        frame, line1, line2, line3 = self.get_path()
        mlab.plot3d(frame[:, 0], frame[:, 1], frame[:, 2], tube_radius=.05, color=(1, 1, 1))
        mlab.plot3d(line1[:, 0], line1[:, 1], line1[:, 2], tube_radius=.05, color=(1, 1, 1))
        mlab.plot3d(line2[:, 0], line2[:, 1], line2[:, 2], tube_radius=.05, color=(1, 1, 1))
        mlab.plot3d(line3[:, 0], line3[:, 1], line3[:, 2], tube_radius=.05, color=(1, 1, 1))

        if points is not None:
            ip = _np.array(points)
            mlab.points3d(ip[:, 0], ip[:, 1], ip[:, 2], 0.1*_np.ones(len(ip)), scale_factor=1)

        return mlab.pipeline

    def plot_wigner_seitz(self, scale=1):
        import itertools
        from tvtk.api import tvtk

        ws = _np.array(self.get_wigner_seitz())
        points = scale * ws.flatten().reshape(-1, 3)
        index = 0
        triangles = index+_np.array(list(itertools.combinations(range(len(ws[0])), 3)))
        scalars = _np.random.random()*_np.ones(len(ws[0]))
        for i in ws[1:]:
            index += len(i)
            triangles = _np.concatenate((triangles, index+_np.array(list(itertools.combinations(range(len(i)), 3)))))
            scalars = _np.concatenate((scalars, _np.random.random()*_np.ones(len(i))))

        # The TVTK dataset.
        mesh = tvtk.PolyData(points=points, polys=triangles)
        mesh.point_data.scalars = scalars
        mesh.point_data.scalars.name = 'scalars'

        pipeline = self.plot()
        pipeline.surface(mesh)
        return pipeline
import functools
import numpy as np
import unittest

from numba import config, cuda, types
from numba.tests.support import TestCase
from numba.tests.test_ufuncs import BasicUFuncTest


def _make_ufunc_usecase(ufunc):
    ldict = {}
    arg_str = ','.join(['a{0}'.format(i) for i in range(ufunc.nargs)])
    func_str = f'def fn({arg_str}):\n    np.{ufunc.__name__}({arg_str})'
    exec(func_str, globals(), ldict)
    fn = ldict['fn']
    fn.__name__ = '{0}_usecase'.format(ufunc.__name__)
    return fn


# This test would also be a CUDATestCase, but to avoid a confusing and
# potentially dangerous inheritance diamond with setUp methods that modify
# global state, we implement the necessary parts of CUDATestCase within this
# class instead. These are:
#
# - Disable parallel testing with _numba_parallel_test_.
# - Disabling CUDA performance warnings for the duration of tests.
class TestUFuncs(BasicUFuncTest, TestCase):
    _numba_parallel_test_ = False

    def setUp(self):
        BasicUFuncTest.setUp(self)

        # The basic ufunc test does not set up complex inputs, so we'll add
        # some here for testing with CUDA.
        self.inputs.extend([
            (np.complex64(-0.5 - 0.5j), types.complex64),
            (np.complex64(0.0), types.complex64),
            (np.complex64(0.5 + 0.5j), types.complex64),

            (np.complex128(-0.5 - 0.5j), types.complex128),
            (np.complex128(0.0), types.complex128),
            (np.complex128(0.5 + 0.5j), types.complex128),

            (np.array([-0.5 - 0.5j, 0.0, 0.5 + 0.5j], dtype='c8'),
             types.Array(types.complex64, 1, 'C')),
            (np.array([-0.5 - 0.5j, 0.0, 0.5 + 0.5j], dtype='c16'),
             types.Array(types.complex128, 1, 'C')),
        ])

        # Test with multiple dimensions
        self.inputs.extend([
            # Basic 2D and 3D arrays
            (np.linspace(0, 1).reshape((5, -1)),
             types.Array(types.float64, 2, 'C')),
            (np.linspace(0, 1).reshape((2, 5, -1)),
             types.Array(types.float64, 3, 'C')),
            # Complex data (i.e. interleaved)
            (np.linspace(0, 1 + 1j).reshape(5, -1),
             types.Array(types.complex128, 2, 'C')),
            # F-ordered
            (np.asfortranarray(np.linspace(0, 1).reshape((5, -1))),
             types.Array(types.float64, 2, 'F')),
        ])

        self._low_occupancy_warnings = config.CUDA_LOW_OCCUPANCY_WARNINGS
        self._warn_on_implicit_copy = config.CUDA_WARN_ON_IMPLICIT_COPY

        # Disable warnings about low gpu utilization in the test suite
        config.CUDA_LOW_OCCUPANCY_WARNINGS = 0
        # Disable warnings about host arrays in the test suite
        config.CUDA_WARN_ON_IMPLICIT_COPY = 0

    def tearDown(self):
        # Restore original warning settings
        config.CUDA_LOW_OCCUPANCY_WARNINGS = self._low_occupancy_warnings
        config.CUDA_WARN_ON_IMPLICIT_COPY = self._warn_on_implicit_copy

    def _make_ufunc_usecase(self, ufunc):
        return _make_ufunc_usecase(ufunc)

    @functools.lru_cache(maxsize=None)
    def _compile(self, pyfunc, args):
        # We return an already-configured kernel so that basic_ufunc_test can
        # call it just like it does for a CPU function
        return cuda.jit(args)(pyfunc)[1, 1]

    ############################################################################
    # Trigonometric Functions

    def test_sin_ufunc(self):
        self.basic_ufunc_test(np.sin, kinds='cf')

    def test_cos_ufunc(self):
        self.basic_ufunc_test(np.cos, kinds='cf')

    def test_tan_ufunc(self):
        self.basic_ufunc_test(np.tan, kinds='cf')

    def test_arcsin_ufunc(self):
        self.basic_ufunc_test(np.arcsin, kinds='cf')

    def test_arccos_ufunc(self):
        self.basic_ufunc_test(np.arccos, kinds='cf')

    def test_arctan_ufunc(self):
        self.basic_ufunc_test(np.arctan, kinds='cf')

    def test_arctan2_ufunc(self):
        self.basic_ufunc_test(np.arctan2, kinds='f')

    def test_hypot_ufunc(self):
        self.basic_ufunc_test(np.hypot, kinds='f')

    def test_sinh_ufunc(self):
        self.basic_ufunc_test(np.sinh, kinds='cf')

    def test_cosh_ufunc(self):
        self.basic_ufunc_test(np.cosh, kinds='cf')

    def test_tanh_ufunc(self):
        self.basic_ufunc_test(np.tanh, kinds='cf')

    def test_arcsinh_ufunc(self):
        self.basic_ufunc_test(np.arcsinh, kinds='cf')

    def test_arccosh_ufunc(self):
        self.basic_ufunc_test(np.arccosh, kinds='cf')

    def test_arctanh_ufunc(self):
        # arctanh is only valid is only finite in the range ]-1, 1[
        # This means that for any of the integer types it will produce
        # conversion from infinity/-infinity to integer. That's undefined
        # behavior in C, so the results may vary from implementation to
        # implementation. This means that the result from the compiler
        # used to compile NumPy may differ from the result generated by
        # llvm. Skipping the integer types in this test avoids failed
        # tests because of this.
        to_skip = [types.Array(types.uint32, 1, 'C'), types.uint32,
                   types.Array(types.int32, 1, 'C'), types.int32,
                   types.Array(types.uint64, 1, 'C'), types.uint64,
                   types.Array(types.int64, 1, 'C'), types.int64]

        self.basic_ufunc_test(np.arctanh, skip_inputs=to_skip, kinds='cf')

    def test_deg2rad_ufunc(self):
        self.basic_ufunc_test(np.deg2rad, kinds='f')

    def test_rad2deg_ufunc(self):
        self.basic_ufunc_test(np.rad2deg, kinds='f')

    def test_degrees_ufunc(self):
        self.basic_ufunc_test(np.degrees, kinds='f')

    def test_radians_ufunc(self):
        self.basic_ufunc_test(np.radians, kinds='f')


if __name__ == '__main__':
    unittest.main()

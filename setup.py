# Some of the setup.py code is inspired or copied from SQLAlchemy

# SQLAlchemy was created by Michael Bayer.

# Major contributing authors include:

# - Michael Bayer <mike_mp@zzzcomputing.com>
# - Jason Kirtland <jek@discorporate.us>
# - Gaetan de Menten <gdementen@gmail.com>
# - Diana Clarke <diana.joan.clarke@gmail.com>
# - Michael Trier <mtrier@gmail.com>
# - Philip Jenvey <pjenvey@underboss.org>
# - Ants Aasma <ants.aasma@gmail.com>
# - Paul Johnston <paj@pajhome.org.uk>
# - Jonathan Ellis <jbellis@gmail.com>

# Copyright 2005-2019 SQLAlchemy authors and contributors (see above)

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to
# deal in the Software without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
# sell copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.

from setuptools import setup, Extension, find_packages
from distutils.errors import (CCompilerError, DistutilsExecError,
                              DistutilsPlatformError)
from setuptools import Distribution as _Distribution
from setuptools.command.build_ext import build_ext
import sys
import os
import subprocess
import platform

# ==============================================================================


class get_pybind_include(object):
    '''Helper class to determine the pybind11 include path

    The purpose of this class is to postpone importing pybind11
    until it is actually installed, so that the ``get_include()``
    method can be invoked. '''
    def __init__(self, user=False):
        self.user = user

    def __str__(self):
        import pybind11
        return pybind11.get_include(self.user)


def status_msgs(*msgs):
    print('*' * 75)
    for msg in msgs:
        print(msg)
    print('*' * 75)


# ==============================================================================

cpython = platform.python_implementation() == 'CPython'

ext_modules = [
    Extension(
        'projectq.backends._sim._cppsim',
        ['projectq/backends/_sim/_cppsim.cpp'],
        include_dirs=[
            # Path to pybind11 headers
            get_pybind_include(),
            get_pybind_include(user=True)
        ],
        language='c++'),
]

ext_errors = (CCompilerError, DistutilsExecError, DistutilsPlatformError)
if sys.platform == 'win32':
    # 2.6's distutils.msvc9compiler can raise an IOError when failing to
    # find the compiler
    ext_errors += (IOError, )


class BuildFailed(Exception):
    def __init__(self):
        self.cause = sys.exc_info()[1]  # work around py 2/3 different syntax


# This reads the __version__ variable from projectq/_version.py
exec(open('projectq/_version.py').read())

# Readme file as long_description:
long_description = open('README.rst').read()

# Read in requirements.txt
with open('requirements.txt', 'r') as f_requirements:
    requirements = f_requirements.readlines()
requirements = [r.strip() for r in requirements]


def compiler_test(compiler,
                  flagname=None,
                  link=False,
                  include='',
                  body='',
                  postargs=None):
    '''
    Return a boolean indicating whether a flag name is supported on the
    specified compiler.
    '''
    import tempfile
    f = tempfile.NamedTemporaryFile('w', suffix='.cpp', delete=False)
    f.write('{}\nint main (int argc, char **argv) {{ {} return 0; }}'.format(
        include, body))
    f.close()
    ret = True

    if postargs is None:
        postargs = [flagname] if flagname is not None else None
    elif flagname is not None:
        postargs.append(flagname)

    try:
        exec_name = os.path.join(tempfile.mkdtemp(), 'test')
        obj_file = compiler.compile([f.name], extra_postargs=postargs)
        if link:
            compiler.link_executable(obj_file,
                                     exec_name,
                                     extra_postargs=postargs)
    except:
        ret = False
    os.unlink(f.name)
    return ret


class BuildExt(build_ext):
    '''A custom build extension for adding compiler-specific options.'''
    c_opts = {
        'msvc': ['/EHsc'],
        'unix': [],
    }

    def run(self):
        try:
            build_ext.run(self)
        except DistutilsPlatformError:
            raise BuildFailed()

    def build_extensions(self):
        self._configure_compiler()
        for ext in self.extensions:
            ext.extra_compile_args = self.opts
            ext.extra_link_args = self.link_opts
        try:
            build_ext.build_extensions(self)
        except ext_errors:
            raise BuildFailed()
        except ValueError:
            # this can happen on Windows 64 bit, see Python issue 7511
            if "'path'" in str(sys.exc_info()[1]):  # works with both py 2/3
                raise BuildFailed()
            raise

    def _configure_compiler(self):
        if sys.platform == 'darwin':
            self.c_opts['unix'] += ['-mmacosx-version-min=10.7']
            if compiler_test(self.compiler, '-stdlib=libc++'):
                self.c_opts['unix'] += ['-stdlib=libc++']

        ct = self.compiler.compiler_type
        self.opts = self.c_opts.get(ct, [])
        self.link_opts = []

        if not compiler_test(self.compiler):
            status_msgs('ERROR: something is wrong with your C++ compiler.\n'
                        'Failed to compile a simple test program!')
            raise BuildFailed()

        # ------------------------------
        # Test for OpenMP

        kwargs = {
            'link': True,
            'include': '#include <omp.h>',
            'body': 'int a = omp_get_num_threads(); ++a;'
        }
        openmp = ''
        if compiler_test(self.compiler, '-fopenmp', **kwargs):
            openmp = '-fopenmp'
        elif compiler_test(self.compiler, '-qopenmp', **kwargs):
            openmp = '-qopenmp'
        elif (sys.platform == 'darwin'
              and compiler_test(self.compiler, '-fopenmp')):
            try:
                llvm_root = subprocess.check_output(
                    ['brew', '--prefix', 'llvm']).decode('utf-8')[:-1]
                compiler_root = subprocess.check_output(
                    ['which', self.compiler.compiler[0]]).decode('utf-8')[:-1]

                # Only add the flag if the compiler we are using is the one
                # from HomeBrew
                if llvm_root in compiler_root:
                    l_arg = '-L{}/lib'.format(llvm_root)
                    if compiler_test(self.compiler,
                                     '-fopenmp',
                                     postargs=[l_arg],
                                     **kwargs):
                        self.link_opts.append(l_arg)
                        openmp = '-fopenmp'
            except subprocess.CalledProcessError:
                pass

        if ct == 'msvc':
            openmp = ''  # supports only OpenMP 2.0

        self.opts.append(openmp)

        # ------------------------------
        # Test for compiler intrinsics

        if compiler_test(self.compiler,
                         flagname='-march=native',
                         link=True,
                         include='#include <immintrin.h>',
                         body='__m256d neg = _mm256_set1_pd(1.0); (void)neg;'):
            self.opts.append('-DINTRIN')
            if ct == 'msvc':
                self.opts.append('/arch:AVX')
            else:
                self.opts.append('-march=native')
                self.opts.append('-ffast-math')

        # ------------------------------
        # Other compiler tests

        if ct == 'unix':
            # Avoiding C++17 for now because of compilation issues on MacOSX
            if compiler_test(self.compiler, '-std=c++14'):
                self.opts.append('-std=c++14')
            elif compiler_test(self.compiler, '-std=c++11'):
                self.opts.append('-std=c++11')
            else:
                status_msgs('ERROR: compiler needs to have at least C++11 support!')
                raise BuildFailed()

            self.opts.append("-DVERSION_INFO='{}'".format(
                             self.distribution.get_version()))
            if compiler_test(self.compiler, '-fvisibility=hidden'):
                self.opts.append('-fvisibility=hidden')
        elif ct == 'msvc':
            self.opts.append("/DVERSION_INFO=\\'%s\\'".format(
                             self.distribution.get_version()))

        self.link_opts.append(openmp)


class Distribution(_Distribution):
    def has_ext_modules(self):
        # We want to always claim that we have ext_modules. This will be fine
        # if we don't actually have them (such as on PyPy) because nothing
        # will get built, however we don't want to provide an overally broad
        # Wheel package when building a wheel without C support. This will
        # ensure that Wheel knows to treat us as if the build output is
        # platform specific.
        return True


def run_setup(with_cext):
    kwargs = {}
    if with_cext:
        kwargs['ext_modules'] = ext_modules
    else:
        kwargs['ext_modules'] = []

    setup(name='projectq',
          version=__version__,
          author='ProjectQ',
          author_email='info@projectq.ch',
          url='http://www.projectq.ch',
          project_urls={
              'Documentation': 'https://projectq.readthedocs.io/en/latest/',
              'Issue Tracker':
              'https://github.com/ProjectQ-Framework/ProjectQ/',
          },
          description=(
              'ProjectQ - '
              'An open source software framework for quantum computing'),
          long_description=long_description,
          install_requires=requirements,
          cmdclass={'build_ext': BuildExt},
          zip_safe=False,
          license='Apache 2',
          packages=find_packages(),
          distclass=Distribution,
          **kwargs)


# ==============================================================================

if not cpython:
    run_setup(False)
    status_msgs(
        'WARNING: C/C++ extensions are not supported on ' +
        'some features are disabled (e.g. C++ simulator).',
        'Plain-Python build succeeded.',
    )
elif os.environ.get('DISABLE_PROJECTQ_CEXT'):
    run_setup(False)
    status_msgs(
        'DISABLE_PROJECTQ_CEXT is set; ' +
        'not attempting to build C/C++ extensions.',
        'Plain-Python build succeeded.',
    )

else:
    try:
        run_setup(True)
    except BuildFailed as exc:
        status_msgs(
            exc.cause,
            'WARNING: Some C/C++ extensions could not be compiled, ' +
            'some features are disabled (e.g. C++ simulator).',
            'Failure information, if any, is above.',
            'Retrying the build without the C/C++ extensions now.',
        )

        run_setup(False)

        status_msgs(
            'WARNING: Some C/C++ extensions could not be compiled, ' +
            'some features are disabled (e.g. C++ simulator).',
            'Plain-Python build succeeded.',
        )

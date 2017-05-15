from setuptools import setup, Extension, find_packages, Feature
from setuptools.command.build_ext import build_ext
import sys
import os
import setuptools


# This reads the __version__ variable from projectq/_version.py
exec(open('projectq/_version.py').read())

# Readme file as long_description:
long_description = open('README.rst').read()

# Read in requirements.txt
with open ('requirements.txt', 'r') as f_requirements:
    requirements = f_requirements.readlines()
requirements = [r.strip() for r in requirements]


class get_pybind_include(object):
    """Helper class to determine the pybind11 include path

    The purpose of this class is to postpone importing pybind11
    until it is actually installed, so that the ``get_include()``
    method can be invoked. """

    def __init__(self, user=False):
        self.user = user

    def __str__(self):
        import pybind11
        return pybind11.get_include(self.user)


cppsim = Feature(
    'C++ Simulator',
    standard=True,
    ext_modules=[
        Extension(
            'projectq.backends._sim._cppsim',
            ['projectq/backends/_sim/_cppsim.cpp'],
            include_dirs=[
                # Path to pybind11 headers
                get_pybind_include(),
                get_pybind_include(user=True)
            ],
            language='c++'
        ),
    ],
)


def has_flag(compiler, flagname=None):
    """
    Return a boolean indicating whether a flag name is supported on the
    specified compiler.
    """
    import tempfile
    f = tempfile.NamedTemporaryFile('w', suffix='.cpp', delete=False)
    f.write('int main (int argc, char **argv) { return 0; }')
    f.close()
    ret = True
    try:
        if flagname is None:
            compiler.compile([f.name])
        else:
            compiler.compile([f.name], extra_postargs=[flagname])
    except:
        ret = False
    os.unlink(f.name)
    return ret


def knows_intrinsics(compiler):
    """
    Return a boolean indicating whether the compiler can handle intrinsics.
    """
    import tempfile
    f = tempfile.NamedTemporaryFile('w', suffix='.cpp', delete=False)
    f.write('#include <immintrin.h>\nint main (int argc, char **argv) '
            '{ __m256d neg = _mm256_set1_pd(1.0); }')
    f.close()
    ret = True
    try:
        compiler.compile([f.name], extra_postargs=['-march=native'])
    except setuptools.distutils.errors.CompileError:
        ret = False
    os.unlink(f.name)
    return ret


class BuildExt(build_ext):
    """A custom build extension for adding compiler-specific options."""
    c_opts = {
        'msvc': ['/EHsc'],
        'unix': [],
    }

    def build_extensions(self):
        if sys.platform == 'darwin':
            self.c_opts['unix'] += ['-mmacosx-version-min=10.7']
            if has_flag(self.compiler, '-stdlib=libc++'):
                self.c_opts['unix'] += ['-stdlib=libc++']

        ct = self.compiler.compiler_type
        opts = self.c_opts.get(ct, [])

        if not has_flag(self.compiler):
            self.warning("Something is wrong with your C++ compiler.\n"
                         "Failed to compile a simple test program!\n")
            return

        openmp = ''
        if has_flag(self.compiler, '-fopenmp'):
            openmp = '-fopenmp'
        elif has_flag(self.compiler, '-openmp'):
            openmp = '-openmp'
        if ct == 'msvc':
            openmp = ''  # supports only OpenMP 2.0

        if knows_intrinsics(self.compiler):
            opts.append('-DINTRIN')
            if ct == 'msvc':
                opts.append('/arch:AVX')
            else:
                opts.append('-march=native')

        opts.append(openmp)
        if ct == 'unix':
            if not has_flag(self.compiler, '-std=c++11'):
                self.warning("Compiler needs to have C++11 support!")
                return

            opts.append('-DVERSION_INFO="%s"'
                        % self.distribution.get_version())
            opts.append('-std=c++11')
            if has_flag(self.compiler, '-fvisibility=hidden'):
                opts.append('-fvisibility=hidden')
        elif ct == 'msvc':
            opts.append('/DVERSION_INFO=\\"%s\\"'
                        % self.distribution.get_version())
        for ext in self.extensions:
            ext.extra_compile_args = opts
            ext.extra_link_args = [openmp]
        try:
            build_ext.build_extensions(self)
        except setuptools.distutils.errors.CompileError:
            self.warning("")

    def warning(self, warning_text):
        raise Exception(warning_text + "\nCould not install the C++-Simulator."
                        "\nProjectQ will default to the (slow) Python "
                        "simulator.\nUse --without-cppsimulator to skip "
                        "building the (faster) C++ version of the simulator.")


setup(
    name='projectq',
    version=__version__,
    author='ProjectQ',
    author_email='info@projectq.ch',
    url='http://www.projectq.ch',
    description=('ProjectQ - '
                 'An open source software framework for quantum computing'),
    long_description=long_description,
    features={'cppsimulator': cppsim},
    install_requires=requirements,
    cmdclass={'build_ext': BuildExt},
    zip_safe=False,
    license='Apache 2',
    packages=find_packages()
)

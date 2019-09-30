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
with open('requirements.txt', 'r') as f_requirements:
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
            language='c++'),
    ],
)


def compiler_test(compiler,
                  flagname=None,
                  link=False,
                  include="",
                  body="",
                  postargs=None):
    """
    Return a boolean indicating whether a flag name is supported on the
    specified compiler.
    """
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
    """A custom build extension for adding compiler-specific options."""
    c_opts = {
        'msvc': ['/EHsc'],
        'unix': [],
    }

    def build_extensions(self):
        if sys.platform == 'darwin':
            self.c_opts['unix'] += ['-mmacosx-version-min=10.7']
            if compiler_test(self.compiler, '-stdlib=libc++'):
                self.c_opts['unix'] += ['-stdlib=libc++']

        ct = self.compiler.compiler_type
        opts = self.c_opts.get(ct, [])
        link_opts = []

        if not compiler_test(self.compiler):
            self.warning("Something is wrong with your C++ compiler.\n"
                         "Failed to compile a simple test program!\n")
            return

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
                    link_opts.append(l_arg)
                    openmp = '-fopenmp'
            except subprocess.CalledProcessError:
                pass

        if ct == 'msvc':
            openmp = ''  # supports only OpenMP 2.0

        opts.append(openmp)

        # ------------------------------
        # Test for compiler intrinsics

        if compiler_test(self.compiler,
                         flagname='-march=native',
                         link=True,
                         include='#include <immintrin.h>',
                         body='__m256d neg = _mm256_set1_pd(1.0); (void)neg;'):
            opts.append('-DINTRIN')
            if ct == 'msvc':
                opts.append('/arch:AVX')
            else:
                opts.append('-march=native')
                opts.append('-ffast-math')

        # ------------------------------
        # Other compiler tests

        if ct == 'unix':
            # Avoiding C++17 for now because of compilation issues on MacOSX
            if compiler_test(self.compiler, '-std=c++14'):
                opts.append('-std=c++14')
            elif compiler_test(self.compiler, '-std=c++11'):
            opts.append('-std=c++11')
            else:
                self.warning("Compiler needs to have C++11 support!")
                return

            opts.append('-DVERSION_INFO="%s"' %
                        self.distribution.get_version())
            if compiler_test(self.compiler, '-fvisibility=hidden'):
                opts.append('-fvisibility=hidden')
        elif ct == 'msvc':
            opts.append('/DVERSION_INFO=\\"%s\\"' %
                        self.distribution.get_version())

        link_opts.append(openmp)
        for ext in self.extensions:
            ext.extra_compile_args = opts
            ext.extra_link_args = link_opts
        try:
            build_ext.build_extensions(self)
        except setuptools.distutils.errors.CompileError:
            self.warning("")

    def warning(self, warning_text):
        raise Exception(warning_text + "\nCould not install the C++-Simulator."
                        "\nProjectQ will default to the (slow) Python "
                        "simulator.\nUse --without-cppsimulator to skip "
                        "building the (faster) C++ version of the simulator.")


setup(name='projectq',
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
      packages=find_packages())

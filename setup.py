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
# - Damien Nguyen <damien1@huawei.com> (ProjectQ)

# Copyright 2005-2020 SQLAlchemy and ProjectQ authors and contributors (see above)

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

"""Setup.py file."""

import distutils.log
import os
import platform
import subprocess
import sys
import tempfile
from distutils.cmd import Command
from distutils.errors import (
    CCompilerError,
    CompileError,
    DistutilsExecError,
    DistutilsPlatformError,
    LinkError,
)
from distutils.spawn import find_executable, spawn
from operator import itemgetter
from pathlib import Path

from setuptools import Distribution as _Distribution
from setuptools import Extension, setup
from setuptools.command.build_ext import build_ext

try:
    import setuptools_scm  # noqa: F401  # pylint: disable=unused-import

    _HAS_SETUPTOOLS_SCM = True
except ImportError:
    _HAS_SETUPTOOLS_SCM = False

try:
    import tomllib

    def parse_toml(filename):
        """Parse a TOML file."""
        with open(str(filename), 'rb') as toml_file:
            return tomllib.load(toml_file)

except ImportError:
    try:
        import toml

        def parse_toml(filename):
            """Parse a TOML file."""
            return toml.load(filename)

    except ImportError:

        def _find_toml_section_end(lines, start):
            """Find the index of the start of the next section."""
            return (
                next(filter(itemgetter(1), enumerate(line.startswith('[') for line in lines[start + 1 :])))[0]
                + start
                + 1
            )

        def _parse_list(lines):
            """Parse a TOML list into a Python list."""
            # NB: This function expects the TOML list to be formatted like so (ignoring leading and trailing spaces):
            #     name = [
            #          '...',
            #     ]
            #     Any other format is not supported.
            name = None
            elements = []

            for idx, line in enumerate(lines):
                if name is None and not line.startswith("'"):
                    name = line.split('=')[0].strip()
                    continue
                if line.startswith("]"):
                    return (name, elements, idx + 1)
                elements.append(line.rstrip(',').strip("'").strip('"'))

            raise RuntimeError(f'Failed to locate closing "]" for {name}')

        def parse_toml(filename):
            """Very simple parser routine for pyproject.toml."""
            result = {'project': {'optional-dependencies': {}}}
            with open(filename) as toml_file:
                lines = [line.strip() for line in toml_file.readlines()]
            lines = [line for line in lines if line and not line.startswith('#')]

            start = lines.index('[project]')
            project_data = lines[start : _find_toml_section_end(lines, start)]

            start = lines.index('[project.optional-dependencies]')
            optional_dependencies = lines[start + 1 : _find_toml_section_end(lines, start)]

            idx = 0
            N = len(project_data)
            while idx < N:
                line = project_data[idx]
                shift = 1
                if line.startswith('name'):
                    result['project']['name'] = line.split('=')[1].strip().strip("'")
                elif line.startswith('dependencies'):
                    (name, pkgs, shift) = _parse_list(project_data[idx:])
                    result['project'][name] = pkgs
                idx += shift

            idx = 0
            N = len(optional_dependencies)
            while idx < N:
                (opt_name, opt_pkgs, shift) = _parse_list(optional_dependencies[idx:])
                result['project']['optional-dependencies'][opt_name] = opt_pkgs
                idx += shift

            return result


# ==============================================================================
# Helper functions and classes


class Pybind11Include:  # pylint: disable=too-few-public-methods
    """
    Helper class to determine the pybind11 include path.

    The purpose of this class is to postpone importing pybind11 until it is actually installed, so that the
    ``get_include()`` method can be invoked.
    """

    def __init__(self, user=False):
        """Initialize a Pybind11Include object."""
        self.user = user

    def __str__(self):
        """Conversion to string."""
        import pybind11  # pylint: disable=import-outside-toplevel

        return pybind11.get_include(self.user)


def important_msgs(*msgs):
    """Print an important message."""
    print('*' * 75)
    for msg in msgs:
        print(msg)
    print('*' * 75)


def status_msgs(*msgs):
    """Print a status message."""
    print('-' * 75)
    for msg in msgs:
        print('# INFO: ', msg)
    print('-' * 75)


def compiler_test(
    compiler,
    flagname=None,
    link_executable=False,
    link_shared_lib=False,
    include='',
    body='',
    compile_postargs=None,
    link_postargs=None,
):  # pylint: disable=too-many-arguments,too-many-branches
    """Return a boolean indicating whether a flag name is supported on the specified compiler."""
    fname = None
    with tempfile.NamedTemporaryFile('w', suffix='.cpp', delete=False) as temp:
        temp.write(f'{include}\nint main (int argc, char **argv) {{ {body} return 0; }}')
        fname = temp.name

    if compile_postargs is None:
        compile_postargs = [flagname] if flagname is not None else None
    elif flagname is not None:
        compile_postargs.append(flagname)

    try:
        if compiler.compiler_type == 'msvc':
            olderr = os.dup(sys.stderr.fileno())
            err = open('err.txt', 'w')  # pylint: disable=consider-using-with
            os.dup2(err.fileno(), sys.stderr.fileno())

        obj_file = compiler.compile([fname], extra_postargs=compile_postargs)
        if not os.path.exists(obj_file[0]):
            raise RuntimeError('')
        if link_executable:
            compiler.link_executable(obj_file, os.path.join(tempfile.mkdtemp(), 'test'), extra_postargs=link_postargs)
        elif link_shared_lib:
            if sys.platform == 'win32':
                lib_name = os.path.join(tempfile.mkdtemp(), 'test.dll')
            else:
                lib_name = os.path.join(tempfile.mkdtemp(), 'test.so')
            compiler.link_shared_lib(obj_file, lib_name, extra_postargs=link_postargs)

        if compiler.compiler_type == 'msvc':
            err.close()
            os.dup2(olderr, sys.stderr.fileno())
            with open('err.txt') as err_file:
                if err_file.readlines():
                    raise RuntimeError('')
    except (CompileError, LinkError, RuntimeError):
        return False
    else:
        return True
    finally:
        os.unlink(fname)


def _fix_macosx_header_paths(*args):
    # Fix path to SDK headers if necessary
    _MACOSX_XCODE_REF_PATH = (  # pylint: disable=invalid-name
        '/Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer'
    )
    _MACOSX_DEVTOOLS_REF_PATH = '/Library/Developer/CommandLineTools/'  # pylint: disable=invalid-name
    _has_xcode = os.path.exists(_MACOSX_XCODE_REF_PATH)
    _has_devtools = os.path.exists(_MACOSX_DEVTOOLS_REF_PATH)
    if not _has_xcode and not _has_devtools:
        important_msgs('ERROR: Must install either Xcode or CommandLineTools!')
        raise BuildFailed()

    for compiler_args in args:
        for idx, item in enumerate(compiler_args):
            if not _has_xcode and _MACOSX_XCODE_REF_PATH in item:
                compiler_args[idx] = item.replace(_MACOSX_XCODE_REF_PATH, _MACOSX_DEVTOOLS_REF_PATH)

            if not _has_devtools and _MACOSX_DEVTOOLS_REF_PATH in item:
                compiler_args[idx] = item.replace(_MACOSX_DEVTOOLS_REF_PATH, _MACOSX_XCODE_REF_PATH)


# ==============================================================================


class BuildFailed(Exception):
    """Extension raised if the build fails for any reason."""

    def __init__(self):
        """Initialize a BuildFailed exception object."""
        super().__init__()
        self.cause = sys.exc_info()[1]  # work around py 2/3 different syntax


# ------------------------------------------------------------------------------
# Python build related variable

cpython = platform.python_implementation() == 'CPython'
ext_errors = (CCompilerError, DistutilsExecError, DistutilsPlatformError)
if sys.platform == 'win32':
    # 2.6's distutils.msvc9compiler can raise an IOError when failing to
    # find the compiler
    ext_errors += (IOError,)

# ==============================================================================
# ProjectQ C++ extensions

ext_modules = [
    Extension(
        'projectq.backends._sim._cppsim',
        ['projectq/backends/_sim/_cppsim.cpp'],
        include_dirs=[
            # Path to pybind11 headers
            Pybind11Include(),
            Pybind11Include(user=True),
        ],
        language='c++',
    ),
]

# ==============================================================================


class BuildExt(build_ext):
    """A custom build extension for adding compiler-specific options."""

    c_opts = {
        'msvc': ['/EHsc'],
        'unix': [],
    }

    user_options = build_ext.user_options + [
        (
            'gen-compiledb',
            None,
            'Generate a compile_commands.json alongside the compilation implies (-n/--dry-run)',
        ),
    ]

    boolean_options = build_ext.boolean_options + ['gen-compiledb']

    def initialize_options(self):
        """Initialize this command's options."""
        build_ext.initialize_options(self)
        self.gen_compiledb = None

    def finalize_options(self):
        """Finalize this command's options."""
        build_ext.finalize_options(self)
        if self.gen_compiledb:
            self.dry_run = True  # pylint: disable=attribute-defined-outside-init

    def run(self):
        """Execute this command."""
        try:
            build_ext.run(self)
        except DistutilsPlatformError as err:
            raise BuildFailed() from err

    def build_extensions(self):
        """Build the individual C/C++ extensions."""
        self._configure_compiler()

        for ext in self.extensions:
            ext.extra_compile_args = self.opts
            ext.extra_link_args = self.link_opts

        if self.compiler.compiler_type == 'unix' and self.gen_compiledb:
            compile_commands = []
            for ext in self.extensions:
                commands = self._get_compilation_commands(ext)
                for cmd, src in commands:
                    compile_commands.append(
                        {
                            'directory': os.path.dirname(os.path.abspath(__file__)),
                            'command': cmd,
                            'file': os.path.abspath(src),
                        }
                    )

            import json  # pylint: disable=import-outside-toplevel

            with open(
                os.path.join(os.path.dirname(os.path.abspath(__file__)), 'compile_commands.json'),
                'w',
            ) as json_file:
                json.dump(compile_commands, json_file, sort_keys=True, indent=4)

        try:
            build_ext.build_extensions(self)
        except ext_errors as err:
            raise BuildFailed() from err
        except ValueError as err:
            # this can happen on Windows 64 bit, see Python issue 7511
            if "'path'" in str(sys.exc_info()[1]):  # works with both py 2/3
                raise BuildFailed() from err
            raise

    def _get_compilation_commands(self, ext):
        # pylint: disable=protected-access
        (_, objects, extra_postargs, pp_opts, build,) = self.compiler._setup_compile(
            outdir=self.build_temp,
            sources=ext.sources,
            macros=ext.define_macros,
            incdirs=ext.include_dirs,
            extra=ext.extra_compile_args,
            depends=ext.depends,
        )

        cc_args = self.compiler._get_cc_args(pp_opts=pp_opts, debug=self.debug, before=None)
        compiler_so = self.compiler.compiler_so
        compiler_so[0] = find_executable(compiler_so[0])

        commands = []
        for obj in objects:
            try:
                src, ext = build[obj]
            except KeyError:
                continue

            commands.append(
                (
                    ' '.join(
                        compiler_so + cc_args + [os.path.abspath(src), "-o", os.path.abspath(obj)] + extra_postargs
                    ),
                    src,
                )
            )
        return commands

    def _configure_compiler(self):
        # pylint: disable=attribute-defined-outside-init

        # Force dry_run = False to allow for compiler feature testing
        dry_run_old = self.compiler.dry_run
        self.compiler.dry_run = False

        if (
            int(os.environ.get('PROJECTQ_CLEANUP_COMPILER_FLAGS', 0))
            and self.compiler.compiler_type == 'unix'
            and sys.platform != 'darwin'
        ):
            self._cleanup_compiler_flags()

        if sys.platform == 'darwin':
            _fix_macosx_header_paths(self.compiler.compiler, self.compiler.compiler_so)

            if compiler_test(self.compiler, '-stdlib=libc++'):
                self.c_opts['unix'] += ['-stdlib=libc++']

        compiler_type = self.compiler.compiler_type
        self.opts = self.c_opts.get(compiler_type, [])
        self.link_opts = []

        if not compiler_test(self.compiler):
            important_msgs(
                'ERROR: something is wrong with your C++ compiler.\nFailed to compile a simple test program!'
            )
            raise BuildFailed()

        # ------------------------------

        status_msgs('Configuring OpenMP')
        self._configure_openmp()
        status_msgs('Configuring compiler intrinsics')
        self._configure_intrinsics()
        status_msgs('Configuring C++ standard')
        self._configure_cxx_standard()

        # ------------------------------
        # Other compiler tests

        status_msgs('Other compiler tests')
        self.compiler.define_macro('VERSION_INFO', f'"{self.distribution.get_version()}"')
        if compiler_type == 'unix' and compiler_test(self.compiler, '-fvisibility=hidden'):
            self.opts.append('-fvisibility=hidden')

        self.compiler.dry_run = dry_run_old
        status_msgs('Finished configuring compiler!')

    def _configure_openmp(self):
        if self.compiler.compiler_type == 'msvc':
            return

        kwargs = {
            'link_shared_lib': True,
            'include': '#include <omp.h>',
            'body': 'int a = omp_get_num_threads(); ++a;',
        }

        for flag in ['-openmp', '-fopenmp', '-qopenmp', '/Qopenmp']:
            if compiler_test(self.compiler, flag, link_postargs=[flag], **kwargs):
                self.opts.append(flag)
                self.link_opts.append(flag)
                return

        flag = '-fopenmp'
        if sys.platform == 'darwin' and compiler_test(self.compiler, flag):
            try:
                llvm_root = subprocess.check_output(['brew', '--prefix', 'llvm']).decode('utf-8')[:-1]
                compiler_root = subprocess.check_output(['which', self.compiler.compiler[0]]).decode('utf-8')[:-1]

                # Only add the flag if the compiler we are using is the one
                # from HomeBrew
                if llvm_root in compiler_root:
                    l_arg = f'-L{llvm_root}/lib'
                    if compiler_test(self.compiler, flag, link_postargs=[l_arg, flag], **kwargs):
                        self.opts.append(flag)
                        self.link_opts.extend((l_arg, flag))
                        return
            except subprocess.CalledProcessError:
                pass

            try:
                # Only relevant for MacPorts users with clang-3.7
                port_path = subprocess.check_output(['which', 'port']).decode('utf-8')[:-1]
                macports_root = os.path.dirname(os.path.dirname(port_path))
                compiler_root = subprocess.check_output(['which', self.compiler.compiler[0]]).decode('utf-8')[:-1]

                # Only add the flag if the compiler we are using is the one
                # from MacPorts
                if macports_root in compiler_root:
                    inc_dir = f'{macports_root}/include/libomp'
                    lib_dir = f'{macports_root}/lib/libomp'
                    c_arg = '-I' + inc_dir
                    l_arg = '-L' + lib_dir

                    if compiler_test(self.compiler, flag, compile_postargs=[c_arg], link_postargs=[l_arg], **kwargs):
                        self.compiler.add_include_dir(inc_dir)
                        self.compiler.add_library_dir(lib_dir)
                        return
            except subprocess.CalledProcessError:
                pass

        important_msgs('WARNING: compiler does not support OpenMP!')

    def _configure_intrinsics(self):
        flags = [
            '-march=native',
            '-mavx2',
            '/arch:AVX2',
            '/arch:CORE-AVX2',
            '/arch:AVX',
        ]

        if int(os.environ.get('PROJECTQ_NOINTRIN', '0')) or (
            sys.platform == 'darwin'
            and platform.machine() == 'arm64'
            and (sys.version_info.major == 3 and sys.version_info.minor < 9)
        ):
            important_msgs(
                'Either requested no-intrinsics or detected potentially unsupported Python version on '
                'Apple Silicon: disabling intrinsics'
            )
            self.compiler.define_macro('NOINTRIN')
            return
        if os.environ.get('PROJECTQ_DISABLE_ARCH_NATIVE'):
            flags = flags[1:]

        for flag in flags:
            if compiler_test(
                self.compiler,
                flagname=flag,
                include='#include <immintrin.h>',
                body='__m256d neg = _mm256_set1_pd(1.0); (void)neg;',
            ):
                self.opts.append(flag)
                self.compiler.define_macro("INTRIN")
                break

        for flag in ['-ffast-math', '-fast', '/fast', '/fp:precise']:
            if compiler_test(self.compiler, flagname=flag):
                self.opts.append(flag)
                break

    def _configure_cxx_standard(self):
        if self.compiler.compiler_type == 'msvc':
            return

        cxx_standards = [17, 14, 11]
        if sys.platform == 'darwin':
            major_version = int(platform.mac_ver()[0].split('.')[0])
            minor_version = int(platform.mac_ver()[0].split('.')[1])
            if major_version <= 10 and minor_version < 14:
                cxx_standards = [year for year in cxx_standards if year < 17]

        for year in cxx_standards:
            flag = f'-std=c++{year}'
            if compiler_test(self.compiler, flag):
                self.opts.append(flag)
                return
            flag = f'/Qstd=c++{year}'
            if compiler_test(self.compiler, flag):
                self.opts.append(flag)
                return

        important_msgs('ERROR: compiler needs to have at least C++11 support!')
        raise BuildFailed()

    def _cleanup_compiler_flags(self):
        status_msgs('INFO: Performing compiler flags cleanup')
        compiler_exe = self.compiler.compiler[0]
        compiler_exe_so = self.compiler.compiler_so[0]
        linker_so = self.compiler.linker_so[0]
        compiler_flags = set(self.compiler.compiler[1:])
        compiler_so_flags = set(self.compiler.compiler_so[1:])
        linker_so_flags = set(self.compiler.linker_so[1:])

        all_common_flags = compiler_flags & compiler_so_flags & linker_so_flags
        common_compiler_flags = (compiler_flags & compiler_so_flags) - all_common_flags

        compiler_flags = compiler_flags - common_compiler_flags - all_common_flags
        compiler_so_flags = compiler_so_flags - common_compiler_flags - all_common_flags

        flags = []
        for flag in common_compiler_flags:
            compiler = type(self.compiler)()
            compiler.set_executables(compiler=compiler_exe, compiler_so=compiler_exe_so, linker_so=linker_so)

            compiler.debug_print(f'INFO: trying out {flag}')
            if compiler_test(compiler, flag, link_shared_lib=True, compile_postargs=['-fPIC']):
                flags.append(flag)
            else:
                important_msgs(f'WARNING: ignoring unsupported compiler flag: {flag}')

        self.compiler.compiler = [compiler_exe] + list(compiler_flags)
        self.compiler.compiler_so = [compiler_exe_so] + list(compiler_so_flags)
        self.compiler.linker_so = [linker_so] + list(linker_so_flags - all_common_flags)

        self.compiler.compiler.extend(flags)
        self.compiler.compiler_so.extend(flags)

        flags = []
        for flag in all_common_flags:
            if compiler_test(self.compiler, flag):
                flags.append(flag)
            else:
                important_msgs(f'WARNING: ignoring unsupported compiler flag: {flag}')

        self.compiler.compiler.extend(flags)
        self.compiler.compiler_so.extend(flags)
        self.compiler.linker_so.extend(flags)


# ------------------------------------------------------------------------------


class ClangTidy(Command):
    """A custom command to run Clang-Tidy on all C/C++ source files."""

    description = 'run Clang-Tidy on all C/C++ source files'
    user_options = [('warning-as-errors', None, 'Warning as errors')]
    boolean_options = ['warning-as-errors']

    sub_commands = [('build_ext', None)]

    def initialize_options(self):
        """Initialize this command's options."""
        self.warning_as_errors = None

    def finalize_options(self):
        """Finalize this command's options."""

    def run(self):
        """Execute this command."""
        # Ideally we would use self.run_command(command) but we need to ensure
        # that --dry-run --gen-compiledb are passed to build_ext regardless of
        # other arguments
        command = 'build_ext'
        distutils.log.info("running %s --dry-run --gen-compiledb", command)
        cmd_obj = self.get_finalized_command(command)
        cmd_obj.dry_run = True
        cmd_obj.gen_compiledb = True
        try:
            cmd_obj.run()
            self.distribution.have_run[command] = 1
        except BuildFailed as err:
            distutils.log.error('build_ext --dry-run --gen-compiledb command failed!')
            raise RuntimeError('build_ext --dry-run --gen-compiledb command failed!') from err

        command = ['clang-tidy']
        if self.warning_as_errors:
            command.append('--warnings-as-errors=*')
        for ext in self.distribution.ext_modules:
            command.extend(os.path.abspath(p) for p in ext.sources)
        spawn(command, dry_run=self.dry_run)


# ------------------------------------------------------------------------------


class GenerateRequirementFile(Command):
    """A custom command to list the dependencies of the current."""

    description = 'List the dependencies of the current package'
    user_options = [
        ('include-all-extras', None, 'Include all "extras_require" into the list'),
        ('include-extras=', None, 'Include some of extras_requires into the list (comma separated)'),
    ]

    boolean_options = ['include-all-extras']

    def initialize_options(self):
        """Initialize this command's options."""
        self.include_extras = None
        self.include_all_extras = None
        self.extra_pkgs = []
        self.dependencies = []

    def finalize_options(self):
        """Finalize this command's options."""
        include_extras = self.include_extras.split(',') if self.include_extras else []
        pyproject_toml = parse_toml(Path(__file__).parent / 'pyproject.toml')

        for name, pkgs in pyproject_toml['project']['optional-dependencies'].items():
            if self.include_all_extras or name in include_extras:
                self.extra_pkgs.extend(pkgs)

        # pylint: disable=attribute-defined-outside-init
        self.dependencies = self.distribution.install_requires
        if not self.dependencies:
            self.dependencies = pyproject_toml['project']['dependencies']

    def run(self):
        """Execute this command."""
        with open('requirements.txt', 'w') as req_file:
            for pkg in self.dependencies:
                req_file.write(f'{pkg}\n')
            req_file.write('\n')
            for pkg in self.extra_pkgs:
                req_file.write(f'{pkg}\n')


# ------------------------------------------------------------------------------


class Distribution(_Distribution):
    """Distribution class."""

    def has_ext_modules(self):  # pylint: disable=no-self-use
        """Return whether this distribution has some external modules."""
        # We want to always claim that we have ext_modules. This will be fine
        # if we don't actually have them (such as on PyPy) because nothing
        # will get built, however we don't want to provide an overally broad
        # Wheel package when building a wheel without C support. This will
        # ensure that Wheel knows to treat us as if the build output is
        # platform specific.
        return True


# ==============================================================================


def run_setup(with_cext):
    """Run the setup() function."""
    kwargs = {}
    if with_cext:
        kwargs['ext_modules'] = ext_modules
    else:
        kwargs['ext_modules'] = []

    # NB: Workaround for people calling setup.py without a proper environment containing setuptools-scm
    #     This can typically be the case when calling the `gen_reqfile` or `clang_tidy`commands
    if not _HAS_SETUPTOOLS_SCM:
        kwargs['version'] = '0.0.0'

    setup(
        cmdclass={
            'build_ext': BuildExt,
            'clang_tidy': ClangTidy,
            'gen_reqfile': GenerateRequirementFile,
        },
        distclass=Distribution,
        **kwargs,
    )


# ==============================================================================

if not cpython:
    run_setup(False)
    important_msgs(
        'WARNING: C/C++ extensions are not supported on some features are disabled (e.g. C++ simulator).',
        'Plain-Python build succeeded.',
    )
elif os.environ.get('PROJECTQ_DISABLE_CEXT'):
    run_setup(False)
    important_msgs(
        'PROJECTQ_DISABLE_CEXT is set; not attempting to build C/C++ extensions.',
        'Plain-Python build succeeded.',
    )

else:
    try:
        run_setup(True)
    except BuildFailed as exc:
        if os.environ.get('PROJECTQ_CI_BUILD'):
            raise exc

        important_msgs(
            exc.cause,
            'WARNING: Some C/C++ extensions could not be compiled, '
            + 'some features are disabled (e.g. C++ simulator).',
            'Failure information, if any, is above.',
            'Retrying the build without the C/C++ extensions now.',
        )

        run_setup(False)

        important_msgs(
            'WARNING: Some C/C++ extensions could not be compiled, '
            + 'some features are disabled (e.g. C++ simulator).',
            'Plain-Python build succeeded.',
        )

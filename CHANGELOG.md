# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [v0.8.0] - 2022-10-18

### Added

-   New backend for the Azure Quantum platform

### Changed

-   Support for Python 3.6 and earlier is now deprecated
-   Moved package metadata into pyproject.toml

### Fixed

-   Fixed installation on Apple Silicon with older Python versions (&lt; 3.9)

### Repository

-   Update `docker/setup-qemu-action` GitHub action to v2
-   Fixed CentOS 7 configuration issue
-   Added two new pre-commit hooks: `blacken-docs` and `pyupgrade`

## [v0.7.3] - 2022-04-27

### Fixed

-   Fixed IonQ dynamic backends fetch, which relied on an incorrect path.

## [v0.7.2] - 2022-04-11

### Changed

-   Added IonQ dynamic backends fetch.

### Repository

-   Fix issues with building on CentOS 7 & 8
-   Update `pre-commit/pre-commit-hooks` to v4.2.0
-   Update `Lucas-C/pre-commit-hooks` hook to v1.1.13
-   Update `flake8` hook to v4.0.1
-   Update `pylint` hook to v3.0.0a4
-   Update `black` hook to v22.3.0
-   Update `check-manifest` to v0.48

## [0.7.1] - 2022-01-10

### Added

-   Added environment variable to avoid -march=native when building ProjectQ
-   Added environment variable to force build failure if extensions do not compile on CI

### Changed

### Deprecated

### Fixed

-   Fix compiler flags cleanup function for use on CI
-   Fix workflow YAML to allow execution of GitHub Actions locally using `act`
-   GitHub action using deprecated and vulnerable `pre-commit` version
-   Fixed issue with `gen_reqfile` command if `--include-extras` is not provided

### Removed

### Repository

-   Add configuration for CIBuildWheel in `pyproject.toml`
-   Remove use of deprecated images `windows-2016` in GitHub workflows
-   Re-add build of Python binary wheels in release publishing GitHub workflow
-   Update `dangoslen/changelog-enforcer` GitHub action to v3
-   Update `thomaseizinger/keep-a-changelog-new-release` GiHub action to v1.3.0
-   Update `thomaseizinger/create-pull-request` GiHub action to v1.2.2
-   Update pre-commit hook `pre-commit/pre-commit-hooks` to v4.1.0
-   Update pre-commit hook `PyCQA/isort` to v5.10.1
-   Update pre-commit hook `psf/black` to v21.12b0
-   Update pre-commit hook `PyCQA/flake8` to v4.0.1
-   Update pre-commit hook `mgedmin/check-manifest` to v0.47

## [0.7.0] - 2021-07-14

### Added

-   UnitarySimulator backend for computing the unitary transformation corresponding to a quantum circuit

### Changed

-   Moved some exceptions classes into their own files to avoid code duplication

### Deprecated

### Fixed

-   Prevent infinite recursion errors when too many compiler engines are added to the MainEngine
-   Error in testing the decomposition for the phase estimation gate
-   Fixed small issue with matplotlib drawing backend
-   Make all docstrings PEP257 compliant

### Removed

-   Some compatibility code for Python 2.x

### Repository

-   Added `isort` to the list of pre-commit hooks
-   Added some more flake8 plugins to the list used by `pre-commit`:
    -   flake8-breakpoint
    -   flake8-comprehensions
    -   flake8-docstrings
    -   flake8-eradicate
    -   flake8-mutable

## [0.6.1] - 2021-06-23

### Repository

-   Fix GitHub workflow for publishing a new release

## [0.6.0] - 2021-06-23

### Added

-   New backend for the IonQ platform
-   New backend for the AWS Braket platform
-   New gates for quantum math operations on quantum registers
-   Support for state-dependent control qubits (ie. negatively or positively controlled gates)

### Changed

-   Name of the single parameter of the `LocalOptimizer` has been changed from `m` to `cache_size` in order to better represent its actual use.

### Deprecated

-   Compatibility with Python &lt;= 3.5
-   `LocalOptimizer(m=10)` should be changed into `LocalOptimizer(cache_size=10)`. Using of the old name is still possible, but is deprecated and will be removed in a future version of ProjectQ.

### Fixed

-   Installation on Mac OS Big Sur
-   IBM Backend issues with new API

### Removed

-   Compatibility with Python 2.7
-   Support for multi-qubit measurement gates has been dropped; use `All(Measure) | qureg` instead

### Repository

-   Use `setuptools-scm` for versioning

-   Added `.editorconfig` file

-   Added `pyproject.toml` and `setup.cfg`

-   Added CHANGELOG.md

-   Added support for GitHub Actions
    -   Build and testing on various plaforms and compilers
    -   Automatic draft of new release
    -   Automatic publication of new release once ready
    -   Automatic upload of releases artifacts to PyPi and GitHub

-   Added pre-commit configuration file

-   Updated cibuildwheels action to v1.11.1

-   Updated thomaseizinger/create-pull-request action to v1.1.0

## [0.5.1] - 2019-02-15

### Added

-   Add histogram plot function for measurement results (thanks @AriJordan )
-   New backend for AQT (thanks @dbretaud )

### Fixed

-   Fix Qiskit backend (thanks @dbretaud )
-   Fix bug with matplotlib drawer (thanks @AriJordan )

## [0.5.0] - 2020

### Added

-   New [PhaseEstimation](https://projectq.readthedocs.io/en/latest/projectq.ops.html#projectq.ops.QPE) and [AmplitudeAmplification](https://projectq.readthedocs.io/en/latest/projectq.ops.html#projectq.ops.QAA) gates (thanks @fernandodelaiglesia)
-   New [Rxx](https://projectq.readthedocs.io/en/latest/projectq.ops.html#projectq.ops.Rxx), [Ryy](https://projectq.readthedocs.io/en/latest/projectq.ops.html#projectq.ops.Ryy) and [Rzz](https://projectq.readthedocs.io/en/latest/projectq.ops.html#projectq.ops.Rzz) gates (thanks @dwierichs)
-   New decomposition rules and compiler setup for trapped ion quantum based computers (thanks @dbretaud)
-   Added basic circuit drawer compiler engine based on Matplotlib [CircuitDrawerMatplotlib](https://projectq.readthedocs.io/en/latest/projectq.backends.html#projectq.backends.CircuitDrawerMatplotlib) (thanks @Bombenchris)

### Changed

-   Significantly improved C++ simulator performances (thanks @melven)
-   Allow user modification of the qubit drawing order for the `CircuitDrawer` compiler engine (thanks @alexandrupaler)
-   Update to the installation script. The installation now automatically defaults to the pure Python implementation if compilation of the C++ simulator (or other C++ modules) should fail (#337)
-   Automatic generation of the documentation (#339)

### Fixes

-   Fixed connection issues between IBM backend and the IBM Quantum Experience API (thanks @alexandrupaler)

### Deprecated

The ProjectQ v0.5.x release branch is the last one that is guaranteed to work with Python 2.7.x.

Future releases might introduce changes that will require Python 3.5 (Python 3.4 and earlier have already been declared deprecated at the time of this writing)

[Unreleased]: https://github.com/ProjectQ-Framework/ProjectQ/compare/v0.8.0...HEAD

[v0.8.0]: https://github.com/ProjectQ-Framework/ProjectQ/compare/v0.7.3...v0.8.0

[v0.7.3]: https://github.com/ProjectQ-Framework/ProjectQ/compare/v0.7.2...v0.7.3

[v0.7.2]: https://github.com/ProjectQ-Framework/ProjectQ/compare/v0.7.1...v0.7.2

[0.7.1]: https://github.com/ProjectQ-Framework/ProjectQ/compare/v0.7.0...v0.7.1

[0.7.0]: https://github.com/ProjectQ-Framework/ProjectQ/compare/v0.6.1...v0.7.0

[0.6.0]: https://github.com/ProjectQ-Framework/ProjectQ/compare/v0.5.1...v0.6.0

[0.5.1]: https://github.com/ProjectQ-Framework/ProjectQ/compare/v0.5.0...v0.5.1

[0.5.0]: https://github.com/ProjectQ-Framework/ProjectQ/compare/v0.4.2...v0.5.0

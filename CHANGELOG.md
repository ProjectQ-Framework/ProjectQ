# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
### Changed
### Deprecated
### Fixed
### Removed
### Repository

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

[Unreleased]: https://github.com/ProjectQ-Framework/ProjectQ/compare/0.6.0...HEAD

[0.6.0]: https://github.com/ProjectQ-Framework/ProjectQ/compare/0.5.1...0.6.0

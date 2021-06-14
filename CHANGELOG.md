# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Support for GitHub Actions
  * Build and testing on various plaforms and compilers
  * Automatic draft of new release
  * Automatic publication of new release once ready
  * Automatic upload of releases artifacts to PyPi and GitHub
- Use ``setuptools-scm`` for versioning
- Added ``.editorconfig` file
- Added ``pyproject.toml`` and ``setup.cfg``
- Added CHANGELOG.md
- Added backend for IonQ.

### Deprecated

-   Compatibility with Python <= 3.5

### Removed

-   Compatibility with Python 2.7

### Repository

- Updated cibuildwheels to 1.11.1

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

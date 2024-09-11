# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.5.0] - Unpublished

**BREAKING** All gadgets have been updated to use Sui GraphQL in addition to command line changes.

### Added

### Fixed

### Changed

### Removed

- `dsl` and `module` commands

## [0.4.9] - 2024-05-03

### Added

### Fixed

### Changed

- Bumped requirements.txt for pysui to >= 0.49.0

### Removed

## [0.4.3] - 2023-11-06

### Added

### Fixed

### Changed

- Bumped requirements.txt for pysui to >= 0.41.0

### Removed

## [0.4.2] - 2023-11-06

### Added

### Fixed

### Changed

- Bumped requirements.txt for pysui to >= 0.39.0

### Removed

## [0.4.0] - 2023-10-13

### Added

### Fixed

### Changed

- Bumped requirements.txt for pysui to >= 0.37.1

### Removed

## [0.3.3] - 2023-08-11

### Added

### Fixed

### Changed

- Bumped requirements.txt for pysui to >= 0.32.0
- Documentation

### Removed

## [0.3.1] - 2023-08-03

### Added

### Fixed

- [bug](https://github.com/FrankC01/pysui_gadgets/issues/12) Update splay budget handling as per pysui 0.32.0

### Changed

- Change for `pysui` 0.32.0

### Removed

## [0.3.0] - Unpublished

### Added

### Fixed

### Changed

- Change for `pysui` 0.30.0

### Removed

## [0.2.0] - 2023-07-08

### Added

- `--merge-threshold` added to `splay` and `to-one` to control partitiioning of transactions during merge phase

### Fixed

- [bug](https://github.com/FrankC01/pysui_gadgets/issues/11)

### Changed

### Removed

## [0.1.0] - 2023-06-05

### Added

- `vh` utility for tracing history of object

### Fixed

### Changed

### Removed

## [0.0.14] - Unpublished

### Added

### Fixed

- Added 'splay' to README

### Changed

### Removed

## [0.0.13] - 2023-05-20

### Added

### Fixed

- Correct setting for readme in pyproject.toml for build and PyPi publish
- `splay` gadget command line argument short cut and posix long arg consistency

### Changed

- Bumped `pysui` dependency to version 0.21.2

### Removed

## [0.0.12] - 2023-05-18

### Added

- `splay` utility for taking addresses coins and distributing to other addresses

### Fixed

### Changed

- Updated to use `pysui` 0.21+

### Removed

## [0.0.11] - 2023-05-03

### Added

### Fixed

### Changed

### Removed

## [0.0.10] - 2023-04-16

### Added

### Fixed

### Changed

- Updated for `pysui` 0.16.1

### Removed

## [0.0.9] - 2023-04-13

### Added

### Fixed

### Changed

- Updated for `pysui` 0.16.0

### Removed

## [0.0.8] - 2023-03-30

### Added

### Fixed

### Changed

<<<<<<< HEAD

- # Updated for `pysui` 0.15.0
- Bumped dependencies for pysui from 0.13.0 to 0.15.x
  > > > > > > > 4c26f9dc3bc146f1bf96b64cb50c80b859eea40a

### Removed

## [0.0.7] - 2023-01-06

### Added

### Fixed

### Changed

- Bumped dependencies for pysui to 0.7.0
- Fetching address gas now using changes to SUI 0.20.0 and supported in pysui 0.7.0

### Removed

## [0.0.6] - 2022-12-29

### Added

- `-s` argument to package genstructs command
- `to_one` gadget that merges all SUI coins 'to one' for an address

### Fixed

### Changed

- Bumping pysui to 0.6.0

### Removed

## [0.0.5] - 2022-12-20

### Added

### Fixed

### Changed

- Bumped to pysui 0.5.1

### Removed

## [0.0.4] - 2022-12-19

### Added

- SUI Address support

### Fixed

### Changed

- Bumped to pysui 0.5.0

### Removed

## [0.0.3] - 2022-12-15

### Added

- [enhancement](https://github.com/FrankC01/pysui_gadgets/issues/1)
- [enhancement](https://github.com/FrankC01/pysui_gadgets/issues/2)

### Fixed

- ObjectRead transition in `templates/sync_model.py`

### Changed

- Removed cruft from template
- Reducedd calls to `ast.parse`

### Removed

## [0.0.2] - 2022-12-15

### Added

- package: Commands to inspect SUI package meta-data
- dslgen: Commands to generate Python DSL classes from SUI package modules

### Fixed

- Typo in FieldIR return assignment
- Attribute check in sync_model template `instance` method
- For all generated XXXModule class methods, added `.copy()` to `locals()`
- Fix list comprehension in sync_model `_Inner.type_args()`
- If type_arg not in ObjectReadData, use `SuiNullType`

### Changed

### Removed

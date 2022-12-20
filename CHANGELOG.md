# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unpublished]

### Added

### Fixed

### Changed

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

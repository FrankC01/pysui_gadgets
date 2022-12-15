# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

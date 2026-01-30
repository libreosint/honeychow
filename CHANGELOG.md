# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- README.md documentation
- CHANGELOG.md
- Makefile with install, dev, build, clean, lint, and format targets
- ruff as dev dependency for linting and formatting

### Changed
- Updated project URLs to GitHub

## [0.1.0] - 2026-01-30

### Added
- Initial release
- Asynchronous username enumeration across 705+ websites
- Configurable concurrent workers and request timeouts
- CSV export functionality
- Filter by specific sites or categories
- Table and quiet output modes
- Support for remote and local site databases
- crates.io site support

### Fixed
- False positives in site detection
- False negatives in database entries

### Removed
- PyPI site (unreliable detection)
- Kali Linux forums (unreliable detection)


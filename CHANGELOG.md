# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
### Fixed
- Timestamps with a time zone (e.g. `+01:00`, `Z`) were ignored; they are now
  sorted by the local time as written, without offset adjustment
- Dates given as a list were not handled
- `--test` and `--copy` options had no effect
- Files with the same name were skipped (copy) or overwritten (move)
- Image collections shared their content between instances

## [0.9.2] - 2022-01-01
### Fixed
- Gihub CI script was emergency fixed

## [0.9.1] - 2022-01-01
### Fixed
- Output in report mode
- stripped down ExifTool before release zip step
### Other
- Code cleanup

## [0.9.0] - 2021-12-30
### Added 
- Initial features
- Initial tests
- Automation using Github actions

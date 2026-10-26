# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
### Changed
- Metadata is read in pure Python (exifread, hachoir): ExifTool and Perl
  are no longer needed
- Packaged with pyproject.toml, install with
  `uv tool install git+https://github.com/arcadien/sortphotos`
- Python 3.10 or later is required
### Removed
- `sortphotos.py` script: use the `sortphotos` command, `uv run sortphotos`
  or `python -m sortphotos`
- IPTC/XMP `DateCreated` tag is no longer read
### Fixed
- Timestamps with a time zone (e.g. `+01:00`, `Z`) were ignored; they are now
  sorted by the local time as written, without offset adjustment
- Dates given as a list were not handled
- `--test` and `--copy` options had no effect
- Files with the same name were skipped (copy) or overwritten (move)
- Image collections shared their content between instances
- Accented file names could crash metadata reading (UTF-8 split across reads)
- ExifTool process was not waited for on exit
- Folder structure was wrong when copying without sort format
- Hidden files and directories were not ignored as documented
- Importing the package changed the process locale
- Help text showed stray backslashes
- Package could not be installed (`pip install`), now provides a
  `sortphotos` command
- Progress symbols were displayed in bursts
### Other
- CI uses Python 3.15, runs on pull requests and lints the whole project
- Tests run in temporary directories
- Code cleanup

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

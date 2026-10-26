
# Description

SortPhotos is a Python tool that organizes photos into folders by date and/or time (year, year/month, year/month/day, or other custom formats).  If you're like me then your growing collection of files are contained in a bunch of folders, some with a date like "Sep 2010", and others which names like "Camping Trip".  SortPhotos takes this collection of folders and files and reorganizes them into a hierarchy of folders by almost any custom date/time format (by default it is by year then month).  It will work with any file, but works best with image and video files that contain EXIF or other metadata formats because that stays with the file even if the files are modified.  The script is also useful for transferring files from your camera into your collection of nicely organized photos.

# Install

SortPhotos is written in pure Python (3.10 or later), no external tool is needed.
Install it as a `sortphotos` command with [uv](https://docs.astral.sh/uv/):

    uv tool install git+https://github.com/arcadien/sortphotos

or run it once without installing:

    uvx --from git+https://github.com/arcadien/sortphotos sortphotos -h

From a clone, `uv run sortphotos -h` runs the working copy.

Dates are read from photo EXIF (JPEG, TIFF, HEIC, PNG and TIFF based RAW
like NEF, CR2, DNG) and from video metadata (MP4, MOV, AVI, MKV...). Files
without a readable date are sorted by their file creation (macOS, Windows)
or modification date.

# Usage

SortPhotos is intended to be used primarily from the command line.  To see all the options, invoke help

    sortphotos -h

The simplest usage is to specify a source directory (the directory where your mess of files is currently located) and a destination directory (where you want the files and directories to go).  The source directory is searched recursively, and files are moved unless `-c` is given.

    sortphotos /Users/Me/MessyDirectory /Users/Me/Pictures

## Options

```
positional arguments:
  src_dir               source directory
  dest_dir              destination directory

options:
  -h, --help            show this help message and exit
  -c, --copy            copy files instead of move
  -t, --test            run a test: files will not be moved/copied,
                        instead you will just get a list of what would happen
  --sort SORT           choose destination folder structure using datetime format
                        https://docs.python.org/3/library/datetime.html#strftime-and-strptime-behavior.
                        Use forward slashes / to indicate subdirectory(ies)
                        (independent of your OS convention).
                        The default is '%Y/%m-%b', which separates by year then month
                        with both the month number and name (e.g., 2012/02-Feb).
  --ignore-file-types IGNORE_FILE_TYPES [IGNORE_FILE_TYPES ...]
                        ignore file types (extensions, e.g. JPG MOV)
                        hidden files (.*) are always ignored
```

Month and day names (`%b`, `%B`, `%a`...) follow your system language, e.g. `2021/01-janv.` with a French locale.

## Output 

Symbol meaning in output:
- `.`: new file added in collection
- `+`: duplicate detected
- `-`: file copied
- `#`: file moved
- `~`: file skipped (target exists)

Files are never overwritten: if a different file with the same name already exists
in the target (or is planned in the same run), a suffix is added (`IMG_0001_1.JPG`).
A file identical to one already in the target is skipped.

With `-t`/`--test`, nothing is written: each planned copy/move is printed instead.

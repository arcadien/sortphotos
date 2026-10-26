# -*- coding: utf-8 -*-

from sortphotos import ImageCollection
from sortphotos.MetadataReader import MetadataReader


def main():
    import argparse
    import locale

    # use the user's locale, e.g. for month names in folder names (%b)
    locale.setlocale(locale.LC_ALL, '')

    MetadataReader.QuietLibraries()

    # setup command line parsing
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter,
        description='Sort files (primarily photos and videos) into folders by date\n'
                    'using EXIF and other metadata')
    parser.add_argument('src_dir', type=str, help='source directory')
    parser.add_argument('dest_dir', type=str, help='destination directory')
    parser.add_argument('-c', '--copy', action='store_true',
                        help='copy files instead of move', default=False)
    parser.add_argument('-t', '--test', action='store_true',
                        help='run a test: files will not be moved/copied,\n'
                             'instead you will just get a list of what would happen',
                        default=False)
    parser.add_argument('--sort', type=str, default='%Y/%m-%b',
                        help='choose destination folder structure using datetime format\n'
                             'https://docs.python.org/3/library/datetime.html#strftime-and-strptime-behavior.\n'
                             'Use forward slashes / to indicate subdirectory(ies)\n'
                             '(independent of your OS convention).\n'
                             "The default is '%%Y/%%m-%%b', which separates by year then month\n"
                             'with both the month number and name (e.g., 2012/02-Feb).')
    parser.add_argument('--ignore-file-types', type=str, nargs='+', default=[],
                        help='ignore file types (extensions, e.g. JPG MOV)\n'
                             'hidden files (.*) are always ignored')

    # parse command line arguments
    args = parser.parse_args()

    # traverse root directory, and list directories as dirs and files as files
    collection = ImageCollection.ImageCollection()
    collection.RecursiveAddDirectory(
        args.src_dir,
        args.ignore_file_types)

    print('Unique/total image count: {:5d}/{:5d}'.format(
        collection.GetUniqueImageCount(),
        collection.totalImageCount))

    print(collection)

    collection.CopyInto(args.dest_dir,
                        args.sort,
                        copy_files=args.copy,
                        dry_run=args.test)


if __name__ == '__main__':
    main()

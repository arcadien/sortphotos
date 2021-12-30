# -*- coding: utf-8 -*-

from sortphotos import ImageCollection


def main():
    import argparse

    # setup command line parsing
    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter,
                                     description='Sort files (primarily photos and videos) into folders by date\nusing EXIF and other metadata')
    parser.add_argument('src_dir', type=str, help='source directory')
    parser.add_argument('dest_dir', type=str, help='destination directory')
    parser.add_argument('-c', '--copy', action='store_true',
                        help='copy files instead of move', default=False)
    parser.add_argument('-t', '--test', action='store_true',
                        help='run a test.  files will not be moved/copied\ninstead you will just a list of would happen', default=False)
    parser.add_argument('--sort', type=str, default='%Y/%m-%b',    help="choose destination folder structure using datetime format \n\    https://docs.python.org/2/library/datetime.html#strftime-and-strptime-behavior. \n\    Use forward slashes / to indicate subdirectory(ies) (independent of your OS convention). \n\ The default is '%%Y/%%m-%%b', which separates by year then month \n\ with both the month number and name (e.g., 2012/02-Feb).")
    parser.add_argument('--ignore-file-types', type=str, nargs='+',    default=[],
                        help="ignore file types\n\    default is to only ignore hidden files (.*)")

    # parse command line arguments
    temp_args = parser.parse_args()
    args = dict()
    args['src_dir'] = temp_args.src_dir
    args['dest_dir'] = temp_args.dest_dir
    args['sort_format'] = temp_args.sort
    args['copy_files'] = temp_args.copy
    args['test'] = temp_args.test
    args['ignore_file_types'] = temp_args.ignore_file_types

    # traverse root directory, and list directories as dirs and files as files
    collection = ImageCollection()
    collection.RecursiveAddDirectory(
        args['src_dir'],
        args['ignore_file_types'])

    print('Unique/total image count: {:5d}/{:5d}'.format(
        collection.GetUniqueImageCount(),
        collection.totalImageCount))

    print(collection)

    collection.CopyInto(args['dest_dir'], args['sort_format'])


if __name__ == '__main__':
    main()

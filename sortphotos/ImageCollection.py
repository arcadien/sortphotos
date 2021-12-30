# -*- coding: utf-8 -*-

from __future__ import print_function
from __future__ import with_statement
import os
import sys
import shutil

import hashlib
from pathlib import Path

from sortphotos.ExifTool import ExifTool
from sortphotos.Image import Image


#
# Class managing images metatas
# Each file is hashed to avoid duplicate. The collection
# contains one Image instance per hash, and that Image
# may reference 0 or more duplicate of the first-seen file
# for the given hash.
class ImageCollection(object):

    _content = {}
    totalImageCount = 0

    def GetUniqueImageCount(self):
        return len(self._content)

    def RecursiveAddDirectory(self, directory, ignore_file_types=[]):
        # print('Building image collection..')
        with ExifTool(verbose=0) as e:
            for (path, dirs, files) in os.walk(directory):
                for file in files:
                    # ignore specified file extensions
                    fileextension = os.path.splitext(file)[-1]
                    fileextension = fileextension.upper().replace('.', '')
                    if fileextension in map(str.upper, ignore_file_types):
                        print(fileextension + ' files ignored, "' +
                              file + '" skipped')
                        print()
                        continue

                    # print('.', end='')
                    self.AddFile(os.path.join(path, file), e)
        # print('\nDone.')

    def CopyInto(self,
                 targetDirectory,
                 sort_format=None,
                 copy_files=True,
                 test=False):
        """
        Use the internal data structure to copy media files
        into the target directory
        """
        for image in self._content.values():

            date = image.creationDate
            src_file = image._metadata['SourceFile']
            src_fileName = os.path.basename(src_file)
            dest_dir = targetDirectory

            if(sort_format is not None):
                # create folder structure
                dir_structure = date.strftime(sort_format)
                dirs = dir_structure.split('/')
                for thedir in dirs:
                    dest_dir = os.path.join(dest_dir, thedir)
                    if not os.path.exists(dest_dir) and not test:
                        os.makedirs(dest_dir)
                # setup destination file
                dest_file = os.path.join(dest_dir, src_fileName)
                # root, ext = os.path.splitext(dest_file)
            else:
                # copy the same folder structure in the target
                p = Path(src_file)
                pathWithoutFirstLevel = Path(*p.parts[2:])
                dest_file = os.path.join(dest_dir, pathWithoutFirstLevel)
                dest_file = os.path.normpath(dest_file)
                print('dest_dir   : {0}'.format(dest_dir))
                print('Input path : {0}'.format(src_file))
                print('Output file: {0}'.format(dest_file))

                p = Path(dest_file)
                for thedir in p.parts[:-1]:
                    dest_dir = os.path.join(dest_dir, thedir)
                    if not os.path.exists(dest_dir) and not test:
                        os.makedirs(dest_dir)
            if copy_files:
                if not test:
                    targetPath = Path(dest_file)
                    if not targetPath.is_file():
                        shutil.copy2(src_file, dest_file)
                    else:
                        print('Skip copy, {0} already there'.format(dest_file))
                else:
                    print('Copy {0} in {1}'.format(src_file, dest_file))
            else:
                if not test:
                    shutil.move(src_file, dest_file)
                else:
                    print('Mode {0} in {1}'.format(src_file, dest_file))

    def HashFile(self, src_file):
        hasher = hashlib.md5()
        with open(src_file, 'rb') as afile:
            # buffered read by blocks of 64k
            b = afile.read(65536)
            while len(b) > 0:
                hasher.update(b)
                b = afile.read(65536)
        return (hasher.hexdigest())

    def AddFile(self, filePath, exifTool):
        if(0 == len(filePath)):
            return
        fileHash = self.HashFile(filePath)
        metadataDict = dict()
        if(not self._content.get(fileHash)):
            self._content[fileHash] = []
            # -j : json outputclear()
            # '-CreateDate', '-FileCreateDate': extract only these tags
            args = [
                '-j',
                # '-time:all',
                '-CreateDate',
                '-DateCreated',
                '-FileCreateDate',
                filePath]

            try:
                metadataDict = exifTool.get_metadata(*args)[0]

            except:  # noqa: E722
                message = "Unexpected error extracting metadata from '{0}'"
                print(message.format(filePath), sys.exc_info()[0])

            metadataDict['SourceFile'] = filePath
            metadataDict['Hash'] = fileHash
            image = Image(metadataDict)
            self._content[fileHash] = image
        else:
            metadataDict['SourceFile'] = filePath
            metadataDict['Hash'] = fileHash
            image = Image(metadataDict)
            self._content[fileHash].AddDuplicate(image)

        self.totalImageCount = self.totalImageCount + 1
        return

    def __repr__(self):
        result = ''
        for image in self._content.values():
            result += image.__repr__() + '\n'
        return result

    def SaveIndex(self, indexFile):
        with open(indexFile, "w") as of:
            for image in self._content.values():
                of.write(image.__repr__() + '\n')

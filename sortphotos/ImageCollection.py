# -*- coding: utf-8 -*-

import os
import shutil

import hashlib

from sortphotos.MetadataReader import MetadataReader
from sortphotos.Image import Image


#
# Class managing images metatas
# Each file is hashed to avoid duplicate. The collection
# contains one Image instance per hash, and that Image
# may reference 0 or more duplicate of the first-seen file
# for the given hash.
class ImageCollection(object):

    def __init__(self, metadataReader=None):
        self._metadataReader = metadataReader or MetadataReader()
        self._content = {}
        self.totalImageCount = 0

    def GetUniqueImageCount(self):
        return len(self._content)

    def RecursiveAddDirectory(self, directory, ignore_file_types=()):
        for (path, dirs, files) in os.walk(directory):
            # skip hidden directories and files (.*)
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            for file in files:
                if file.startswith('.'):
                    continue
                # ignore specified file extensions
                fileextension = os.path.splitext(file)[-1]
                fileextension = fileextension.upper().replace('.', '')
                if fileextension in map(str.upper, ignore_file_types):
                    print(fileextension + ' files ignored, "' +
                          file + '" skipped' + "\n")
                    continue
                self.AddFile(os.path.join(path, file), directory)

    def CopyInto(self,
                 targetDirectory,
                 sort_format=None,
                 copy_files=True,
                 dry_run=False):
        """
        Use the internal data structure to copy (or move) media files
        into the target directory. With dry_run, only print what
        would be done.
        """
        # destinations already used during this run, so that
        # collisions are detected even when nothing is written (dry run)
        reserved = set()
        for image in self._content.values():
            date = image.creationDate
            src_file = image._metadata['SourceFile']
            src_fileName = os.path.basename(src_file)
            dest_dir = targetDirectory

            if sort_format is not None:
                # folder structure from date
                dirs = date.strftime(sort_format).split('/')
                dest_file = os.path.join(dest_dir, *dirs, src_fileName)
            else:
                # copy the same folder structure in the target
                dest_file = os.path.join(dest_dir, image.relativePath)
            dest_file = os.path.normpath(dest_file)

            dest_file = self._ResolveDestination(
                dest_file, image._metadata['Hash'], reserved)
            if dest_file is None:
                # identical file already in target
                if dry_run:
                    print('skip {0} (already in target)'.format(src_file))
                else:
                    print("~", end='', flush=True)
                continue
            reserved.add(dest_file)

            if dry_run:
                print('{0} {1} -> {2}'.format(
                    'copy' if copy_files else 'move', src_file, dest_file))
                continue

            os.makedirs(os.path.dirname(dest_file), exist_ok=True)
            if copy_files:
                shutil.copy2(src_file, dest_file)
                print("-", end='', flush=True)
            else:
                shutil.move(src_file, dest_file)
                print("#", end='', flush=True)

    def _ResolveDestination(self, dest_file, fileHash, reserved):
        """
        Return a destination path that does not overwrite another file.
        If a file with the same name but different content exists
        (on disk or planned in this run), a suffix is appended
        (name_1.ext, name_2.ext...). Return None when an identical
        file is already there.
        """
        base, ext = os.path.splitext(dest_file)
        candidate = dest_file
        index = 0
        while True:
            if candidate not in reserved:
                if not os.path.exists(candidate):
                    return candidate
                if os.path.isfile(candidate) and \
                        self.HashFile(candidate) == fileHash:
                    return None
            index += 1
            candidate = '{0}_{1}{2}'.format(base, index, ext)

    def HashFile(self, src_file):
        hasher = hashlib.md5()
        with open(src_file, 'rb') as afile:
            # buffered read by blocks of 64k
            b = afile.read(65536)
            while len(b) > 0:
                hasher.update(b)
                b = afile.read(65536)
        return (hasher.hexdigest())

    def AddFile(self, filePath, sourceDirectory=None):
        """
        Add a file to the collection. sourceDirectory is the root the
        file was found in, used to keep the folder structure when
        copying without sort format.
        """
        if 0 == len(filePath):
            return
        fileHash = self.HashFile(filePath)
        metadataDict = dict()
        if not self._content.get(fileHash):
            try:
                metadataDict = self._metadataReader.GetMetadata(filePath)
            except Exception as e:
                message = "Unexpected error extracting metadata from '{0}': {1}"
                print(message.format(filePath, e))

            metadataDict['SourceFile'] = filePath
            metadataDict['Hash'] = fileHash
            image = Image(metadataDict)
            if sourceDirectory is not None:
                image.relativePath = os.path.relpath(filePath, sourceDirectory)
            self._content[fileHash] = image
            print('.', end='', flush=True)
        else:
            self._content[fileHash].AddDuplicate(filePath)
            print('+', end='', flush=True)

        self.totalImageCount = self.totalImageCount + 1
        return

    def __repr__(self):
        result = ''
        for image in self._content.values():
            result += image.__repr__() + '\n'
        return result

# -*- coding: utf-8 -*-

import logging
import os
from datetime import datetime

import exifread
from hachoir.core import config as hachoirConfig
from hachoir.metadata import extractMetadata
from hachoir.parser import createParser

# date format used in EXIF, and expected by Image
EXIF_DATE_FORMAT = '%Y:%m:%d %H:%M:%S'


class MetadataReader(object):
    """
    Read creation dates from media files, in pure Python:
    EXIF for photos (JPEG, TIFF, HEIC, PNG, TIFF based RAW...),
    container metadata for videos (MP4, MOV, AVI, MKV...).
    """

    # EXIF tags holding the shooting date
    exifTags = ['EXIF DateTimeOriginal', 'EXIF DateTimeDigitized']

    # QuickTime/MP4 time origin, written when no date is set
    quickTimeEpoch = datetime(1904, 1, 1)

    @staticmethod
    def QuietLibraries():
        """
        Silence warnings of the metadata libraries, printed for every
        file without metadata (which is expected)
        """
        logging.getLogger('exifread').setLevel(logging.ERROR)
        hachoirConfig.quiet = True

    def GetMetadata(self, filePath):
        """
        Return a dict of date tags, values as EXIF formatted strings
        (YYYY:MM:DD HH:MM:SS). Empty if no date could be read.
        """
        metadata = self._ReadExif(filePath)
        if not metadata:
            metadata = self._ReadMediaContainer(filePath)

        # file system creation date, where available (macOS, Windows)
        birthTime = getattr(os.stat(filePath), 'st_birthtime', None)
        if birthTime:
            metadata['FileCreateDate'] = datetime.fromtimestamp(
                birthTime).strftime(EXIF_DATE_FORMAT)
        return metadata

    def _ReadExif(self, filePath):
        try:
            with open(filePath, 'rb') as f:
                tags = exifread.process_file(f, details=False)
        except Exception:
            return {}
        return {key: str(tags[key]) for key in self.exifTags if key in tags}

    def _ReadMediaContainer(self, filePath):
        try:
            parser = createParser(filePath)
            if parser is None:
                return {}
            with parser:
                metadata = extractMetadata(parser)
        except Exception:
            return {}

        if metadata is None or not metadata.has('creation_date'):
            return {}
        creationDate = metadata.get('creation_date')
        if not isinstance(creationDate, datetime) or \
                creationDate == self.quickTimeEpoch:
            return {}
        return {'CreateDate': creationDate.strftime(EXIF_DATE_FORMAT)}

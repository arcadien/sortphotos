import unittest
import shutil
import os.path
import io
import struct
import tempfile
from contextlib import redirect_stdout
from datetime import datetime

from sortphotos.ImageCollection import ImageCollection
from sortphotos.MetadataReader import MetadataReader
from sortphotos.Image import Image

# Constants
imageFileName_1 = "81984ab0bd8e9c4079a42dcd0d739607_20210102_143116.jpg"
testDataDirectory = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test-data")

MetadataReader.QuietLibraries()


class Test_ImageCollection(unittest.TestCase):

    def test_HashFile(self):
        imageCollection = ImageCollection()
        actual = imageCollection.HashFile(self.InPath("test_HashFile.txt"))
        expected = "65b1e8826c261ee5cc0b0f9d9b8f01f2"
        self.assertEqual(actual, expected,
                         "Computation of file hash should finish and be right")

    def test_AddFile(self):
        imageCollection = ImageCollection()
        imageCollection.AddFile(self.InPath(imageFileName_1))
        imageCollection.AddFile(self.InPath(imageFileName_1))
        actual = imageCollection.GetUniqueImageCount()
        expected = 1
        self.assertEqual(
            actual, expected, "Only one image file should be processed (duplicated)")

        image = list(imageCollection._content.values())[0]
        self.assertEqual(image._duplicates, [self.InPath(imageFileName_1)],
                         "The duplicate file path should be recorded")

        actual = imageCollection.totalImageCount
        expected = 2
        self.assertEqual(actual, expected,
                         "Two image processed, with one duplicate")

    def test_AddFileWithoutMetadata(self):
        class NoMetadataReader(object):
            def GetMetadata(self, filePath):
                return {}

        imageCollection = ImageCollection(NoMetadataReader())
        imageCollection.AddFile(self.InPath("test_HashFile.txt"))
        self.assertEqual(imageCollection.GetUniqueImageCount(), 1,
                         "A file without metadata should still be added")

    def test_HiddenFilesAreIgnored(self):
        root = tempfile.mkdtemp()
        try:
            os.makedirs(os.path.join(root, '.thumbnails'))
            for name in ['.hidden.jpg', '.thumbnails/thumb.jpg', 'visible.jpg']:
                with open(os.path.join(root, name), 'w') as f:
                    f.write(name)
            imageCollection = ImageCollection()
            imageCollection.RecursiveAddDirectory(root)
            self.assertEqual(imageCollection.totalImageCount, 1,
                             "Hidden files and directories should be ignored")
        finally:
            shutil.rmtree(root)

    def test_InstancesDoNotShareContent(self):
        first = ImageCollection()
        first._content['somehash'] = None
        first.totalImageCount = 1
        second = ImageCollection()
        self.assertEqual(second.GetUniqueImageCount(), 0,
                         "A new collection should be empty")
        self.assertEqual(second.totalImageCount, 0,
                         "A new collection should have no image counted")

    @classmethod
    def setUpClass(cls):
        cls.inDirectory = tempfile.mkdtemp()
        with open(os.path.join(cls.inDirectory, "test_HashFile.txt"), "w") as f:
            f.write("This is a wonderful content")
        shutil.copyfile(os.path.join(testDataDirectory, imageFileName_1),
                        os.path.join(cls.inDirectory, imageFileName_1))

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.inDirectory)

    def InPath(self, fileName):
        return os.path.join(self.inDirectory, fileName)


class Test_ParseExifDate(unittest.TestCase):

    def test_DateWithTimeZoneIsKept(self):
        image = Image({'SourceFile': 'missing.jpg',
                       'FileCreateDate': '2021:01:02 14:31:16+01:00'})
        self.assertEqual(image.creationDate, datetime(2021, 1, 2, 14, 31, 16),
                         "A timestamp with a time zone should be parsed as local time")

    def test_TimeZoneDoesNotChangeMonth(self):
        image = Image({'SourceFile': 'missing.jpg',
                       'CreateDate': '2021:01:31 23:30:00+02:00'})
        self.assertEqual(image.creationDate, datetime(2021, 1, 31, 23, 30, 0),
                         "The time zone offset should not shift the date")

    def test_DateWithUtcSuffixIsKept(self):
        image = Image({'SourceFile': 'missing.jpg',
                       'CreateDate': '2021:01:02 14:31:16Z'})
        self.assertEqual(image.creationDate, datetime(2021, 1, 2, 14, 31, 16),
                         "A timestamp ending with Z should be parsed")

    def test_OldestDateIsUsed(self):
        image = Image({'SourceFile': 'missing.jpg',
                       'FileCreateDate': '2021:01:02 14:31:16-05:00',
                       'CreateDate': '2019:05:05 10:00:00'})
        self.assertEqual(image.creationDate, datetime(2019, 5, 5, 10, 0, 0),
                         "The oldest timestamp should be used")


class Test_CopyInto(unittest.TestCase):

    def setUp(self):
        self.root = tempfile.mkdtemp()
        self.src = os.path.join(self.root, 'src')
        self.dest = os.path.join(self.root, 'dest')
        os.makedirs(os.path.join(self.src, 'a'))
        os.makedirs(os.path.join(self.src, 'b'))
        os.makedirs(self.dest)
        self.collection = ImageCollection()
        # two different photos with the same name, same month
        self.files = [self.AddImage('a/IMG_0001.JPG', 'first photo'),
                      self.AddImage('b/IMG_0001.JPG', 'second photo')]

    def tearDown(self):
        shutil.rmtree(self.root)

    def AddImage(self, relativePath, content):
        filePath = os.path.join(self.src, relativePath)
        with open(filePath, 'w') as f:
            f.write(content)
        fileHash = self.collection.HashFile(filePath)
        self.collection._content[fileHash] = Image({
            'SourceFile': filePath,
            'Hash': fileHash,
            'CreateDate': '2021:01:02 14:31:16'})
        return filePath

    def ReadAll(self, directory):
        contents = []
        for (dirPath, dirs, files) in os.walk(directory):
            for file in files:
                with open(os.path.join(dirPath, file)) as f:
                    contents.append(f.read())
        return sorted(contents)

    def test_CopyKeepsFilesWithSameName(self):
        self.collection.CopyInto(self.dest, '%Y/%m', copy_files=True)
        self.assertEqual(self.ReadAll(self.dest),
                         ['first photo', 'second photo'],
                         "Both photos should be copied")
        self.assertTrue(all(os.path.isfile(f) for f in self.files),
                        "Sources should be kept when copying")

    def test_MoveDoesNotOverwrite(self):
        self.collection.CopyInto(self.dest, '%Y/%m', copy_files=False)
        self.assertEqual(self.ReadAll(self.dest),
                         ['first photo', 'second photo'],
                         "Both photos should be moved without overwrite")
        self.assertFalse(any(os.path.exists(f) for f in self.files),
                         "Sources should be removed when moving")

    def test_IdenticalFileInTargetIsSkipped(self):
        self.collection.CopyInto(self.dest, '%Y/%m', copy_files=True)
        self.collection.CopyInto(self.dest, '%Y/%m', copy_files=True)
        self.assertEqual(self.ReadAll(self.dest),
                         ['first photo', 'second photo'],
                         "Running twice should not create copies")

    def test_NoSortFormatKeepsSourceStructure(self):
        class NoMetadataReader(object):
            def GetMetadata(self, filePath):
                return {}

        collection = ImageCollection(NoMetadataReader())
        for filePath in self.files:
            collection.AddFile(filePath, self.src)
        collection.CopyInto(self.dest, None, copy_files=True)
        for relativePath in ['a/IMG_0001.JPG', 'b/IMG_0001.JPG']:
            self.assertTrue(
                os.path.isfile(os.path.join(self.dest, relativePath)),
                "Source structure should be kept: " + relativePath)

    def test_DryRunWritesNothing(self):
        output = io.StringIO()
        with redirect_stdout(output):
            self.collection.CopyInto(self.dest, '%Y/%m',
                                     copy_files=False, dry_run=True)
        self.assertEqual(os.listdir(self.dest), [],
                         "Dry run should not write in the target")
        self.assertTrue(all(os.path.isfile(f) for f in self.files),
                        "Dry run should not move sources")
        self.assertIn('IMG_0001_1.JPG', output.getvalue(),
                      "Dry run should report the renamed destination")


def WriteMp4(filePath, creationDate):
    """Write a minimal MP4 (ftyp + moov/mvhd) with the given creation date"""
    def box(boxType, payload):
        return struct.pack('>I', 8 + len(payload)) + boxType + payload
    seconds = int((creationDate - datetime(1904, 1, 1)).total_seconds())
    mvhd = struct.pack('>B3xIIII', 0, seconds, seconds, 600, 6000) \
        + struct.pack('>IH', 0x00010000, 0x0100) + b'\0' * 10 \
        + struct.pack('>9I', 0x10000, 0, 0, 0, 0x10000, 0, 0, 0, 0x40000000) \
        + b'\0' * 24 + struct.pack('>I', 2)
    with open(filePath, 'wb') as f:
        f.write(box(b'ftyp', b'isom\0\0\x02\0isommp41'))
        f.write(box(b'moov', box(b'mvhd', mvhd)))


class Test_MetadataReader(unittest.TestCase):

    def setUp(self):
        self.directory = tempfile.mkdtemp()
        self.reader = MetadataReader()

    def tearDown(self):
        shutil.rmtree(self.directory)

    def Dates(self, filePath):
        metadata = self.reader.GetMetadata(filePath)
        metadata.pop('FileCreateDate', None)  # depends on the platform
        return metadata

    def test_PhotoExifDates(self):
        self.assertEqual(
            self.Dates(os.path.join(testDataDirectory, imageFileName_1)),
            {'EXIF DateTimeOriginal': '2021:01:02 14:31:16',
             'EXIF DateTimeDigitized': '2021:01:02 14:31:16'},
            "EXIF shooting dates should be read from a photo")

    def test_VideoCreationDate(self):
        filePath = os.path.join(self.directory, 'video.mp4')
        WriteMp4(filePath, datetime(2019, 7, 14, 10, 20, 30))
        self.assertEqual(self.Dates(filePath),
                         {'CreateDate': '2019:07:14 10:20:30'},
                         "Creation date should be read from a video")

    def test_VideoWithoutDate(self):
        filePath = os.path.join(self.directory, 'video.mp4')
        WriteMp4(filePath, datetime(1904, 1, 1))
        self.assertEqual(self.Dates(filePath), {},
                         "An unset video date (1904 origin) should be ignored")

    def test_FileWithoutMetadata(self):
        filePath = os.path.join(self.directory, 'notes.txt')
        with open(filePath, 'w') as f:
            f.write('no metadata here')
        self.assertEqual(self.Dates(filePath), {},
                         "A file without metadata should give no date")

    def test_VideoIsSortedByCreationDate(self):
        filePath = os.path.join(self.directory, 'video.mp4')
        WriteMp4(filePath, datetime(2019, 7, 14, 10, 20, 30))
        collection = ImageCollection(self.reader)
        collection.AddFile(filePath)
        image = list(collection._content.values())[0]
        self.assertEqual(image.creationDate, datetime(2019, 7, 14, 10, 20, 30),
                         "A video should be dated from its metadata")


if __name__ == '__main__':
    unittest.main()

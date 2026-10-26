import unittest
import shutil
import os.path
import io
import tempfile
from contextlib import redirect_stdout
from datetime import datetime
from os import path

from sortphotos.ImageCollection import ImageCollection
from sortphotos.ExifTool import ExifTool
from sortphotos.Image import Image

# Constants
imageFileName_1 = "81984ab0bd8e9c4079a42dcd0d739607_20210102_143116.jpg"


class Test_ImageCollection(unittest.TestCase):

    def test_HashFile(self):
        imageCollection = ImageCollection()
        actual = imageCollection.HashFile("test-in/test_HashFile.txt")
        expected = "65b1e8826c261ee5cc0b0f9d9b8f01f2"
        self.assertEqual(actual, expected,
                         "Computation of file hash should finish and be right")

    def test_AddFile(self):
        imageCollection = ImageCollection()
        with ExifTool(verbose=0) as exiftool:
            imageCollection.AddFile("test-in/" + imageFileName_1, exiftool)
            imageCollection.AddFile("test-in/" + imageFileName_1, exiftool)
        actual = imageCollection.GetUniqueImageCount()
        expected = 1
        self.assertEqual(
            actual, expected, "Only one image file should be processed (duplicated)")

        actual = imageCollection.totalImageCount
        expected = 2
        self.assertEqual(actual, expected,
                         "Two image processed, with one duplicate")

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
        os.makedirs("test-in")
        os.makedirs("test-out")
        f = open("test-in/test_HashFile.txt", "w+")
        f.write("This is a wonderful content")
        f.close()
        shutil.copyfile("test-data/" + imageFileName_1,
                        "test-in/" + imageFileName_1)

    @classmethod
    def tearDownClass(cls):
        RemoveDir("test-in")
        RemoveDir("test-out")


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


def RemoveDir(toRemoveIfExist):
    if(path.isdir(toRemoveIfExist)):
        try:
            shutil.rmtree(toRemoveIfExist)
        except OSError as e:
            print("Error: %s : %s" % (toRemoveIfExist, e.strerror))


if __name__ == '__main__':
    unittest.main()

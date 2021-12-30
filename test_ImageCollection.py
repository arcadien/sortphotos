import unittest
import shutil
import os.path
from os import path

from sortphotos.ImageCollection import ImageCollection
from sortphotos.ExifTool import ExifTool

# Constants
imageFileName_1 = "81984ab0bd8e9c4079a42dcd0d739607_20210102_143116.jpg"


class Test_ImageCollection(unittest.TestCase):

    def test_HashFile(self):
        imageCollection = ImageCollection()
        actual = imageCollection.HashFile("test-in/test_HashFile.txt")
        expected = "65b1e8826c261ee5cc0b0f9d9b8f01f2"
        self.assertEqual(actual, expected,
                         "Computation of file hash should be a MD5 one")

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


def RemoveDir(toRemoveIfExist):
    if(path.isdir(toRemoveIfExist)):
        try:
            shutil.rmtree(toRemoveIfExist)
        except OSError as e:
            print("Error: %s : %s" % (toRemoveIfExist, e.strerror))


if __name__ == '__main__':
    unittest.main()

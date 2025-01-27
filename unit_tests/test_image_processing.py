import unittest
from detect_violations import is_valid_image

class TestImageProcessing(unittest.TestCase):
    def test_invalid_image(self):
        self.assertFalse(is_valid_image("invalid_file.txt"))

    def test_valid_image(self):
        self.assertTrue(is_valid_image("sample.jpg"))  # Ensure you have a valid image

if __name__ == '__main__':
    unittest.main()

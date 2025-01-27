import unittest
from detect_violations import is_valid_image

class TestImageProcessing(unittest.TestCase):
    def test_invalid_image(self):
        self.assertFalse(is_valid_image("invalid_file.txt"))

    def test_valid_image(self):
        self.assertTrue(is_valid_image("../images/violation_image_20241122215003_20241123-105002_AIOP_Video_image.jpeg"))  # Ensure you have a valid image

if __name__ == '__main__':
    unittest.main()

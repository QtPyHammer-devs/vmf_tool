import os
import unittest

import vmf_tool


class TestVmfMethods(unittest.TestCase):

    def setUp(self):
        self.source_filename = "tests/mapsrc/test2.vmf"
        self.vmf = vmf_tool.vmf(self.source_filename)

    def test_save_to_file(self):
        folder = os.path.dirname(self.source_filename)
        filename = os.path.basename(self.source_filename)
        save_filename = os.path.join(folder, f"test_save_{filename}")
        self.vmf.save_to_file(save_filename)
        with open(self.source_filename, "r") as source:
            source_text = source.read()
        with open(save_filename, "r") as save:
            save_text = save.read()
        os.remove(save_filename)
        self.assertEqual(source_text, save_text)

    def tearDown(self):
        del self.source_filename
        del self.vmf

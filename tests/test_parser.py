import os
import unittest

from src.parser import parse


class ParseTest(unittest.TestCase):
    def test_empty_line(self):
        self.assertEqual(parse("   "), (None, []))

    def test_command_and_arguments(self):
        self.assertEqual(parse("ls -l /etc"), ("ls", ["-l", "/etc"]))

    def test_variable_expansion(self):
        os.environ["VFS_DEMO"] = "demo"
        self.assertEqual(parse("ls $VFS_DEMO"), ("ls", ["demo"]))

    def test_unknown_variable(self):
        os.environ.pop("VFS_MISSING", None)
        self.assertEqual(parse("ls $VFS_MISSING"), ("ls", [""]))


if __name__ == "__main__":
    unittest.main()

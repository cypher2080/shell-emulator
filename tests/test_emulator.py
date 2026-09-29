import io
import os
import tempfile
import unittest

from src.errors import ExitRequest, ScriptError, VfsError
from src.main import _parse_args
from src.parser import parse
from src.shell import Shell
from src.vfs import Vfs, node_from_dict

MIN_PATH = os.path.join("tests", "data", "vfs_min.json")
FILES_PATH = os.path.join("tests", "data", "vfs_files.json")
DEEP_PATH = os.path.join("tests", "data", "vfs_deep.json")


def shell_with_output():
    stream = io.StringIO()
    return Shell(output=stream), stream


def script_file(text):
    handle, path = tempfile.mkstemp(suffix=".vsh")
    with os.fdopen(handle, "w", encoding="utf-8") as stream:
        stream.write(text)
    return path


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

    def test_lonely_dollar_is_kept(self):
        self.assertEqual(parse("ls 5$"), ("ls", ["5$"]))


class ShellTest(unittest.TestCase):
    def setUp(self):
        self.shell, self.stream = shell_with_output()

    def run_line(self, line):
        self.shell.run_line(line)
        return self.stream.getvalue()

    def test_prompt_contains_user_and_host(self):
        self.assertIn("@", self.shell.prompt())
        self.assertTrue(self.shell.prompt().endswith(":~$ "))

    def test_ls_stub(self):
        self.assertEqual(self.run_line("ls -a /tmp"), "ls -a /tmp\n")

    def test_cd_stub(self):
        self.assertEqual(self.run_line("cd /tmp"), "cd /tmp\n")

    def test_unknown_command(self):
        self.assertIn("команда не найдена", self.run_line("wat"))

    def test_bad_arguments(self):
        self.assertIn("слишком много аргументов", self.run_line("cd a b"))

    def test_exit_requests_stop(self):
        with self.assertRaises(ExitRequest):
            self.shell.execute("exit 3")


class ConfigTest(unittest.TestCase):
    def test_defaults_are_empty(self):
        args = _parse_args([])
        self.assertIsNone(args.vfs_path)
        self.assertIsNone(args.script_path)

    def test_parses_both_parameters(self):
        args = _parse_args(["--vfs", "a.json", "--script", "b.vsh"])
        self.assertEqual(args.vfs_path, "a.json")
        self.assertEqual(args.script_path, "b.vsh")

    def test_debug_output_lists_parameters(self):
        shell, stream = shell_with_output()
        shell.vfs_path = "a.json"
        shell.script_path = "b.vsh"
        shell.write_debug()
        self.assertIn("a.json", stream.getvalue())
        self.assertIn("b.vsh", stream.getvalue())

    def test_debug_output_marks_missing_parameters(self):
        shell, stream = shell_with_output()
        shell.write_debug()
        self.assertIn("<не задан>", stream.getvalue())


class ScriptTest(unittest.TestCase):
    def setUp(self):
        self.shell, self.stream = shell_with_output()

    def test_echoes_input_and_output(self):
        path = script_file("ls one\n")
        self.shell.run_script(path)
        os.unlink(path)
        self.assertIn(self.shell.prompt() + "ls one", self.stream.getvalue())
        self.assertIn("\nls one\n", self.stream.getvalue())

    def test_stops_at_first_error(self):
        path = script_file("ls one\nbad\nls three\n")
        with self.assertRaises(ScriptError):
            self.shell.run_script(path)
        os.unlink(path)
        self.assertNotIn("ls three", self.stream.getvalue())

    def test_missing_file_is_reported(self):
        with self.assertRaises(ScriptError):
            self.shell.run_script("nosuch.vsh")


class VfsTest(unittest.TestCase):
    def test_minimal_vfs(self):
        self.assertEqual(Vfs.load(MIN_PATH).root.names(), [])

    def test_several_files(self):
        root = Vfs.load(FILES_PATH).root
        self.assertEqual(
            root.names(), ["logo.bin", "notes.txt", "readme.txt"]
        )

    def test_three_levels(self):
        root = Vfs.load(DEEP_PATH).root
        docs = root.children["home"].children["user"].children["docs"]
        self.assertIn("report.txt", docs.names())

    def test_base64_content(self):
        root = Vfs.load(FILES_PATH).root
        self.assertEqual(root.children["logo.bin"].data, bytes(range(16)))

    def test_missing_image(self):
        with self.assertRaises(VfsError):
            Vfs.load("tests/data/nosuch.json")

    def test_broken_json(self):
        path = script_file('{"name": "/", "type": "dir",')
        with self.assertRaises(VfsError):
            Vfs.load(path)
        os.unlink(path)

    def test_unknown_node_type(self):
        with self.assertRaises(VfsError):
            node_from_dict({"name": "/", "type": "socket"})

    def test_invalid_base64(self):
        with self.assertRaises(VfsError):
            node_from_dict({"name": "a", "type": "file",
                            "encoding": "base64", "content": "не-base64"})


class VfsInitTest(unittest.TestCase):
    def test_replaces_tree(self):
        shell, _ = shell_with_output()
        shell.vfs = Vfs.load(DEEP_PATH)
        shell.vfs.source = None
        shell.run_line("vfs-init")
        self.assertIn("home", shell.vfs.root.names())

    def test_rejects_arguments(self):
        shell, stream = shell_with_output()
        shell.run_line("vfs-init a")
        self.assertIn("не поддерживаются", stream.getvalue())

    def test_clears_physical_image(self):
        path = script_file("{}")
        Vfs.load(DEEP_PATH)
        shell, _ = shell_with_output()
        shell.vfs = Vfs.default(path)
        shell.run_line("vfs-init")
        reloaded = Vfs.load(path)
        os.unlink(path)
        self.assertEqual(reloaded.root.names(), ["home", "tmp"])

    def test_image_is_not_modified_without_vfs_init(self):
        before = open(DEEP_PATH, encoding="utf-8").read()
        shell, _ = shell_with_output()
        shell.vfs = Vfs.load(DEEP_PATH)
        shell.run_line("ls")
        self.assertEqual(open(DEEP_PATH, encoding="utf-8").read(), before)


if __name__ == "__main__":
    unittest.main()

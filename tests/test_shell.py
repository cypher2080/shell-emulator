import io
import unittest

from src.errors import ExitRequest
from src.shell import Shell


def run(line):
    stream = io.StringIO()
    Shell(output=stream).run_line(line)
    return stream.getvalue()


class ShellTest(unittest.TestCase):
    def test_prompt_contains_user_and_host(self):
        shell = Shell(output=io.StringIO())
        self.assertIn("@", shell.prompt())
        self.assertTrue(shell.prompt().endswith(":~$ "))

    def test_ls_stub(self):
        self.assertEqual(run("ls -a /tmp"), "ls -a /tmp\n")

    def test_cd_stub(self):
        self.assertEqual(run("cd /tmp"), "cd /tmp\n")

    def test_unknown_command(self):
        self.assertIn("команда не найдена", run("wat"))

    def test_bad_arguments(self):
        self.assertIn("слишком много аргументов", run("cd a b"))

    def test_exit_requests_stop(self):
        with self.assertRaises(ExitRequest):
            Shell(output=io.StringIO()).execute("exit 3")


if __name__ == "__main__":
    unittest.main()

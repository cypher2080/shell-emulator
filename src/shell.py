import getpass
import socket
import sys

from src.commands import COMMANDS
from src.errors import CommandError, EmulatorError, ScriptError
from src.parser import parse

HOME_ALIAS = "~"
PROMPT_SUFFIX = "$ "
ERROR_PREFIX = "ошибка: "
DEBUG_PREFIX = "[debug] "
NOT_SET = "<не задан>"


class Shell:
    def __init__(self, vfs_path=None, script_path=None, output=None):
        self.vfs_path = vfs_path
        self.script_path = script_path
        self.output = output or sys.stdout
        self.user = getpass.getuser()
        self.host = socket.gethostname().split(".")[0]

    def prompt(self):
        return "{}@{}:{}{}".format(
            self.user, self.host, HOME_ALIAS, PROMPT_SUFFIX
        )

    def write(self, text):
        self.output.write(text + "\n")
        self.output.flush()

    def write_debug(self):
        self.write(DEBUG_PREFIX + "vfs    = " + _shown(self.vfs_path))
        self.write(DEBUG_PREFIX + "script = " + _shown(self.script_path))

    def execute(self, line):
        name, args = parse(line)
        if name is None:
            return
        handler = COMMANDS.get(name)
        if handler is None:
            raise CommandError(name + ": команда не найдена")
        handler(self, args)

    def run_line(self, line):
        try:
            self.execute(line)
        except EmulatorError as error:
            self.write(ERROR_PREFIX + str(error))
            return False
        return True

    def run_script(self, path):
        for number, line in _read_script(path):
            self.write(self.prompt() + line)
            if not self.run_line(line):
                raise ScriptError(
                    "{}: строка {}: выполнение остановлено".format(
                        path, number
                    )
                )

    def run(self):
        while True:
            try:
                line = input(self.prompt())
            except EOFError:
                self.write("")
                return
            self.run_line(line)


def _read_script(path):
    try:
        with open(path, encoding="utf-8") as stream:
            lines = stream.read().splitlines()
    except OSError as error:
        raise ScriptError("не удалось прочитать скрипт: " + str(error))
    return [
        (number, line.strip())
        for number, line in enumerate(lines, start=1)
        if line.strip()
    ]


def _shown(value):
    return value if value else NOT_SET

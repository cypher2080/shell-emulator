import getpass
import socket
import sys

from src.commands import COMMANDS
from src.errors import CommandError, EmulatorError
from src.parser import parse

HOME_ALIAS = "~"
PROMPT_SUFFIX = "$ "
ERROR_PREFIX = "ошибка: "


class Shell:
    def __init__(self, output=None):
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

    def run(self):
        while True:
            try:
                line = input(self.prompt())
            except EOFError:
                self.write("")
                return
            self.run_line(line)

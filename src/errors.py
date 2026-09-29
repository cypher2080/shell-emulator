class EmulatorError(Exception):
    pass


class CommandError(EmulatorError):
    pass


class ScriptError(EmulatorError):
    pass


class ExitRequest(Exception):
    def __init__(self, code=0):
        super().__init__(code)
        self.code = code

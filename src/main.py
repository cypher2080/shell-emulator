import sys

from src.errors import ExitRequest
from src.shell import Shell


def main():
    try:
        Shell().run()
    except ExitRequest as request:
        return request.code
    return 0


if __name__ == "__main__":
    sys.exit(main())

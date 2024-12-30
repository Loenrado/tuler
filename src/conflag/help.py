from dataclasses import fields
from typing import (
    List,
    Literal,
    Type,
    TYPE_CHECKING,
    get_args,
)

if TYPE_CHECKING:
    from _typeshed import DataclassInstance


def _unit_process(s, _):
    return s


def help_table[T: DataclassInstance](
    row_type: Type[T], name: str, rows: List[T] = [], indent="  ", newline="\n"
):
    if not rows:
        return

    processors = []
    maxes = []
    for f in fields(row_type):
        maxes.append(0)

        args = get_args(f.type)
        if len(args) < 2:
            processors.append(_unit_process)
        else:
            processors.append(args[1])

    for row in rows:
        for i, f in enumerate(fields(row)):
            maxes[i] = max(maxes[i], len(getattr(row, f.name)))

    ret = f"{name}:\n"
    for row in rows:
        ret += indent
        ret += " ".join(
            process(getattr(row, f.name), max)
            for f, process, max in zip(fields(row_type), processors, maxes)
        )
        ret += newline

    return ret


def process(
    just: Literal["L", "R"] = "L", pre: str = " ", post: str = " ", ansi: str = ""
):
    def __process(s: str, cs: int):
        match just:
            case "L":
                return pre + ansi + s.ljust(cs) + Colors.END + post
            case "R":
                return pre + ansi + s.rjust(cs) + Colors.END + post

    return __process


class Colors:
    BLACK = "\033[0;30m"
    RED = "\033[0;31m"
    GREEN = "\033[0;32m"
    BOLD_GREEN = "\033[1;32m"
    BROWN = "\033[0;33m"
    BLUE = "\033[0;34m"
    PURPLE = "\033[0;35m"
    CYAN = "\033[0;36m"
    LIGHT_GRAY = "\033[0;37m"
    DARK_GRAY = "\033[1;30m"
    LIGHT_RED = "\033[1;31m"
    LIGHT_GREEN = "\033[1;32m"
    YELLOW = "\033[1;33m"
    LIGHT_BLUE = "\033[1;34m"
    LIGHT_PURPLE = "\033[1;35m"
    LIGHT_CYAN = "\033[1;36m"
    LIGHT_WHITE = "\033[1;37m"
    BOLD = "\033[1m"
    FAINT = "\033[2m"
    ITALIC = "\033[3m"
    UNDERLINE = "\033[4m"
    BLINK = "\033[5m"
    NEGATIVE = "\033[7m"
    CROSSED = "\033[9m"
    END = "\033[0m"

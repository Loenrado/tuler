from dataclasses import fields
from typing import (
    List,
    Literal,
    Type,
    TYPE_CHECKING,
    get_args,
)
from colorama import Fore, Style

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
                return pre + ansi + s.ljust(cs) + Style.RESET_ALL + post
            case "R":
                return pre + ansi + s.rjust(cs) + Style.RESET_ALL + post

    return __process

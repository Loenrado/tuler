from dataclasses import dataclass, field
from typing import Annotated
from conflag import _HelpError, App, Argument, Flag, Option
import pytest


@pytest.mark.parametrize(
    "params",
    [
        ("cmd", "--verbose", "100"),
        ("--verbose", "100", "cmd"),
    ],
)
def test_global_opts(params):
    @dataclass
    class Opts:
        verbose: str = "10"

    app = App(Opts)

    is_run = False

    @app.command()
    def cmd():
        nonlocal is_run
        is_run = True

        assert app.opts.verbose == "100"

    app.run(["./foo", *params])
    assert is_run


def test_global_opts_no_defaults_err():
    @dataclass
    class Opts:
        beans: bool
        verbose: str

    with pytest.raises(_HelpError):
        App(Opts)

from typing import Annotated
from conflag import _HelpError, App, Argument, Flag, Option
import pytest


def test_command_with_no_args():
    app = App()

    is_run = False

    @app.command()
    def cmd():
        nonlocal is_run
        is_run = True

    app.run(["./foo", "cmd"])
    assert is_run


def test_command_with_arg():
    app = App()

    is_run = False

    @app.command()
    def cmd(x):
        nonlocal is_run
        is_run = True

        assert x == "bar"

    app.run(["./foo", "cmd", "bar"])
    assert is_run


def test_command_with_args():
    app = App()

    is_run = False

    @app.command()
    def cmd(x, y):
        nonlocal is_run
        is_run = True

        assert x == "bar"
        assert y == "bazz"

    app.run(["./foo", "cmd", "bar", "bazz"])
    assert is_run


@pytest.mark.parametrize("params", [("--x", "15"), ("--x=15",)])
def test_command_with_opt(params):
    app = App()

    is_run = False

    @app.command()
    def cmd(x="12"):
        nonlocal is_run
        is_run = True

        assert x == "15"

    app.run(["./foo", "cmd", *params])
    assert is_run


@pytest.mark.parametrize(
    "params",
    [("--x", "15", "--y", "25"), ("--y=25", "--x=15"), ("--y", "25", "--x", "15")],
)
def test_command_with_opts(params):
    app = App()

    is_run = False

    @app.command()
    def cmd(x="12", y="13"):
        nonlocal is_run
        is_run = True

        assert x == "15"
        assert y == "25"

    app.run(["./foo", "cmd", *params])
    assert is_run


@pytest.mark.parametrize(
    "params", [("15", "--y", "25"), ("--y=25", "15"), ("--y", "25", "15")]
)
def test_command_with_arg_and_opt(params):
    app = App()

    is_run = False

    @app.command()
    def cmd(x, y="13"):
        nonlocal is_run
        is_run = True

        assert x == "15"
        assert y == "25"

    app.run(["./foo", "cmd", *params])
    assert is_run


@pytest.mark.parametrize(
    "params",
    [
        ("15", "25", "--a", "bazz", "--b", "buzz"),
        ("15", "--a", "bazz", "25", "--b", "buzz"),
        ("--b=buzz", "15", "--a", "bazz", "25"),
    ],
)
def test_command_with_args_and_opts(params):
    app = App()

    is_run = False

    @app.command()
    def cmd(x, y, a="foo", b="bar"):
        nonlocal is_run
        is_run = True

        assert x == "15"
        assert y == "25"
        assert a == "bazz"
        assert b == "buzz"

    app.run(["./foo", "cmd", *params])
    assert is_run


@pytest.mark.parametrize(
    "params",
    [
        ("15", "25", "35", "--a", "bazz", "--b", "buzz"),
        ("--b=buzz", "15", "--a", "bazz"),
        ("15", "--a", "bazz", "25", "--b", "buzz", "--c"),
    ],
    ids=[
        "too_many_args",
        "not_enough_args",
        "option_does_not_exist",
    ],
)
def test_command_with_args_and_opts_err(params):
    app = App()

    @app.command()
    def cmd(x, y, a="foo", b="bar"):
        pass

    with pytest.raises(_HelpError):
        app.run(["./foo", "cmd", *params], catch_help=False)


def test_with_no_command():
    app = App()

    @app.command()
    def cmd(x, y, a="foo", b="bar"):
        pass

    with pytest.raises(_HelpError):
        app.run(["./foo"], catch_help=False)


def test_with_no_available_commands():
    app = App()

    with pytest.raises(_HelpError):
        app.run(["./foo"], catch_help=False)


def test_command_with_options_not_set():
    app = App()

    is_run = False

    @app.command()
    def cmd(x, y, a="foo", b="bar"):
        nonlocal is_run
        is_run = True

        assert x == "X"
        assert y == "Y"
        assert a == "foo"
        assert b == "bar"

    app.run(["./foo", "cmd", "X", "Y"])
    assert is_run


def test_command_with_name():
    app = App()

    is_run = False

    @app.command(name="command")
    def cmd(x, y, a="foo", b="bar"):
        nonlocal is_run
        is_run = True

        assert x == "X"
        assert y == "Y"
        assert a == "foo"
        assert b == "bar"

    app.run(["./foo", "command", "X", "Y"])
    assert is_run


def test_command_with_name_err():
    app = App()

    @app.command(name="command")
    def cmd(x, y, a="foo", b="bar"):
        print("HERE")

    with pytest.raises(_HelpError):
        app.run(["./foo", "cmd", "X", "Y"], catch_help=False)


@pytest.mark.parametrize(
    "params, expected",
    [
        (("cmd_a", "X"), (True, False)),
        (("cmd_b", "X", "Y"), (False, True)),
    ],
    ids=["cmd_a", "cmd_b"],
)
def test_commands(params, expected):
    app = App()

    a_is_run = False
    b_is_run = False

    @app.command()
    def cmd_a(x):
        nonlocal a_is_run
        a_is_run = True

        assert x == "X"

    @app.command()
    def cmd_b(x, y):
        nonlocal b_is_run
        b_is_run = True

        assert x == "X"
        assert y == "Y"

    app.run(["./foo", *params])
    assert a_is_run == expected[0]
    assert b_is_run == expected[1]


def test_command_argument_format_name():
    app = App()

    is_run = False

    @app.command()
    def cmd(longer_name):
        nonlocal is_run
        is_run = True

        assert longer_name == "bones"

    app.run(["./foo", "cmd", "bones"])
    assert is_run


def test_command_argument_with_no_name():
    app = App()

    is_run = False

    @app.command()
    def cmd(longer_name: Annotated[str, Argument()]):
        nonlocal is_run
        is_run = True

        assert longer_name == "bones"

    app.run(["./foo", "cmd", "bones"])
    assert is_run


def test_command_option_format_name():
    app = App()

    is_run = False

    @app.command()
    def cmd(longer_name="buns"):
        nonlocal is_run
        is_run = True

        assert longer_name == "bones"

    app.run(["./foo", "cmd", "--longer-name", "bones"])
    assert is_run


def test_command_with_opt_default_not_set_err():
    app = App()

    with pytest.raises(_HelpError):

        @app.command()
        def cmd(longer_name: Annotated[str, Option()]):
            pass


@pytest.mark.parametrize(
    "params",
    [
        ("-lbones",),
        ("-l", "bones"),
    ],
)
def test_command_with_short_option(params):
    app = App()

    is_run = False

    @app.command()
    def cmd(longer_name: Annotated[str, Option(short_name="l")] = "buns"):
        nonlocal is_run
        is_run = True

        assert longer_name == "bones"

    app.run(["./foo", "cmd", *params])
    assert is_run


@pytest.mark.parametrize(
    "params, expected",
    [
        (("--longer-name",), True),
        (("--no-longer-name",), False),
    ],
)
def test_command_with_implicit_flag(params, expected):
    app = App()

    is_run = False

    @app.command()
    def cmd(longer_name: bool = False):
        nonlocal is_run
        is_run = True

        assert longer_name == expected

    app.run(["./foo", "cmd", *params])
    assert is_run


def test_command_with_flag_err():
    app = App()

    @app.command()
    def cmd(longer_name: bool = False):
        pass

    with pytest.raises(_HelpError):
        app.run(["./foo", "cmd", "--longer_name"], catch_help=False)


@pytest.mark.parametrize(
    "params, expected",
    [
        (("--boomp",), True),
        (("--zoomp-boomp",), False),
        (("-b",), True),
    ],
)
def test_command_with_flag_with_custom_naming(params, expected):
    app = App()

    is_run = False

    @app.command()
    def cmd(
        longer_name: Annotated[
            bool, Flag(name="boomp", negated_prefix="zoomp", short_name="b")
        ] = False,
    ):
        nonlocal is_run
        is_run = True

        assert longer_name == expected

    app.run(["./foo", "cmd", *params])
    assert is_run


def test_command_with_arg_parser():
    app = App()

    is_run = False

    @app.command()
    def cmd(
        longer_name: Annotated[
            int,
            Argument(name="boomp", parser=int),
        ],
    ):
        nonlocal is_run
        is_run = True

        assert longer_name == 120

    app.run(["./foo", "cmd", "120"])
    assert is_run


def test_command_with_arg_parser_and_validator():
    app = App()

    is_run = False

    @app.command()
    def cmd(
        longer_name: Annotated[
            int,
            Argument(name="boomp", parser=int, validator=lambda x: x > 100),
        ],
    ):
        nonlocal is_run
        is_run = True

        assert longer_name == 120

    app.run(["./foo", "cmd", "120"])
    assert is_run


def test_command_with_arg_validator():
    app = App()

    is_run = False

    @app.command()
    def cmd(
        longer_name: Annotated[
            int,
            Argument(name="boomp", validator=lambda x: x in ("zeeb", "zoob")),
        ],
    ):
        nonlocal is_run
        is_run = True

        assert longer_name == "zeeb"

    app.run(["./foo", "cmd", "zeeb"])
    assert is_run


def test_command_with_arg_validator_err():
    app = App()

    @app.command()
    def cmd(
        longer_name: Annotated[
            int,
            Argument(name="boomp", validator=lambda x: x in ("zeeb", "zoob")),
        ],
    ):
        pass

    with pytest.raises(_HelpError):
        app.run(["./foo", "cmd", "differente"], catch_help=False)


def test_command_with_arg_parser_and_validator_err():
    app = App()

    @app.command()
    def cmd(
        longer_name: Annotated[
            int,
            Argument(name="boomp", parser=int, validator=lambda x: x > 100),
        ],
    ):
        pass

    with pytest.raises(_HelpError):
        app.run(["./foo", "cmd", "99"], catch_help=False)


def test_command_with_opt_parser_and_validator():
    app = App()

    is_run = False

    @app.command()
    def cmd(
        longer_name: Annotated[
            int,
            Option(name="boomp", parser=int, validator=lambda x: x > 100),
        ] = 110,
    ):
        nonlocal is_run
        is_run = True

        assert longer_name == 120

    app.run(["./foo", "cmd", "--boomp", "120"])
    assert is_run


def test_command_with_opt_validator():
    app = App()

    is_run = False

    @app.command()
    def cmd(
        longer_name: Annotated[
            str,
            Option(name="boomp", validator=lambda x: x in ("kazoo", "kozoo")),
        ] = "kozoo",
    ):
        nonlocal is_run
        is_run = True

        assert longer_name == "kazoo"

    app.run(["./foo", "cmd", "--boomp=kazoo"])
    assert is_run


def test_command_with_opt_validator_err():
    app = App()

    @app.command()
    def cmd(
        longer_name: Annotated[
            str,
            Option(name="boomp", validator=lambda x: x in ("bean", "bone")),
        ] = "bean",
    ):
        pass

    with pytest.raises(_HelpError):
        app.run(["./foo", "cmd", "--boomp", "bonee"], catch_help=False)


def test_command_with_opt_parser_and_validator_err():
    app = App()

    @app.command()
    def cmd(
        longer_name: Annotated[
            int,
            Option(name="boomp", parser=int, validator=lambda x: x > 100),
        ] = 101,
    ):
        pass

    with pytest.raises(_HelpError):
        app.run(["./foo", "cmd", "--boomp", "99"], catch_help=False)


def test_command_with_opt_parser():
    app = App()

    is_run = False

    @app.command()
    def cmd(
        longer_name: Annotated[
            int,
            Option(name="boomp", parser=int),
        ] = 100000,
    ):
        nonlocal is_run
        is_run = True

        assert longer_name == 120

    app.run(["./foo", "cmd", "--boomp", "120"])
    assert is_run


@pytest.mark.parametrize(
    "params", [("--help",), ("cmd", "--help")], ids=["base_help", "cmd_help"]
)
def test_help_flag(params):
    app = App()

    @app.command()
    def cmd(
        longer_name: Annotated[
            int,
            Option(name="boomp", parser=int),
        ] = 100000,
    ):
        pass

    with pytest.raises(_HelpError):
        app.run(["./foo", *params], catch_help=False)


@pytest.mark.parametrize(
    "params",
    [("--longer-name=something",), ("--no-longer-name=true",), ("-lno",)],
    ids=["true_flag", "false_flag", "short_flag"],
)
def test_value_not_allowed_for_flag(params):
    app = App()

    @app.command()
    def cmd(
        longer_name: Annotated[bool, Flag(short_name="l")] = True,
    ):
        pass

    with pytest.raises(_HelpError):
        app.run(["./foo", "cmd", *params], catch_help=False)

import pytest
from conflag import App, _HelpError


@pytest.mark.parametrize(
    "params",
    [
        tuple(),
        ("sub",),
    ],
    ids=[
        "no_subapp",
        "subapp",
    ],
)
def test_subapp_with_no_commands_available(params):
    app = App()
    sub = app.subapp("sub")

    with pytest.raises(_HelpError):
        app.run(["./foo", *params], catch_help=False)


@pytest.mark.parametrize(
    "params",
    [
        tuple(),
        ("sub",),
    ],
    ids=[
        "no_subapp",
        "subapp",
    ],
)
def test_subapp_with_no_commands(params):
    app = App()
    sub = app.subapp("sub")

    @sub.command()
    def cmd():
        pass

    with pytest.raises(_HelpError):
        app.run(["./foo", *params], catch_help=False)


@pytest.mark.parametrize(
    "params, expected",
    [
        (("global_cmd",), (True, False)),
        (("sub", "cmd"), (False, True)),
    ],
    ids=[
        "no_subapp",
        "subapp",
    ],
)
def test_subapp_with_commands(params, expected):
    app = App()

    global_is_run = False
    cmd_is_run = False

    @app.command()
    def global_cmd():
        nonlocal global_is_run
        global_is_run = True

    sub = app.subapp("sub")

    @sub.command()
    def cmd():
        nonlocal cmd_is_run
        cmd_is_run = True

    app.run(["./foo", *params])
    assert global_is_run == expected[0]
    assert cmd_is_run == expected[1]


@pytest.mark.parametrize(
    "params",
    [
        ("global_cmd", "--help"),
        ("sub", "cmd", "--help"),
    ],
    ids=[
        "no_subapp",
        "subapp",
    ],
)
def test_subapp_with_help(params):
    app = App()

    @app.command()
    def global_cmd(x):
        pass

    sub = app.subapp("sub")

    @sub.command()
    def cmd(y):
        pass

    with pytest.raises(_HelpError):
        app.run(["./foo", *params], catch_help=False)

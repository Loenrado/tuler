from dataclasses import MISSING, dataclass, field, fields
from inspect import signature
from io import FileIO
import sys
from typing import (
    Annotated,
    Any,
    Callable,
    Dict,
    Generator,
    List,
    Type,
    cast,
    get_args,
    TYPE_CHECKING,
)
import tomllib

from conflag.help import Colors, help_table, process

if TYPE_CHECKING:
    from _typeshed import DataclassInstance


HELP_BREAK = "\n" * 2


@dataclass
class _HelpError(Exception):
    help_message: str
    _help_sections: List[str | None] = field(init=False, default_factory=list)
    _usage_attached: bool = field(init=False, default=False)

    def print(self):
        return HELP_BREAK.join(
            msg for msg in (self.help_message, *self._help_sections) if msg is not None
        )


_Helper = Callable[[Any], List[str | None]]


def _attach_helpers(usage: _Helper, options: _Helper):
    def decorator(func):
        def wrapper(*args, **kwargs):
            self = args[0]
            try:
                return func(*args, **kwargs)
            except _HelpError as e:
                if not e._usage_attached:
                    e._help_sections += usage(self)
                    e._usage_attached = True
                e._help_sections += options(self)
                raise

        return wrapper

    return decorator


@dataclass
class _LongOption:
    name: str
    value: str | None


@dataclass
class _ShortOption:
    name: str
    value: str | None


@dataclass
class _HelpOption:
    short_name: Annotated[str, process(ansi=Colors.BOLD_GREEN)]
    names: Annotated[str, process(just="L", post="\t", ansi=Colors.BOLD_GREEN)]
    hint: Annotated[str, process(just="L")]
    default: Annotated[str, process(just="R", ansi=Colors.BOLD)]


@dataclass
class Option[T]:
    _field_name: str = field(init=False, default="")
    _default: T = field(init=False, default=cast(T, ""))

    name: str | None = None
    short_name: str | None = None
    hint: str | None = None
    parser: Callable[[str], T] | None = None
    validator: Callable[[T], bool] | None = None

    def _help(self) -> _HelpOption:
        return _HelpOption(
            f"-{self.short_name}" if self.short_name is not None else "",
            f"--{self.name}",
            self.hint if self.hint is not None else "",
            f"[default: {repr(self._default)}]",
        )

    def _parse(self, x: str) -> T:
        if self.parser is not None:
            y = self.parser(x)
        else:
            y = cast(T, x)

        if self.validator is not None:
            if not self.validator(y):
                raise _HelpError("Option did not pass validation!")

        return y

    @staticmethod
    def _format_name(name: str):
        return name.replace("_", "-")


@dataclass
class Flag:
    _field_name: str = field(init=False, default="")
    _default: bool = field(init=False, default=False)

    name: str | None = None
    negated_prefix: str = "no"
    short_name: str | None = None
    hint: str | None = None

    def _help(self) -> _HelpOption:
        return _HelpOption(
            f"-{self.short_name}" if self.short_name is not None else "",
            f"--[{self.negated_prefix}-]{self.name}",
            self.hint if self.hint is not None else "",
            f"[default: {self.name if self._default else self.negated_name}]",
        )

    @property
    def negated_name(self):
        return f"{self.negated_prefix}-{self.name}"


@dataclass
class _HelpArgument:
    name: Annotated[str, process(post="\t", ansi=Colors.BOLD_GREEN)]
    hint: Annotated[str, process(just="L")]


@dataclass
class Argument[T]:
    name: str | None = None
    hint: str | None = None
    parser: Callable[[str], T] | None = None
    validator: Callable[[T], bool] | None = None

    def _help(self) -> _HelpArgument:
        assert self.name is not None
        return _HelpArgument(
            f"<{self.name}>", self.hint if self.hint is not None else ""
        )

    def _parse(self, x: str) -> T:
        if self.parser is not None:
            y = self.parser(x)
        else:
            y = cast(T, x)

        if self.validator is not None:
            if not self.validator(y):
                raise _HelpError("Option did not pass validation!")

        return y

    @staticmethod
    def _format_name(name: str):
        return name.replace("_", "-").upper()


OptionParser = Callable[[_LongOption | _ShortOption, Generator[str, None, None]], bool]


def _option_name_type(token: str) -> _LongOption | _ShortOption | None:
    if token[:2] == "--":
        s = token[2:].split("=")
        return _LongOption(s[0], "=".join(s[1:]) if len(s) > 1 else None)
    elif token[:1] == "-":
        return _ShortOption(token[1], token[2:] if len(token) > 2 else None)


@dataclass
class _HelpCommand:
    name: Annotated[str, process(post="\t", ansi=Colors.BOLD_GREEN)]
    hint: Annotated[str, process(just="R")]


@dataclass
class _Command:
    name: str
    func: Callable
    hint: str | None
    path: Callable[[], List[str]]
    config_options: Dict[str, Any]

    _argument_register: List[Argument] = field(init=False, default_factory=list)
    _option_register: List[Option | Flag] = field(init=False, default_factory=list)

    def __post_init__(self):
        self._fill_registers()

    def _help_oneline(self) -> _HelpCommand:
        return _HelpCommand(self.name, self.hint if self.hint is not None else "")

    def _help_usage(self):
        return [
            " ".join(
                [
                    "USAGE:",
                    " ".join(self.path()),
                    "<ARGUMENTS> [OPTIONS]",
                ]
            ),
            help_table(
                _HelpArgument,
                "ARGUMENTS",
                [arg._help() for arg in self._argument_register],
            ),
        ]

    def _help_options(self):
        return [
            help_table(
                _HelpOption,
                f"{self.name.upper()} OPTIONS",
                [opt._help() for opt in self._option_register],
            )
        ]

    def _fill_registers(self):
        sig = signature(self.func)
        for name, param in sig.parameters.items():
            for arg in get_args(param.annotation):
                match arg:
                    case Argument():
                        if arg.name is None:
                            arg.name = Argument._format_name(name)
                        self._argument_register.append(arg)
                        break
                    case Option() | Flag():
                        if param.default is param.empty:
                            raise _HelpError(
                                "A command option must have a default value."
                            )
                        arg._default = param.default
                        arg._field_name = name
                        if arg.name is None:
                            arg.name = Option._format_name(name)
                        self._option_register.append(arg)
                        break
            else:
                if param.default is param.empty:
                    self._argument_register.append(
                        Argument(Argument._format_name(name))
                    )
                else:
                    if isinstance(param.default, bool):
                        option = Flag(Option._format_name(name))
                    else:
                        option = Option(Option._format_name(name))
                    option._field_name = name
                    option._default = param.default
                    self._option_register.append(option)

    def _parse_token(
        self,
        token: str,
        g: Generator[str, None, None],
        *option_parsers: OptionParser,
    ):
        # token can be an option
        if (opt_name_type := _option_name_type(token)) is not None:
            if self._parse_option(opt_name_type, g):
                return
            for option_parser in option_parsers:
                if option_parser(opt_name_type, g):
                    return
            raise _HelpError("unable to parse option")

        # token must be an argument
        if len(self._args) >= len(self._argument_register):
            raise _HelpError("Command received too many tokens.")

        argument = self._argument_register[len(self._args)]
        self._args.append(argument._parse(token))

    def _parse_option(
        self,
        opt_name_type: _LongOption | _ShortOption,
        g: Generator[str, None, None],
    ):
        match opt_name_type:
            case _LongOption("help", _):
                raise _HelpError("Help flag.")

        for opt in self._option_register:
            match opt_name_type, opt:
                case _LongOption(name, value), Option():
                    if opt.name == name:
                        self._opts[opt._field_name] = opt._parse(
                            next(g) if value is None else value
                        )
                        return True
                case _LongOption(name, value), Flag():
                    if opt.name == name:
                        if value is not None:
                            raise _HelpError("Value not allowed for a flag.")
                        self._opts[opt._field_name] = True
                        return True
                    if opt.negated_name == name:
                        if value is not None:
                            raise _HelpError("Value not allowed for a flag.")
                        self._opts[opt._field_name] = False
                        return True
                case _ShortOption(name, value), Option():
                    if opt.short_name == name:
                        self._opts[opt._field_name] = opt._parse(
                            next(g) if value is None else value
                        )
                        return True
                case _ShortOption(name, value), Flag():
                    if opt.short_name == name:
                        if value is not None:
                            raise _HelpError("Value not allowed for a flag.")
                        self._opts[opt._field_name] = True
                        return True

        return False

    def _handle_config_options(self):
        for opt_name, value in self.config_options.items():
            if isinstance(value, dict):
                continue

            for opt in self._option_register:
                match opt:
                    case Option():
                        if opt.name == opt_name:
                            self._opts[opt._field_name] = opt._parse(value)
                    case Flag():
                        if opt.name == opt_name:
                            if value.lower() not in ("yes", "true", "no", "false"):
                                raise _HelpError(
                                    "Flag values must be either "
                                    "'yes', 'true', 'no', 'false' (case insensitive)"
                                )
                            self._opts[opt._field_name] = (
                                value.lower() in ("yes", "true"),
                            )

    @_attach_helpers(_help_usage, _help_options)
    def run(
        self,
        g: Generator[str, None, None],
        *option_parsers: OptionParser,
    ):
        self._args = []
        self._opts = {}

        self._handle_config_options()

        for token in g:
            self._parse_token(token, g, *option_parsers)

        try:
            self.func(*self._args, **self._opts)
        except TypeError:
            raise _HelpError("Something went wrong calling function!")


@dataclass
class App[T: DataclassInstance]:
    option_template: Type[T] | None = None
    hint: str | None = None
    config_file: str | FileIO | None = None

    opts: T = field(init=False)

    _name: str = field(init=False)
    _path: List[str] = field(init=False, default_factory=list)

    _option_register: List[Option | Flag] = field(init=False, default_factory=list)
    _command_register: List[_Command] = field(init=False, default_factory=list)
    _subapp_register: List["App"] = field(init=False, default_factory=list)

    _config_options: Dict[str, Any] = field(init=False, default_factory=dict)

    def __post_init__(self):
        self._register_options()
        self._handle_config_file()

    def _handle_config_file(self):
        match self.config_file:
            case FileIO():
                self._config_options = tomllib.load(self.config_file)
            case str():
                with open(self.config_file, "rb") as f:
                    self._config_options = tomllib.load(f)

    def _parse_config_options(self):
        for opt_name, value in self._config_options.items():
            if isinstance(value, dict):
                continue

            for opt in self._option_register:
                match opt:
                    case Option():
                        if opt.name == opt_name:
                            setattr(
                                self.opts, opt._field_name, opt._parse(cast(Any, value))
                            )
                    case Flag():
                        if opt.name == opt_name:
                            if not isinstance(value, bool):
                                raise _HelpError(
                                    "Flag option must be set with a boolean."
                                )
                            setattr(self.opts, opt._field_name, value)

    def _help_oneline(self) -> _HelpCommand:
        return _HelpCommand(
            getattr(self, "_name", ""),
            self.hint if self.hint is not None else "",
        )

    def _help_usage(self):
        return [
            " ".join(
                [
                    "USAGE:",
                    " ".join(self._path),
                    "<COMMAND> [OPTIONS]",
                ]
            ),
            help_table(
                _HelpCommand,
                "COMMANDS",
                [cmd._help_oneline() for cmd in self._command_register]
                + [sub._help_oneline() for sub in self._subapp_register],
            ),
        ]

    def _help_options(self):
        return [
            help_table(
                _HelpOption,
                "OPTIONS",
                [opt._help() for opt in self._option_register],
            )
        ]

    @_attach_helpers(_help_usage, _help_options)
    def command(self, name: str | None = None, hint: str | None = None):
        def _register_command(func):
            n = name if name is not None else func.__name__
            self._command_register.append(
                _Command(
                    n,
                    func,
                    hint,
                    lambda: self._path + [n],
                    self._config_options.get(n, dict()),
                )
            )

            def wrapper(*args, **kwargs):
                func(*args, **kwargs)

            return wrapper

        return _register_command

    def subapp[S: DataclassInstance](
        self,
        name: str,
        option_template: Type[S] | None = None,
    ):
        sub = App(option_template)
        sub._name = name
        sub._path = self._path + [name]
        sub._config_options = self._config_options.get(name, dict())
        self._subapp_register.append(sub)
        return sub

    def run(self, argv=sys.argv, catch_help=True):
        self._path = [argv[0]]
        g = (arg for arg in argv[1:])
        try:
            self._run(g)
        except _HelpError as e:
            print(e.print())

            if not catch_help:
                raise

    @_attach_helpers(_help_usage, _help_options)
    def _run(
        self,
        g: Generator[str, None, None],
        *option_parsers: OptionParser,
    ):
        if self.option_template is not None:
            try:
                self.opts = self.option_template()
            except TypeError:
                raise _HelpError(
                    "All fields of the option template must have a default."
                )

        self._parse_config_options()

        for token in g:
            if self._parse_token(token, g, *option_parsers):
                return

        raise _HelpError("No command run.")

    def _register_options(self):
        if self.option_template is None:
            return

        for f in fields(self.option_template):
            for option in get_args(f.type):
                if not isinstance(option, Option | Flag):
                    continue

                option._field_name = f.name

                if f.default is not MISSING:
                    option._default = f.default
                elif f.default_factory is not MISSING:
                    option._default = f.default_factory()
                else:
                    raise _HelpError("All options must have a default value.")

                if option.name is None:
                    option.name = Option._format_name(f.name)
                self._option_register.append(option)
                break
            else:
                if f.type is bool:
                    option = Flag(name=Option._format_name(f.name))
                else:
                    option = Option(name=Option._format_name(f.name))
                option._field_name = f.name

                if f.default is not MISSING:
                    option._default = f.default
                elif f.default_factory is not MISSING:
                    option._default = f.default_factory()
                else:
                    raise _HelpError("All options must have a default value.")

                self._option_register.append(option)

    def _parse_token(
        self,
        token: str,
        g: Generator[str, None, None],
        *option_parsers: OptionParser,
    ):
        # token can be an option
        if (opt_name_type := _option_name_type(token)) is not None:
            if self._parse_option(opt_name_type, g):
                return False
            for option_parser in option_parsers:
                if option_parser(opt_name_type, g):
                    return False
            raise _HelpError("Option not found.")

        # token can be a command
        for cmd in self._command_register:
            if cmd.name == token:
                cmd.run(g, self._parse_option, *option_parsers)
                return True

        # token can be a subapp
        for subapp in self._subapp_register:
            if subapp._name == token:
                subapp._run(g, self._parse_option, *option_parsers)
                return True

        raise _HelpError(f"Token {token} not found.")

    def _parse_option(
        self,
        opt_name_type: _LongOption | _ShortOption,
        g: Generator[str, None, None],
    ):
        match opt_name_type:
            case _LongOption("help", _):
                raise _HelpError("Help flag.")

        for opt in self._option_register:
            assert opt.name is not None

            match (opt_name_type, opt):
                case _LongOption(name, value), Option():
                    if opt.name == name:
                        setattr(
                            self.opts,
                            opt._field_name,
                            opt._parse(next(g) if value is None else value),
                        )
                        return True
                case _LongOption(name, value), Flag():
                    if opt.name == name:
                        if value is not None:
                            raise _HelpError("Value not allowed for a flag.")
                        setattr(self.opts, opt._field_name, True)
                        return True
                    if opt.negated_name == name:
                        if value is not None:
                            raise _HelpError("Value not allowed for a flag.")
                        setattr(self.opts, opt._field_name, False)
                        return True
                case _ShortOption(name, value), Option():
                    if opt.short_name is not None and opt.short_name == name:
                        setattr(
                            self.opts,
                            opt._field_name,
                            opt._parse(next(g) if value is None else value),
                        )
                        return True
                case _ShortOption(name, value), Flag():
                    if opt.short_name is not None and opt.short_name == name:
                        if value is not None:
                            raise _HelpError("Value not allowed for a flag.")
                        setattr(self.opts, opt._field_name, True)
                        return True

        return False

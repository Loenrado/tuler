# Tuler
__A tool for building python CLIs__

# What does it do?
Tuler is heavily inspired by Typer, another CLI tool, with a few key differences.

Here is the basic pattern for Tuler.
```python
from tuler import App

app = App()

@app.command()
def greet_friend():
    print("hey friend!")

if __name__ == "__main__":
    app.run()
```

```console
$ python3 foo.py greet_friend
hey friend!
```


`@app.command()` registers `greet_friend` as a command in `app`. `app.run()` will parse `sys.argv` and either run `greet_friend()` or display a help message.

You can register multiple commands that use arguments and options.
```python
from tuler import App

app = App()

@app.command()
def greet_friend(name):
    print(f"hey {name}!")

@app.command()
def greet_with_message(name, message="my friend!"):
    print(f"hello {name}, {message}")

if __name__ == "__main__":
    app.run()
```

```console
$ python3 foo.py greet_friend Leo
hey Leo!
$ python3 foo.py greet_with_message Mark --message "a handshake is available on request."
hello Mark, a handshake is available on request.
```

You also get a built in help screen.
```console
$ python3 foo.py --help

USAGE: foo.py <COMMAND> [OPTIONS]

COMMANDS:
   greet_friend
   greet_with_message
```

```console
$ python3 foo.py greet_friend --help

USAGE: src/demo2.py greet_with_message <ARGUMENTS> [OPTIONS]

ARGUMENTS:
   <NAME>


GREET_WITH_MESSAGE OPTIONS:
      --message      [default: 'you fool!']
```

Tuler handles global options by using templates.
```python
from tuler import App
from dataclasses import dataclass

@dataclass
class GlobalOptionsTemplate:
    verbose: bool = False
    directory: str = "/"

app = App(GlobalOptionsTemplate)

@app.command()
def print_global_opts():
    print("verbose:", app.opts.verbose)
    print("directory:", app.opts.directory)

if __name__ == "__main__":
    app.run()
```
```console
$ python3 foo.py print_global_opts
verbose: False
directory: /

$ python3 foo.py print_global_opts --verbose --directory "/dev/"
verbose: True
directory: /dev/
```

A template is a dataclass that lays out options via fields. All fields must have default values. When a template is passed into App(), app.opts is the initialized template dataclass with the values of your options.

Arguments and options can be annotated to include additional metadata.
```python
from dataclasses import dataclass
from typing import Annotated
from tuler import App, Argument, Flag, Option

@dataclass
class GlobalOptionsTemplate:
    verbose: Annotated[
        bool,
        Flag(
            short_name="v",
            hint="How much output should the program produce",
        ),
    ] = False
    directory: Annotated[
        str,
        Option(
            short_name="d",
            hint="Which directory to print.",
        ),
    ] = "/"

app = App(GlobalOptionsTemplate)

@app.command()
def magic(
    x: Annotated[
        int,
        Argument(
            hint="Magical argument",
            parser=int,
            validator=lambda v: v > 100,
        ),
    ],
):
    print(x)

if __name__ == "__main__":
    app.run()
```

```console
$ python3 foo.py --help
USAGE: foo.py <COMMAND> [OPTIONS]

COMMANDS:
   magic
 

OPTIONS:
   -v   --[no-]verbose    How much output should the program produce   [default: no-verbose]
   -d   --directory       Which directory to print.                           [default: '/']

$ python3 foo.py magic --help
USAGE: foo.py magic <ARGUMENTS> [OPTIONS]

ARGUMENTS:
   <X>    Magical number that must be greater than 100


OPTIONS:
   -v   --[no-]verbose    How much output should the program produce   [default: no-verbose]
   -d   --directory       Which directory to print.                           [default: '/']

$ python3 foo.py magic 50
Argument <X> did not pass validation!
```

You can also pass in a configuration toml file to App().
```python
from tuler import App
from dataclasses import dataclass

@dataclass
class Options:
    verbose: bool = False
    foo: str = "bar"

app = App(config_file="config.toml")

@app.command()
def greet_friend(name):
    print(f"hey {name}!")

@app.command()
def greet_with_message(name, message="my friend!"):
    print(f"hello {name}, {message}")

if __name__ == "__main__":
    app.run()
```
_config.toml:_
```toml
verbose = true
foo = "bazz"

[greet_with_message]
message = "from config!"
```

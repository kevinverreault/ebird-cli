import argparse


class _RaisingArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        raise argparse.ArgumentError(None, message)


class CliArgumentParser:
    def __init__(self):
        self.parser = _RaisingArgumentParser()
        self.positional_args = []
        self.flag_args = []

    def add_positional_argument(self, *args, **kwargs):
        if "choices" in kwargs:
            self.positional_args.extend(kwargs["choices"])
        self.parser.add_argument(*args, **kwargs)

    def add_flag_argument(self, *args, **kwargs):
        self.flag_args.extend(args)
        self.parser.add_argument(*args, **kwargs)

    def parse_args(self, args):
        """Parse a command line, raising argparse.ArgumentError if it is invalid. Returns None once -h printed help."""
        try:
            return self.parser.parse_args(args)
        except SystemExit:
            return None

    def try_parse_args(self, args):
        """Parse a partial command line while completing it. Returns None if it does not parse yet."""
        try:
            return self.parse_args(args)
        except argparse.ArgumentError:
            return None

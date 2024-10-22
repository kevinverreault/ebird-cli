import argparse


class CliArgumentParser:
    def __init__(self):
        self.parser = argparse.ArgumentParser(exit_on_error=False)
        self.positional_args = []
        self.flag_args = []

    def add_positional_argument(self, *args, **kwargs):
        if 'choices' in kwargs:
            self.positional_args.extend(kwargs['choices'])
        self.parser.add_argument(*args, **kwargs)

    def add_flag_argument(self, *args, **kwargs):
        self.flag_args.extend(args)
        self.parser.add_argument(*args, **kwargs)

    def parse_args(self, args):
        return self.parser.parse_args(args)

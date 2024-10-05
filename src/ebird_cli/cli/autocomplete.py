from prompt_toolkit.completion import Completer, Completion, WordCompleter
from prompt_toolkit.document import Document

exit_program = "exit"


class ContextSensitiveCompleter(Completer):
    def __init__(self, commands):
        self.first_word_completer = WordCompleter([cmd.command_name for cmd in commands] + [exit_program], ignore_case=True)
        self.command_completers = {cmd.command_name: cmd for cmd in commands}

    def get_completions(self, document: Document, complete_event):
        text = document.text_before_cursor
        words = text.split(" ")
        if not words or (len(words) == 1 and not text.endswith(" ")):
            for completion in self.first_word_completer.get_completions(document, complete_event):
                yield Completion(completion.text if completion.text == exit_program else completion.text + '', start_position=completion.start_position)
        else:
            command_name = words[0]
            command = self.command_completers.get(command_name)
            if command and len(words) >= 2:
                completions = command.get_completions(words)
                if command.single_param_command():
                    command_arguments = " ".join(words[1:])
                    for completion in completions:
                        yield Completion(completion, start_position=-len(command_arguments))
                else:
                    for completion in completions:
                        yield Completion(completion, start_position=-len(document.get_word_before_cursor()))

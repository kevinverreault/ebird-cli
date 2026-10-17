import pytest

from ebird_cli.cli.grammar import CommandLineError, Flag, Grammar, Positional

COLOURS = Positional("colour", choices=["red", "green", "blue"])


def test_parse_names_each_positional_and_gives_absent_flags_their_default():
    grammar = Grammar([COLOURS], [Flag("size", default="medium"), Flag("label")])

    assert grammar.parse(["green"]) == {"colour": "green", "size": "medium", "label": None}


def test_a_multi_word_flag_takes_every_word_up_to_the_next_flag_in_any_order():
    grammar = Grammar([COLOURS], [Flag("label", multi_word=True), Flag("size")])

    assert grammar.parse(["red", "-size", "large", "-label", "Dunes", "de", "Tadoussac"]) == {
        "colour": "red",
        "label": "Dunes de Tadoussac",
        "size": "large",
    }


@pytest.mark.parametrize(
    ("words", "message"),
    [
        (["purple"], "argument colour: invalid choice: 'purple' (choose from 'red', 'green', 'blue')"),
        (["-size", "large"], "the following arguments are required: colour"),
    ],
)
def test_parse_rejects_a_line_that_does_not_fit_the_positionals(words, message):
    grammar = Grammar([COLOURS], [Flag("size")])

    with pytest.raises(CommandLineError) as error:
        grammar.parse(words)

    assert error.value.message == message


@pytest.mark.parametrize(
    ("words", "message"),
    [
        (["red", "green"], "unrecognized arguments: green"),
        (["red", "-shade", "very", "dark"], "unrecognized arguments: -shade very dark"),
        (["red", "-size", "large", "extra"], "unrecognized arguments: extra"),
        (["red", "-size"], "argument -size: expected one argument"),
        (["red", "-label", "-size", "large"], "argument -label: expected one argument"),
    ],
)
def test_parse_rejects_words_the_flags_do_not_take(words, message):
    grammar = Grammar([COLOURS], [Flag("label", multi_word=True), Flag("size")])

    with pytest.raises(CommandLineError) as error:
        grammar.parse(words)

    assert error.value.message == message


@pytest.mark.parametrize(("value", "expected"), [("2", "2"), ("4", "1"), ("-2", "1"), ("two", "1")])
def test_a_flag_value_outside_its_choices_falls_back_to_the_default(value, expected):
    grammar = Grammar([COLOURS], [Flag("coats", choices=["1", "2", "3"], default="1")])

    assert grammar.parse(["red", "-coats", value])["coats"] == expected


def completions(grammar: Grammar, text: str) -> list[tuple[str, int]]:
    return [(completion.text, completion.start_position) for completion in grammar.complete(text)]


@pytest.mark.parametrize(
    ("text", "expected"),
    [("", [("red", 0), ("green", 0), ("blue", 0)]), ("GR", [("green", -2)]), ("x", [])],
)
def test_complete_offers_the_choices_of_the_next_positional_by_prefix_ignoring_case(text, expected):
    assert completions(Grammar([COLOURS], [Flag("size")]), text) == expected


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("red ", [("-label", 0), ("-size", 0)]),
        ("red -", [("-label", -1), ("-size", -1)]),
        ("red -SI", [("-size", -3)]),
        ("red -size large ", [("-label", 0)]),
        ("red -label Dunes de -", [("-size", -1)]),
    ],
)
def test_complete_offers_the_flags_not_yet_used_once_the_positionals_are_typed(text, expected):
    grammar = Grammar([COLOURS], [Flag("label", multi_word=True), Flag("size")])

    assert completions(grammar, text) == expected


def test_complete_hides_a_flag_while_the_typed_arguments_exclude_it():
    grammar = Grammar([COLOURS], [Flag("label", hidden_when=lambda arguments: arguments["colour"] == "red")])

    assert completions(grammar, "red ") == []
    assert completions(grammar, "blue ") == [("-label", 0)]


def labels(typed: str, arguments: dict) -> list[str]:
    return [
        label for label in [f"{arguments['colour']} door", f"{arguments['colour']} dune"] if label.startswith(typed)
    ]


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("blue -label ", [("blue door", 0), ("blue dune", 0)]),
        ("red -label red d", [("red door", -5), ("red dune", -5)]),
        ("red -label red du", [("red dune", -6)]),
        ("purple -label ", []),
        ("red -shade dark -label ", []),
    ],
)
def test_complete_asks_a_flag_for_values_matching_every_word_typed_after_it(text, expected):
    grammar = Grammar([COLOURS], [Flag("label", multi_word=True, suggestions=labels)])

    assert completions(grammar, text) == expected


@pytest.mark.parametrize(("text", "expected"), [("red -coats ", ["1", "2", "12"]), ("red -coats 2", ["2", "12"])])
def test_complete_offers_the_choices_of_a_flag_containing_what_was_typed(text, expected):
    grammar = Grammar([COLOURS], [Flag("coats", choices=["1", "2", "12"])])

    assert [completion for completion, _ in completions(grammar, text)] == expected


def test_a_flag_can_be_named_by_any_prefix_only_it_starts_with():
    grammar = Grammar([COLOURS], [Flag("label", multi_word=True), Flag("lining"), Flag("size")])

    assert grammar.parse(["red", "-s", "large", "-lab", "Dunes", "de"]) == {
        "colour": "red",
        "label": "Dunes de",
        "lining": None,
        "size": "large",
    }
    with pytest.raises(CommandLineError, match="unrecognized arguments: -l silk"):
        grammar.parse(["red", "-l", "silk"])

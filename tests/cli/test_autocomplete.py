import pytest
from conftest import FIXTURES
from prompt_toolkit.completion import CompleteEvent
from prompt_toolkit.document import Document


@pytest.fixture
def cli(make_cli):
    return make_cli(aggregations=str(FIXTURES / "aggregations.json"))


@pytest.mark.parametrize(
    ("text", "expected"),
    [("", ["recent", "notable", "exit"]), ("re", ["recent"]), ("NO", ["notable"]), ("e", ["exit"]), ("x", [])],
)
def test_first_word_offers_command_names_and_exit(cli, text, expected):
    assert cli.completions(text) == expected


@pytest.mark.parametrize("command", ["recent", "notable"])
def test_scope_is_offered_after_the_command_name(cli, command):
    assert cli.completions(f"{command} ") == ["hotspot", "nearby", "regional", "subnational"]


def test_scope_completion_filters_on_what_was_typed(cli):
    assert cli.completions("recent re") == ["regional"]


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("recent regional ", ["-region", "-species", "-back"]),
        ("recent regional -", ["-region", "-species", "-back"]),
        ("recent regional -r", ["-region"]),
        ("notable regional ", ["-region", "-back"]),
    ],
)
def test_flags_are_offered_after_the_scope(cli, text, expected):
    assert cli.completions(text) == expected


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("recent regional -back 3 ", ["-region", "-species"]),
        ("recent regional -region Montréal -", ["-species", "-back"]),
        ("recent nearby -back 1 ", ["-species"]),
    ],
)
def test_only_flags_not_already_used_are_offered(cli, text, expected):
    assert cli.completions(text) == expected


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("recent nearby ", ["-species", "-back"]),
        ("recent nearby -", ["-species", "-back"]),
        ("notable nearby ", ["-back"]),
    ],
)
def test_region_flag_is_hidden_after_nearby_scope(cli, text, expected):
    assert cli.completions(text) == expected


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        (
            "recent subnational -region ",
            ["Alberta", "Colombie-Britannique", "Nouveau-Brunswick", "Nouvelle-Écosse", "Ontario", "Québec"],
        ),
        ("recent subnational -region NOU", ["Nouveau-Brunswick", "Nouvelle-Écosse"]),
        ("recent regional -region ", ["Côte-Nord", "Montérégie", "Montréal", "Mauricie"]),
        ("notable regional -region mont", ["Montérégie", "Montréal"]),
        ("recent regional -region ri", ["Mauricie"]),
    ],
)
def test_region_values_match_the_scope_case_insensitively_by_substring(cli, text, expected):
    assert cli.completions(text) == expected


def test_hotspot_region_values_include_aggregation_names(cli):
    assert cli.completions("recent hotspot -region ") == [
        "Dunes de Tadoussac",
        "Dunes de Tadoussac--Halte",
        "Parc de l'Île-Saint-Quentin",
        "Parc national de la Mauricie",
        "Technoparc--Étang Hertel",
        "Technoparc",
        "Trois-Rivières",
    ]


def test_hotspot_region_values_filter_hotspots_and_aggregations(cli):
    assert cli.completions("recent hotspot -region tech") == ["Technoparc--Étang Hertel", "Technoparc"]


@pytest.mark.parametrize("typed", ["Dunes de", "Dunes  de"])
def test_multi_word_region_value_completion_replaces_every_word_typed_after_the_flag(cli, typed):
    text = f"recent hotspot -region {typed}"

    completions = list(cli.completer.get_completions(Document(text, len(text)), CompleteEvent()))

    assert [(completion.text, completion.start_position) for completion in completions] == [
        ("Dunes de Tadoussac", -len(typed)),
        ("Dunes de Tadoussac--Halte", -len(typed)),
    ]


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("recent regional -species canard", ["Canard noir", "Canard colvert"]),
        ("recent nearby -species HARFANG des", ["Harfang des neiges"]),
        ("recent regional -species tête", ["Mésange à tête noire"]),
        ("recent regional -species ", []),
    ],
)
def test_species_values_match_national_taxonomy_case_insensitively_by_substring(cli, text, expected):
    assert cli.completions(text) == expected


def test_back_values_match_days_containing_what_was_typed(cli):
    assert cli.completions("recent regional -back 3") == ["3", "13", "23", "30"]


def test_back_values_offer_every_accepted_day_from_1_to_30(cli):
    assert cli.completions("recent regional -back ") == [str(day) for day in range(1, 31)]


@pytest.mark.parametrize("text", ["bogus ", "bogus x"])
def test_unknown_command_yields_a_single_empty_completion(cli, text):
    assert cli.completions(text) == [""]

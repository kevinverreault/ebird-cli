def test_species_code_lookup_needs_the_exact_common_name(cli):
    assert cli.taxonomy_service.get_species_code("Harfang des neiges") == ["snoowl1"]
    assert cli.taxonomy_service.get_species_code("harfang des neiges") == []
    assert cli.taxonomy_service.get_species_code("Harfang") == []


def test_species_outside_the_national_taxonomy_are_unknown(cli):
    assert cli.taxonomy_service.get_species_code("Kiwi austral") == []
    assert cli.taxonomy_service.search_by_common_name("kiwi") == []


def test_common_name_search_is_case_insensitive_substring(cli):
    assert cli.taxonomy_service.search_by_common_name("NOIR") == ["Canard noir", "Mésange à tête noire"]

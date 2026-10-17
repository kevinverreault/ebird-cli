import pytest


@pytest.mark.parametrize(
    "line",
    [
        "recent nearby",
        "recent regional",
        "recent nearby -species Canard colvert",
        "recent regional -species Canard colvert",
        "notable nearby",
        "notable regional",
    ],
)
def test_requests_pass_back_and_hotspot_per_call_without_changing_client_state(cli, line):
    state_before = {name: value for name, value in vars(cli.client).items() if name != "calls"}

    cli.run(f"{line} -back 3")

    assert {name: value for name, value in vars(cli.client).items() if name != "calls"} == state_before
    assert [(call.back, call.hotspot) for call in cli.client.calls] == [("3", True)]

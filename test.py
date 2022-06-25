import pytest
from typing import Dict

from move_semantics import Move, unpack, move, Gone

def get_id(value: Move[Dict[str, str]]) -> str:
    value_unpacked = unpack(value)
    return value_unpacked.pop("id")


def test_move_semantics() -> None:
    value = {"id": "foobar"}
    with move(value) as moved_value:
        id = get_id(moved_value)
        # in test mode, the moved value is removed from locals and replaced
        # with a placeholder
        assert isinstance(value, Gone)
        # presence of this line is enforced at runtime by decorator
        del value, moved_value  

    assert id == "foobar"
    with pytest.raises(UnboundLocalError):
        # mypy complains because we del'd those variables
        assert value["id"] == 'foobar'  # type: ignore

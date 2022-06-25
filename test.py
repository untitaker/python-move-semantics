import pytest
from typing import Dict

from move_semantics import LeakedMoveError, Move, unpack, move, Gone

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


def test_del_missing() -> None:
    value = {"id": "foobar"}
    with pytest.raises(LeakedMoveError):
        with move(value) as moved_value:
            pass

def test_del_missing2() -> None:
    value = {"id": "foobar"}
    with pytest.raises(LeakedMoveError):
        with move(value) as moved_value:
            del value

def test_del_missing3() -> None:
    value = {"id": "foobar"}
    with pytest.raises(LeakedMoveError):
        with move(value) as moved_value:
            del moved_value

def test_no_del_missing() -> None:
    value = {"id": "foobar"}
    with move(value) as moved_value:
        del value, moved_value
        

def test_multiple_references() -> None:
    value = {"id": "foobar"}
    with pytest.raises(LeakedMoveError):
        with move(value) as moved_value:
            moved_value2 = moved_value
            value2 = value

            del value, moved_value
        

def test_store_value() -> None:
    storage = []

    def store_value(value: Move[Dict[str, str]]):
        storage.append(unpack(value))

    value = {"id": "foobar"}
    with move(value) as moved_value:
        store_value(moved_value)
        del value, moved_value

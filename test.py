import pytest
from typing import Dict, List

from move_semantics import LeakedMoveError, Move, unpack, move, Gone, NoUniqueAccessError

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

    def store_value(value: Move[Dict[str, str]]) -> None:
        storage.append(unpack(value))

    value = {"id": "foobar"}
    with move(value) as moved_value:
        store_value(moved_value)
        del value, moved_value


def test_move_again() -> None:
    Ty = Dict[str, str]
    storage1 = []
    def bar(value: Move[Ty]) -> None:
        storage1.append(unpack(value))
        pass

    storage2 = []
    def foo(value: Move[Ty]) -> None:
        storage2.append(unpack(value))
        bar(value)

    value = {"id": "foobar"}

    with pytest.raises(NoUniqueAccessError):
        with move(value) as moved_value:
            foo(moved_value)
            del value, moved_value


def test_move_again2() -> None:
    Ty = Dict[str, str]
    storage1: List[Ty] = []
    def bar(value: Move[Ty]) -> None:
        storage1.append(unpack(value))

    storage2: List[Ty] = []
    def foo(value: Move[Ty]) -> None:
        value2 = unpack(value)
        storage2.append(value2)

        with move(value2) as value3:
            bar(value3)
            del value2, value3, value

    value = {"id": "foobar"}

    with pytest.raises(NoUniqueAccessError):
        with move(value) as moved_value:
            foo(moved_value)
            del value, moved_value

def test_move_three_times() -> None:
    Ty = Dict[str, str]
    storage1 = []
    def baz(value: Move[Ty]) -> None:
        storage1.append(unpack(value))

    def bar(value: Move[Ty]) -> None:
        baz(value)

    def foo(value: Move[Ty]) -> None:
        bar(value)

    value = {"id": "foobar"}

    with move(value) as moved_value:
        foo(moved_value)
        del value, moved_value

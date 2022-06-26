import contextlib
import platform
import sys
import inspect
from weakref import WeakSet, WeakValueDictionary
from typing import Generator, Generic, TypeVar, Protocol, NewType, TYPE_CHECKING,Any

if TYPE_CHECKING:
    from types import FrameType
    from types import TracebackType

RUNTIME_CHECKS = True
_INTERNED_TYPES = (int, str)

T = TypeVar("T")

class Move(Generic[T]):
    pass


class Gone:
    def __init__(self, value: Any) -> None:
        self._inner_value = value


def _wipe_value_from_locals(value: Any, caller: 'FrameType') -> WeakValueDictionary:
    caller_locals = caller.f_locals
    locals_modified = False
    removed_values = WeakValueDictionary()
    for k in list(caller_locals):
        if caller_locals[k] is value:
            caller_locals[k] = Gone(caller_locals[k])
            removed_values[k] = caller_locals[k]
            locals_modified = True

    if locals_modified:
        locals_to_fast(caller)

    return removed_values


class MoveError(RuntimeError):
    pass

class NoUniqueAccessError(MoveError):
    pass

class LeakedMoveError(MoveError):
    pass


@contextlib.contextmanager
def move(value: T) -> Generator[Move[T], None, None]:
    if not RUNTIME_CHECKS or type(value) in _INTERNED_TYPES:
        yield value  # type: ignore
        return

    # caller's local variable, our local variable and getrefcount
    if sys.getrefcount(value) > 3:
        raise NoUniqueAccessError(value)

    # caller frame
    caller: 'FrameType' = inspect.currentframe().f_back.f_back  # type: ignore
    removed_values = _wipe_value_from_locals(value, caller)

    yield value  # type: ignore

    removed_values.update(_wipe_value_from_locals(value, caller))

    if removed_values:
        raise LeakedMoveError(dict(removed_values))

    _unpacked_values.clear()


_unpacked_values = {}


def unpack(value: Move[T]) -> T:
    if RUNTIME_CHECKS:
        if _unpacked_values.get(id(value)) is value:
            raise NoUniqueAccessError(value)
        
        _unpacked_values[id(value)] = value
    return value  # type: ignore


if platform.python_implementation() == "CPython":
    import ctypes

    def locals_to_fast(frame):
        # type: (FrameType) -> None
        ctypes.pythonapi.PyFrame_LocalsToFast(ctypes.py_object(frame), ctypes.c_int(0))
elif platform.python_implementation() == "PyPy":
    from __pypy__ import locals_to_fast  # type: ignore

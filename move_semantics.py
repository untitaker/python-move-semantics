import contextlib
import platform
import sys
import inspect
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


@contextlib.contextmanager
def move(value: T) -> Generator[Move[T], None, None]:
    if not RUNTIME_CHECKS or type(value) in _INTERNED_TYPES:
        yield value  # type: ignore
        return

    # caller's local variable, our local variable and getrefcount
    if sys.getrefcount(value) > 3:
        raise RuntimeError("no unique access to value!")

    # caller frame
    caller: 'FrameType' = inspect.currentframe().f_back.f_back  # type: ignore
    caller_locals = caller.f_locals
    locals_modified = False
    for k in list(caller_locals):
        if caller_locals[k] is value:
            caller_locals[k] = Gone(caller_locals[k])
            locals_modified = True

    if locals_modified:
        locals_to_fast(caller)

    del caller
    del caller_locals

    yield value  # type: ignore

    # our local variable, getrefcount, and for some reason
    # overriding the caller's local variable with Gone
    # creates another reference
    if sys.getrefcount(value) > 3:
        raise RuntimeError("value has not been deleted. please insert del stmt")

def unpack(value: Move[T]) -> T:
    return value  # type: ignore


if platform.python_implementation() == "PyPy":
    from __pypy__ import locals_to_fast  # type: ignore
elif platform.python_implementation() == "CPython":
    import ctypes

    def locals_to_fast(frame):
        # type: (FrameType) -> None
        ctypes.pythonapi.PyFrame_LocalsToFast(ctypes.py_object(frame), ctypes.c_int(0))

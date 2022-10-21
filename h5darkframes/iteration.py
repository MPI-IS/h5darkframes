import typing
import itertools
from .control_range import ControlRange


def iterate_ints(*a) -> typing.Generator[typing.Tuple[int, ...], None, None]:
    """
    returns all combination of values
    """
    for values in itertools.product(*a):
        yield values
    return None


def iterate_controls(
    controls: typing.List[ControlRange],
) -> typing.Generator[typing.Tuple[int, ...], None, None]:
    """
    Function that iterate over all the possible combinations of
    controls
    """
    all_values = [prange.get_values() for prange in controls]
    return _iterate_ints(*all_values)

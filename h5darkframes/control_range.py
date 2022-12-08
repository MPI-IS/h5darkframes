import typing
import itertools
from collections import OrderedDict


class ControlRange:
    """
    Configuration item for the method "create_hdf5", allowing the user
    to specify for a given control which range of value should be used.

    Arguments
    ---------
    min:
      start of the range.
    max:
      end of the range.
    step:
      step between min and max.
    threshold:
      as the method 'create_hdf5' will go through the values, it
      will set the camera configuration accordingly. For some control
      (for now we only have temperature in mind) this may require time
      and not be precise. This threshold setup the accepted level of precision
      for the control.
    timeout:
      the camera will attempt to setup the right value (+/ threshold) for
      at maximum this duration (in seconds).
    """

    def __init__(
        self,
        min_: int,
        max_: int,
        step: int,
        threshold: int = 0,
        timeout: float = 0.1,
    ) -> None:
        if not isinstance(min_, int):
            raise ValueError(f"Control range: min value ({min_}) must be an integer")
        if not isinstance(max_, int):
            raise ValueError(f"Control range: max value ({max_}) must be an integer")
        self.min = min_
        self.max = max_
        self.step = step
        self.threshold = threshold
        self.timeout = timeout

    def to_dict(self) -> typing.Dict[str, typing.Any]:
        attrs = ("min", "max", "step", "threshold", "timeout")
        return {attr: getattr(self, attr) for attr in attrs}

    def get_values(self) -> typing.List[int]:
        """
        return the list of values in the range
        """
        if self.step == 0:
            if self.min != self.max:
                raise ValueError(
                    "Issue with range configuration: a step of 0 is accepted only if the min and the max values "
                    "are different (min: {self.min}, max: {self.max}"
                )
            else:
                return [self.min]
        return list(range(self.min, self.max + 1, self.step))

    def __str__(self, name: typing.Optional[str] = None):
        if name is None:
            name = ""
        else:
            name = f"{name}:\t"
        return str(f"{name}{repr(self.get_values())}")

    def __repr__(self) -> str:
        return str(
            f"ControlRange({self.min},{self.max}, "
            f"{self.step},{self.threshold},{self.timeout})"
        )

    @classmethod
    def iterate_controls(
        cls,
        controls: typing.Mapping[str, object],  # object: instance of ControlRange
    ) -> typing.Generator[typing.OrderedDict[str, int], None, None]:
        all_values: typing.List[typing.Iterable] = []
        for prange in controls.values():
            prange_ = typing.cast(ControlRange, prange)
            all_values.append(prange_.get_values())
        for values in itertools.product(*all_values):
            d = OrderedDict()
            for control, value in zip(controls.keys(), values):
                d[control] = value
            yield (d)
        return None

    def __eq__(self, other) -> bool:
        attrs = ("min", "max", "threshold", "step")
        return all([getattr(self, attr) == getattr(other, attr) for attr in attrs])

from collections import OrderedDict
import typing
import toml
from pathlib import Path
from .camera import Camera
from .roi import ROI


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
        return list(range(self.min, self.max + 1, self.step))

    def __str__(self, name: typing.Optional[str] = None):
        if name is None:
            name = ""
        else:
            name = f"{name}:\t"
        return str(f"{name}{repr(self.get_values)}")

    def __repr__(self) -> str:
        return str(
            f"ControlRange({self.min},{self.max}, "
            f"{self.step},{self.threshold},{self.timeout})"
        )


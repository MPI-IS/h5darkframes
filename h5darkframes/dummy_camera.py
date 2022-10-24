import time
import typing
import numpy
import toml
from collections import OrderedDict
from numpy import typing as npt
from pathlib import Path
from .control_range import ControlRange
from .camera import Camera


class DummyCamera(Camera):
    """
    dummy camera, for testing
    """

    def __init__(
        self, control_ranges: typing.Mapping[str, ControlRange], value: int = 0
    ) -> None:
        super().__init__(control_ranges)
        self.width = 0
        self.height = 0
        self._value = value

    def picture(self) -> npt.ArrayLike:
        """
        Taking a picture
        """
        time.sleep(0.01)
        return numpy.zeros((self.width, self.height)) + self._value

    def configure(self, path: Path) -> None:
        """
        Configure the camera
        """
        if not path.is_file():
            raise FileNotFoundError(str(path))
        content = toml.load(str(path))
        try:
            config = content["camera"]
        except KeyError:
            raise KeyError(
                f"failed to find the key 'camera' in the configuration file {path}"
            )
        self._value = int(config["value"])

    def get_configuration(self) -> typing.Mapping[str, int]:
        """
        Returns the current configuration of the camera
        """
        return {"width": self.width, "height": self.height, "value": self._value}

    def estimate_picture_time(self, controls: typing.Mapping[str, int]) -> float:
        """
        estimation of how long it will take for a picture
        to be taken (typically relevant if one of the control
        is the exposure time
        """
        return 0.01

    def set_control(self, control: str, value: int) -> None:
        """
        Changing the configuration of the camera
        """
        setattr(self, control, value)

    def get_control(self, control: str) -> int:
        """
        Getting the configuration of the camera
        """
        return getattr(self, control)

    @classmethod
    def generate_config_file(cls, path: Path, **kwargs) -> None:
        """
        Generate a default toml configuration file specifying the control ranges
        of the darkframes pictures.
        """
        r: typing.Dict[str, typing.Any] = {}
        r["darkframes"] = {}
        r["darkframes"]["average_over"] = 5
        control_ranges = OrderedDict()
        control_ranges["width"] = ControlRange(10, 20, 5, 0, 10)
        control_ranges["height"] = ControlRange(100, 200, 50, 0, 10)
        r["darkframes"]["controllables"] = OrderedDict()
        for name, control_range in control_ranges.items():
            r["darkframes"]["controllables"][name] = control_range.to_dict()
        r["camera"] = {"value": kwargs["value"]}
        with open(path, "w") as f:
            toml.dump(r, f)

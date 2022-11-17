import time
import typing
import numpy
import toml
import threading
from collections import OrderedDict
from numpy import typing as npt
from pathlib import Path
from .control_range import ControlRange
from .camera import Camera
from .toml_config import read_config


class _Height:
    def __init__(self, value: int, dynamic: bool) -> None:
        self._value = value
        self._desired = value
        self._dynamic = dynamic
        self._lock = threading.Lock()
        if self._dynamic:
            self._running = False
            self._thread = threading.Thread(target=self._run)
            self._thread.start()

    def set(self, value) -> None:
        # not dynamic, directly setting the value
        if not self._dynamic:
            self._value = value
            return
        # dynamic: setting a desired value,
        # (the running thread will have value
        # reaching the desired value over some
        # time lapse)
        with self._lock:
            self._desired = value

    def get(self) -> int:
        with self._lock:
            return self._value

    def stop(self) -> None:
        if self._dynamic:
            self._running = False
            self._thread.join()

    def _run(self) -> None:
        self._running = True
        while self._running:
            with self._lock:
                if self._value != self._desired:
                    if self._value > self._desired:
                        self._value -= 1
                    else:
                        self._value += 1
            time.sleep(0.1)


class DummyCamera(Camera):
    """
    dummy camera, for testing
    """

    def __init__(
        self,
        control_ranges: typing.Mapping[str, ControlRange],
        value: int = 0,
        dynamic: bool = True,
    ) -> None:
        super().__init__(control_ranges)
        self.width = 0
        self._height = _Height(0, dynamic)
        self._value = value

    def stop(self):
        self._height.stop()

    def picture(self) -> npt.ArrayLike:
        """
        Taking a picture
        """
        time.sleep(0.001)
        shape = (self.width, self._height.get())
        return numpy.zeros(shape) + self._value

    @classmethod
    def configure(cls, path: Path, **kwargs) -> object:
        """
        Configure the camera
        """
        if not path.is_file():
            raise FileNotFoundError(str(path))
        control_ranges, _ = read_config(path)
        content = toml.load(str(path))
        try:
            content["camera"]
        except KeyError:
            raise KeyError(
                f"failed to find the key 'camera' in the configuration file {path}"
            )
        instance = cls(control_ranges, content["camera"]["value"])
        return instance

    def get_configuration(self) -> typing.Dict[str, int]:
        """
        Returns the current configuration of the camera
        """
        return {"width": self.width, "height": self._height.get(), "value": self._value}

    def estimate_picture_time(self, controls: typing.Mapping[str, int]) -> float:
        """
        estimation of how long it will take for a picture
        to be taken (typically relevant if one of the control
        is the exposure time
        """
        return 0.001

    def set_control(self, control: str, value: int) -> None:
        """
        Changing the configuration of the camera
        """
        if control != "height":
            setattr(self, control, value)
        else:
            self._height.set(value)

    def get_control(self, control: str) -> int:
        """
        Getting the configuration of the camera
        """
        if control != "height":
            return getattr(self, control)
        else:
            return self._height.get()

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
        control_ranges["height"] = ControlRange(100, 200, 50, 0, 10)
        control_ranges["width"] = ControlRange(10, 20, 5, 0, 10)
        r["darkframes"]["controllables"] = OrderedDict()
        for name, control_range in control_ranges.items():
            r["darkframes"]["controllables"][name] = control_range.to_dict()
        r["camera"] = {"value": kwargs["value"]}
        with open(path, "w") as f:
            toml.dump(r, f)

    def __enter__(self):
        return self

    def __exit__(self, _, __, ___):
        self.stop()

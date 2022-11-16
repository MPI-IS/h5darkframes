import numpy.typing as npt
import toml
import typing
from collections import OrderedDict
from pathlib import Path
import camera_zwo_asi as zwo
from .camera import Camera
from .control_range import ControlRange
from .toml_config import read_config


class AsiZwoCamera(Camera):
    def __init__(
        self, index, control_ranges: typing.Mapping[str, ControlRange]
    ) -> None:
        super().__init__(control_ranges)
        self._camera = zwo.Camera(index)

    def picture(self) -> npt.ArrayLike:
        """
        Taking a picture
        """
        image = self._camera.capture()
        return image.get_image()

    def get_configuration(self) -> typing.Mapping[str, int]:
        """
        Returns the current configuration of the camera
        """
        return self._camera.to_dict()

    @classmethod
    def configure(cls, path: Path, **kwargs) -> object:
        """
        Configure the camera from a toml
        configuration file.
        """
        if not path.is_file():
            raise FileNotFoundError(str(path))
        control_ranges, _ = read_config(path)
        instance = cls(kwargs["index"], control_ranges)
        content = toml.load(str(path))
        try:
            config = content["camera"]
        except KeyError:
            raise KeyError(
                f"failed to find the key 'camera' in the configuration file {path}"
            )
        instance._camera.configure_from_toml(config)
        return instance

    def estimate_picture_time(self, controls: typing.Mapping[str, int]) -> float:
        """
        estimation of how long it will take for a picture
        to be taken (typically relevant if one of the control
        is the exposure time)
        """
        if "Exposure" not in controls:
            return self._camera.get_controls()["Exposure"].value / 1e6
        else:
            return controls["Exposure"] / 1e6

    def set_control(self, control: str, value: int) -> None:
        """
        Changing the configuration of the camera
        """
        if control == "TargetTemp":
            self._camera.set_control("CoolerOn", 1)
        self._camera.set_control(control, value)

    def get_control(self, control: str) -> int:
        """
        Getting the configuration of the camera
        """
        control = control if control != "TargetTemp" else "Temperature"
        v = self._camera.get_controls()[control].value
        if control == "Temperature":
            return int(v / 10.0 + 0.5)
        else:
            return v

    @classmethod
    def generate_config_file(cls, path: Path, **kwargs):
        """
        Generate a toml configuration file with reasonable
        default values. User can edit this file and then call
        the method 'ControlRangefrom_toml' to get desired instances of ControlRange
        and ROI.
        """
        if "index" not in kwargs:
            raise ValueError(
                "the keywork argument 'index' is required for generating "
                "asi zwo camera configuration file"
            )
        if not path.parent.is_dir():
            raise FileNotFoundError(
                f"can not generate the configuration file {path}: "
                f"directory {path.parent} not found"
            )
        camera = zwo.Camera(kwargs["index"])
        r: typing.Dict[str, typing.Any] = {}
        r["darkframes"] = {}
        r["darkframes"]["average_over"] = 5
        control_ranges = OrderedDict()
        control_ranges["TargetTemp"] = ControlRange(-15, 15, 3, 1, 600)
        control_ranges["Exposure"] = ControlRange(1000000, 30000000, 4000000, 1, 0.1)
        control_ranges["Gain"] = ControlRange(200, 400, 100, 1, 0.1)
        r["darkframes"]["controllables"] = OrderedDict()
        for name, control_range in control_ranges.items():
            r["darkframes"]["controllables"][name] = control_range.to_dict()
        r["camera"] = camera.to_dict()

        with open(path, "w") as f:
            toml.dump(r, f)

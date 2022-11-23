import typing
import time
from pathlib import Path
import numpy.typing as npt
from .control_range import ControlRange
from .progress import Progress


class ImageTaker:
    def picture(self) -> npt.ArrayLike:
        """
        Taking a picture
        """
        raise NotImplementedError()


class Camera(ImageTaker):
    """
    Abstract superclass for a configurable camera.
    """

    def __init__(self, control_ranges: typing.Mapping[str, ControlRange]) -> None:
        self._thresholds = {
            control: cr.threshold for control, cr in control_ranges.items()
        }
        self._timeouts = {control: cr.timeout for control, cr in control_ranges.items()}
        self._set_values: typing.Dict[str, typing.Optional[int]] = {
            control: None for control in control_ranges.keys()
        }

    @classmethod
    def configure(
        cls, path: Path, **kwargs
    ) -> object:  # object will be an instance of Camera
        """
        Instantiate and configure the camera
        """
        raise NotImplementedError()

    def stop(self) -> None:
        return

    def get_configuration(self) -> typing.Mapping[str, int]:
        """
        Returns the current configuration of the camera
        """
        raise NotImplementedError()

    def estimate_picture_time(self, controls: typing.Mapping[str, int]) -> float:
        """
        estimation of how long it will take for a picture
        to be taken (typically relevant if one of the control
        is the exposure time
        """
        raise NotImplementedError

    def set_control(self, control: str, value: int) -> None:
        """
        Changing the configuration of the camera
        """
        raise NotImplementedError()

    def get_control(self, control: str) -> int:
        """
        Getting the configuration of the camera
        """
        raise NotImplementedError()

    def reach_control(
        self,
        control: str,
        value: int,
        progress: typing.Optional[Progress] = None,
        sleeptime: float = 0.02,
    ) -> None:
        """
        Changing the configuration of the camera, but without the assumption
        this can be done instantly: if threshold is not 0, then the function
        will block until the configuration reached the desired value (up to
        timeout, in seconds). A use case: changing the temperature of the camera.
        """
        set_value = self._set_values[control]
        if set_value is not None and set_value == value:
            return
        self._set_values[control] = value
        timeout = self._timeouts[control]
        threshold = self._thresholds[control]
        self.set_control(control, value)
        start = time.time()
        tdiff = time.time() - start
        while tdiff < timeout:
            obtained_value = self.get_control(control)
            if abs(value - obtained_value) <= threshold:
                return
            if progress is not None:
                progress.reach_control_feedback(
                    control, obtained_value, value, threshold, tdiff, timeout
                )
            time.sleep(sleeptime)
            tdiff = time.time() - start

    @classmethod
    def generate_config_file(cls, path: Path, **kwargs) -> None:
        """
        Generate a default toml configuration file specifying the control ranges
        of the darkframes pictures.
        """
        raise NotImplementedError()

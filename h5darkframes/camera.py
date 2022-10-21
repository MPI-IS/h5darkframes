import typing
import time
import numpy.typing as npt
from .control_range import ControlRange

class Camera:
    """
    Abstract superclass for a configurable camera.
    """

    def picture(self)->npt.ArrayLike:
        """
        Taking a picture
        """
        raise NotImplementedError()

    def estimate_picture_time(
            self
            controls : typing.Mapping[str,int]
    )->float:
        """
        estimation of how long it will take for a picture
        to be taken (typically relevant if one of the control
        is the exposure time
        """
        raise NotImplementedError
        
    
    def set_control(control: str, value: int)->None:
        """
        Changing the configuration of the camera
        """
        raise NotImplementedError()

    def get_control(control: str)->int:
        """
        Getting the configuration of the camera
        """
        raise NotImplementedError()
    
    def reach_control(
            self,
            control: str,
            value: int,
            timeout: float,
            threshold: int = 0,
            callback: typing.Optional[typing.Callable[[int,int],None]] = None,
            sleeptime: float = 0.02
    )->None:
        """
        Changing the configuration of the camera, but without the assumption 
        this can be done instantly: if threshold is not 0, then the function
        will block until the configuration reached the desired value (up to 
        timeout, in seconds). A use case: changing the temperature of the camera. 
        """
        
        self.set_control(control,value)
        if threshold==0:
            return
        start = time.time()
        while time.time() - start < timeout:
            obtained_value = self.get_control(control)
            if abs(value - obtained_value) <= threshold:
                return
            if callback is not None:
                callback(obtained_value,value)
            time.sleep(sleeptime)

    
    @classmethod
    def from_toml(cls, path: Path) -> typing.Tuple[typing.Dict[str, object], ROI, int]:
        """
        Generate a list of instances of ControlRange, an instance
        of a ROI based on a toml configuration file and an int value setting
        how many pictures have to be taken per darkframe. The configuration
        files must have the keys "ROI", "controllables" and "average_over". The "ROI" section
        must have values for start_x, start_y, width, height, bins, type.
        Each controllable must have values for min, max, step, threshold and
        timeout (in seconds).
        """

        def _get_range(name: str, config: typing.Mapping[str, typing.Any]) -> object:
            required_keys = ("min", "max", "step", "threshold", "timeout")
            for rk in required_keys:
                if rk not in config.keys():
                    raise ValueError(
                        f"error with darkframes configuration file {path}, "
                        f"controllable {name}: "
                        f"missing required key '{rk}'"
                    )
            try:
                min_, max_, step, threshold, timeout = [
                    int(config[key]) for key in required_keys
                ]
            except ValueError as e:
                raise ValueError(
                    f"error with darkframes configuration file {path}, "
                    f"controllable {name}: "
                    f"failed to cast value to int ({e})"
                )
            return cls(min_, max_, step, threshold, timeout)

        if not path.is_file():
            raise FileNotFoundError(str(path))
        content = toml.load(str(path))

        required_keys = ("ROI", "average_over", "controllables")
        for rk in required_keys:
            if rk not in content.keys():
                raise ValueError(
                    f"error with darkframes configuration file {path}: "
                    f"missing key '{rk}'"
                )

        roi = typing.cast(ROI, ROI.from_toml(content["ROI"]))
        try:
            avg_over = int(content["average_over"])
        except ValueError as e:
            raise ValueError(
                f"failed to cast value for 'average_over' ({content['average_over']}) "
                f"to int: {e}"
            )

        controllables = content["controllables"]
        return (
            {name: _get_range(name, values) for name, values in controllables.items()},
            roi,
            avg_over,
        )

    @classmethod
    def generate_config_file(cls, camera: Camera, path: Path) -> None:
        """
        Generate a toml configuration file with reasonable
        default values. User can edit this file and then call
        the method 'from_toml' to get desired instances of ControlRange
        and ROI.
        """

        if not path.parent.is_dir():
            raise FileNotFoundError(
                f"can not generate the configuration file {path}: "
                f"directory {path.parent} not found"
            )
        r: typing.Dict[str, typing.Any] = {}
        r["average_over"] = 5
        roi = camera.get_roi().to_dict()
        r["ROI"] = roi
        control_ranges = OrderedDict()
        control_ranges["TargetTemp"] = ControlRange(-15, 15, 3, 1, 600)
        control_ranges["Exposure"] = ControlRange(1000000, 30000000, 5000000, 1, 0.1)
        control_ranges["Gain"] = ControlRange(200, 400, 100, 1, 0.1)
        r["controllables"] = OrderedDict()
        for name, control_range in control_ranges.items():
            r["controllables"][name] = control_range.to_dict()
        with open(path, "w") as f:
            toml.dump(r, f)

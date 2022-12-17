import typing
import time
from pathlib import Path
import numpy.typing as npt
from .control_range import ControlRange
from .progress import Progress



def _dump_picture(
    image: npt.ArrayLike,
    directory: Path,
    index: int,
    controllables: Controllables,
    param: Param,
    file_format: str = "npy",
) -> None:

    filename = "_".join([f"{key}_{value}" for key,value in zip(controllables,param)])
    filename += f"_{index}.{file_format}"

    path = directory / filename

    _logger.debug(f"writing file {path}")

    if file_format == "npy":
        np.save(path, image)
    else:
        cv2.imwrite(path, image)


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

    def __init__(
            self,
            control_ranges: typing.Mapping[str, ControlRange],
            progress: typing.Optional[Progress] = None,
            dump_path: typing.Optional[Path] = None,
            dumpy_format: str = "tiff"
    ) -> None:
        self._thresholds = {
            control: cr.threshold for control, cr in control_ranges.items()
        }
        self._timeouts = {control: cr.timeout for control, cr in control_ranges.items()}
        self._set_values: typing.Dict[str, typing.Optional[int]] = {
            control: None for control in control_ranges.keys()
        }
        self._progress = progress
        self._dump_path = dump_path
        self._dump_format = dump_format

    def averaged_picture(
            self,
            controllables: Controllables,
            param: Param,
            average_over: int
    )->npt.ArrayLike:
        images_sum: typing.Optional[npt.ArrayLike] = None
        images_type = None
        for index in range(average_over):
            original_image = camera.picture()
            if self._dump_path:
                _dump_picture(original_image, dump, index, controllables, param, dump_format)
            if images_type is None:
                images_type = original_image.dtype  # type: ignore
            image_ = original_image.astype(np.uint64)  # type: ignore
            if images_sum is None:
                images_sum = image_
            else:
                images_sum += image_
            if self._progress is not None:
                progress.picture_taken_feedback(1)
        return (images_sum / avg_over).astype(images_type)  # type: ignore
        
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

    def get_param(self, controllables: Controllables)->Param:
        values = [self.get_control(controllable) for controllable in controllables]
        return tuple(values)
    
    def reach_control(
        self,
        control: str,
        value: int,
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
            if self._progress is not None:
                self._progress.reach_control_feedback(
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

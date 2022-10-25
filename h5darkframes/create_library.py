from collections import OrderedDict
from pathlib import Path
import h5py
import typing
import numpy as np
from numpy import typing as npt
from .camera import Camera
from .control_range import ControlRange
from .progress import Progress


def _add_to_hdf5(
    camera: Camera,
    controls: typing.OrderedDict[str, int],
    avg_over: int,
    hdf5_file: h5py.File,
    progress: typing.Optional[Progress] = None,
) -> None:
    """
    Has the camera take images, average them and adds this averaged image
    to the hdf5 file, with 'path'
    like hdf5_file[param1.value][param2.value][param3.value]...
    Before taking the image, the camera's configuration is set accordingly.
    Returns the estimated duration taken by the function to complete.
    """

    # for the progress feedback
    estimated_duration = camera.estimate_picture_time(controls)

    # setting the configuration of the current pictures set
    for control, value in controls.items():
        camera.reach_control(control, value, progress=progress)

    # taking and averaging the pictures
    images: typing.List[npt.ArrayLike] = []
    for _ in range(avg_over):
        images.append(camera.picture())
        if progress is not None:
            progress.picture_taken_feedback(controls, estimated_duration, 1)
    image = np.mean(images, axis=0)  # type: ignore

    # adding the image to the hdf5 file
    group = hdf5_file
    for control in controls.keys():
        value = camera.get_control(control)
        group = group.require_group(str(value))
    group.create_dataset("image", data=image)

    # add the camera current configuration to the group
    group.attrs["camera_config"] = repr(camera.get_configuration())


def library(
    name: str,
    camera: Camera,
    control_ranges: OrderedDict[str, ControlRange],
    avg_over: int,
    hdf5_path: Path,
    progress: typing.Optional[Progress] = None,
) -> None:
    """Create an hdf5 image library file

    This function will take pictures using
    the specified configuration range. For each configuration, a set of
    'avg_over' pictures are taken and averaged.
    Images can be accessed using instances of 'ImageLibrary'.
    'name' is a (possibly chosen unique) arbitrary string,
    used for identification of the file (can be, for example,
    the serial number of the camera used to take the frames).
    For each set of picture taken, the callback is called, passing
    as argument the duration taken to take the pictures.
    """

    # opening the hdf5 file in write mode
    with h5py.File(hdf5_path, "w") as hdf5_file:

        # adding the name to the hdf5 file
        hdf5_file.attrs["name"] = name

        # adding the control ranges to the hdf5 file
        hdf5_file.attrs["controls"] = repr(control_ranges)

        # iterating over all the controls and adding
        # the images to the hdf5 file
        for controls in ControlRange.iterate_controls(control_ranges):
            _add_to_hdf5(camera, controls, avg_over, hdf5_file, progress=progress)

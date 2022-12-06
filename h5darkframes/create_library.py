from collections import OrderedDict
from pathlib import Path
import logging
import h5py
import typing
import cv2
import numpy as np
from numpy import typing as npt
from .camera import Camera, ImageTaker
from .control_range import ControlRange
from .progress import Progress

_logger = logging.getLogger("h5darkframes")


def _get_group(
    hdf5_file: h5py.File,
    controls: typing.OrderedDict[str, int],
    create: bool,
) -> typing.Tuple[typing.Optional[h5py.File], bool]:
    """
    Returns the group in the hdf5 file corresponding
    to the controls, and a boolean indicating if the
    group was created (always 'False' if 'create' is False).

    e.g. if controls is (and 'create' is False):

    ```python
    controls = {'a':1,'b':2}
    ```

    returns hdf5_file[1][2], False.

    Returns None,False if 'create' is False and no such group.
    """

    group = hdf5_file
    created = False
    for _, value in controls.items():
        if str(value) in group:
            group = group[str(value)]
        else:
            if create:
                group = group.require_group(str(value))
                created = True
            else:
                return None, False
    return group, created


def _dump_picture(
    image: npt.ArrayLike,
    directory: Path,
    index: int,
    controls: typing.OrderedDict,
    file_format: str,
) -> None:

    filename = "_".join([f"{key}_{value}" for key, value in controls.items()])
    filename += f"_{index}.{file_format}"

    path = directory / filename

    _logger.debug(f"writing file {path}")

    if file_format == "npy":
        np.save(path, image)
    else:
        cv2.imwrite(path, image)


def _take_and_average_images(
    camera: ImageTaker,
    avg_over: int,
    progress: typing.Optional[Progress] = None,
    controls: typing.Optional[OrderedDict] = None,
    estimated_duration: float = 0,
    dump: typing.Optional[Path] = None,
    dump_format: typing.Optional[str] = None,
) -> npt.ArrayLike:
    images_sum: typing.Optional[npt.ArrayLike] = None
    images_type = None
    for index in range(avg_over):
        _logger.debug("taking picture")
        original_image = camera.picture()
        if dump and dump_format and controls:
            _dump_picture(original_image, dump, index, controls, dump_format)
        if images_type is None:
            images_type = original_image.dtype  # type: ignore
        image_ = original_image.astype(np.uint64)  # type: ignore
        if images_sum is None:
            images_sum = image_
        else:
            images_sum += image_
        if progress is not None:
            if controls is not None:
                progress.picture_taken_feedback(controls, estimated_duration, 1)
    return (images_sum / avg_over).astype(images_type)  # type: ignore


def _add_to_hdf5(
    camera: Camera,
    controls: typing.OrderedDict[str, int],
    avg_over: int,
    hdf5_file: h5py.File,
    progress: typing.Optional[Progress] = None,
    dump: typing.Optional[Path] = None,
    dump_format: typing.Optional[str] = None,
) -> None:
    """
    Has the camera take images, average them and adds this averaged image
    to the hdf5 file, with 'path'
    like hdf5_file[param1.value][param2.value][param3.value]...
    Before taking the image, the camera's configuration is set accordingly.
    """

    _logger.info(f"creating darkframe for {repr(controls)}")

    # for the progress feedback
    estimated_duration = camera.estimate_picture_time(controls)

    # the darkframe for this control set already exists, exit
    create = False
    if _get_group(hdf5_file, controls, create)[0] is not None:
        _logger.info(f"data already exists for {repr(controls)}, skipping")
        if progress is not None:
            progress.picture_taken_feedback(controls, estimated_duration, 1)
        return

    # setting the configuration of the current pictures set
    for control, value in controls.items():
        _logger.info(f"{control}: reaching value of {value}")
        camera.reach_control(control, value, progress=progress)

    # the control values we reached (which may not be the one
    # we asked for)
    applied_controls = OrderedDict()
    for control in controls.keys():
        applied_controls[control] = camera.get_control(control)
    _logger.info(f"reached controls: {repr(applied_controls)}")

    # do the data for these reached controls already exist ?
    # if so, skipping
    create = True
    group, created = _get_group(hdf5_file, applied_controls, create)
    if group is None or not created:
        _logger.info(f"data already exists for {repr(applied_controls)}, skipping")
        if progress is not None:
            progress.picture_taken_feedback(controls, estimated_duration, 1)
        return

    # taking and averaging the pictures
    image = _take_and_average_images(
        camera,
        avg_over,
        progress=progress,
        controls=controls,
        estimated_duration=estimated_duration,
        dump=dump,
        dump_format=dump_format,
    )

    # adding the image to the hdf5 file
    report: str = ", ".join(
        [f"{control}: {value}" for control, value in applied_controls.items()]
    )
    _logger.info(f"creating dataset for {report}")
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
    dump: typing.Optional[Path] = None,
    dump_format: typing.Optional[str] = "npy",
) -> None:
    """Create an hdf5 image library file

    This function will take pictures using
    the specified configuration range. For each configuration, a set of
    'avg_over' pictures are taken and averaged.
    Images can be accessed using instances of 'ImageLibrary'.
    'name' is a (possibly chosen unique) arbitrary string,
    used for identification of the file (can be, for example,
    the serial number of the camera used to take the frames).

    'dump' is an optional path to an existing folder into
    which all picture taken will be written into a file of format
    'dump_format' (which default value is npy, i.e. numpy array).
    Note that 'all' really means all, i.e. before averaging
    (if 'avg_over' is 10, 10 pictures will be dumped per control
    range).
    """

    # opening the hdf5 file in write mode
    with h5py.File(hdf5_path, "a") as hdf5_file:

        # adding the name to the hdf5 file
        hdf5_file.attrs["name"] = name

        # adding the control ranges to the hdf5 file
        hdf5_file.attrs["controls"] = repr(control_ranges)

        # iterating over all the controls and adding
        # the images to the hdf5 file
        for controls in ControlRange.iterate_controls(control_ranges):
            _add_to_hdf5(
                camera,
                controls,
                avg_over,
                hdf5_file,
                progress=progress,
                dump=dump,
                dump_format=dump_format,
            )

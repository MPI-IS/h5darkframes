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




def _add_to_hdf5(
        camera: Camera,
        controllables: Controllables,
        desired_param: Param,
        avg_over: int,
        hdf5_file: h5py.File,
        overwrite: bool
) -> None:

    if not overwrite:
        # we should not overwrite, so testing if the image is
        # already present in the library
        create = False
        group, created = h5.get_group(h5,desired_param,create)
        if group is not None:
            # already exists, so exit
            return
            
    # setting the configuration of the current pictures set
    for controllable, p in zip(controllables, param):
        camera.reach_control(controllable,p)

    # the param values we reached (no necessarily the one
    # we asked for)
    applied_param: Param = camera.get_param(controllables)

    # do the data for these reached controls already exist ?
    # if so, skipping
    create = False
    group, created = h5.get_group(h5,applied_param,create)
    if group is not None:
        # already exists, so exit
        return

    # taking and averaging the pictures
    image = camera.averaged_picture(controllables, applied_param, avg_over)
    
    # adding the image to the hdf5 file
    group.create_dataset("image", data=image)

    # add the camera current configuration to the group
    group.attrs["camera_config"] = repr(camera.get_configuration())


def library(
    name: str,
    camera: Camera,
    control_ranges: OrderedDict[str, ControlRange],
    avg_over: int,
    hdf5_path: Path,
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

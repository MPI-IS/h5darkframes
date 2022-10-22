from collections import OrderedDict
import datetime
import itertools
import alive_progress
from pathlib import Path
import time
import h5py
import typing
import numpy as np
from .camera import Camera
from .control_range import ControlRange
from .iterations import iterate_ints, interate_controls


        

def _add_to_hdf5(
        camera: Camera,
        controls: typing.Mapping[str,int],
        avg_over: int,
        hdf5_file: h5py.File,
        progress: typing.Optional[Progress]=None
) -> float:
    """
    Has the camera take images, average them and adds this averaged image
    to the hdf5 file, with 'path'
    like hdf5_file[param1.value][param2.value][param3.value]...
    Before taking the image, the camera's configuration is set accordingly.
    Returns the estimated duration taken by the function to complete.
    """

    for control,value in controls.items():
        camera.reach_control(control,value,progress=progress)
    
    for 
    # getting the configuration values, which may or may not
    # be what we asked for (e.g. when setting temperature)
    all_controls = camera.get_controls()
    current_controls = OrderedDict()
    for control in controls.keys():
        current_controls[control] = all_controls[control].value

    # taking and averaging the pictures
    images: typing.List[FlattenData] = []
    for _ in range(avg_over):
        if progress is not None:
            str_controls = ", ".join(
                [f"{key}: {value}" for key, value in current_controls.items()]
            )
            progress.text = str(
                f"taking picture {current_nb_pics}/{total_nb_pics} " f"({str_controls})"
            )
        images.append(camera.capture().get_data())
        if progress is not None:
            progress(exposure)
            if current_nb_pics is not None:
                current_nb_pics += 1
            else:
                current_nb_pics = 1
    image = np.mean(images, axis=0)

    # adding the image to the hdf5 file
    group = hdf5_file
    for control, value in current_controls.items():
        group = group.require_group(str(value))
    group.create_dataset("image", data=image)

    # add the camera current configuration to the group
    group.attrs["camera_config"] = camera.to_toml()

    return current_nb_pics


def library(
        name: str,
        camera: Camera,
        control_ranges: OrderedDict[str, ControlRange],
        avg_over: int,
        hdf5_path: Path,
        callback: typing.Optional[typing.Callable[[float,int],None]]=None
) -> int:
    """ Create an hdf5 image library file

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
            hdf5_file.attrs["controls"] = repr(controls)

            # adding the camera's configuration to the hdf5 file
            hdf5_file.attrs["configuration"] = repr(camera.get_configuration())
            
            # counting the number of images saved
            nb_images = 0

            # iterating over all the controls and adding
            # the images to the hdf5 file
            for controls in ControlRange.iterate_controls(control_ranges)
                duration = _add_to_hdf5(
                    camera,
                    controls,
                    hdf5_file,
                    avg_over
                )
                if callback is not None:
                    callback(duration)

    return nb_images

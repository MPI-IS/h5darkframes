import os
import typing
import alive_progress
from pathlib import Path
from .camera import Camera
from .progress import AliveBarProgress
from .create_library import library
from .toml_config import read_config
from .duration_estimate import estimate_total_duration

_root_dir = os.getcwd()

def set_root_dir(self, path: Path):
    global _root_dir
    _root_dir = path

    
def get_darkframes_config_path(check_exists: bool = True) -> Path:
    path = Path(_root_dir) / "darkframes.toml"
    if check_exists:
        if not path.is_file():
            raise FileNotFoundError(
                "\ncould not find a file 'darkframes.toml' in the current "
                "directory.\n"
            )
    return path


def get_darkframes_path(check_exists: bool = True) -> Path:
    path = Path(_root_dir) / "darkframes.hdf5"
    if check_exists:
        if not path.is_file():
            raise FileNotFoundError(
                "\ncould not find a file 'darkframes.hdf5' in the current "
                "directory.\n"
            )
    return path


def darkframes_config(camera_class: typing.Type[Camera], **kwargs) -> Path:
    # path to configuration file
    path = get_darkframes_config_path(check_exists=False)
    # generating file with decent default values
    camera_class.generate_config_file(path, **kwargs)
    # returning path to generated file
    return path


class _no_progress_bar:

    def __init__(self,
                 duration: int,
                 dual_line: bool =True,
                 title : str ="darkframes library creation"):
        pass

    def __enter__(self):
        return None

    def __exit__(self,_,__,___):
        return


def darkframes_library(
        camera_class: typing.Type[Camera],
        libname: str,
        progress_bar: bool,
        **camera_kwargs
) -> Path:

    # path to configuration file
    config_path = get_darkframes_config_path()

    # path to library file
    path = get_darkframes_path(check_exists=False)

    # reading configuration file
    control_ranges, average_over = read_config(config_path)

    # configuring the camera
    camera = camera_class.configure(config_path, **camera_kwargs)

    # estimating duration and number of pics
    duration, nb_pics = estimate_total_duration(camera,control_ranges,average_over)
    
    # adding a progress bar
    if progress_bar:
        progress_context_manager = alive_progress.alive_bar
    else:
        progress_context_manager = _no_progress_bar

    # creating library
    with progress_context_manager(
            nb_pics,
            dual_line=True,
            title="darkframes library creation",
    ) as progress_instance:
        if progress_instance:
            progress_bar = AliveBarProgress(duration, nb_pics, progress_instance)
        else:
            progress_bar = None
        library(libname, camera, control_ranges, average_over, path, progress=progress_bar)

    # stopping camera
    camera.stop()
        
    # returning path to created file
    return path

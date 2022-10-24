import os
from pathlib import Path
from .camera import Camera
from .progress import AliveBarProgress
from .create_library import library
from .toml_config import read_config
from .duration_estimate import estimate_total_duration

_root_dir = os.getcwd()


def _get_darkframes_config_path(check_exists: bool = True) -> Path:
    path = Path(_root_dir) / "darkframes.toml"
    if check_exists:
        if not path.is_file():
            raise FileNotFoundError(
                "\ncould not find a file 'darkframes.toml' in the current "
                "directory. You may create one by calling zwo-asi-darkframes-config\n"
            )
    return path


def get_darkframes_path(check_exists: bool = True) -> Path:
    path = Path(_root_dir) / "darkframes.hdf5"
    if check_exists:
        if not path.is_file():
            raise FileNotFoundError(
                "\ncould not find a file 'darkframes.toml' in the current "
                "directory. You may create one by calling zwo-asi-darkframes-config\n"
            )
    return path


def darkframes_config(camera: Camera) -> Path:
    # path to configuration file
    path = _get_darkframes_config_path(check_exists=False)
    # generating file with decent default values
    camera.generate_config_file(path)
    # returning path to generated file
    return path


def darkframes_library(camera: Camera, libname: str, progress_bar: bool) -> Path:

    # path to configuration file
    config_path = _get_darkframes_config_path()

    # path to library file
    path = get_darkframes_path(check_exists=False)

    # reading configuration file
    control_ranges, average_over = read_config(config_path)

    # configuring the camera
    camera.configure(config_path)

    # adding a progress bar
    if progress_bar:
        duration, nb_pics = estimate_total_duration(
            camera, control_ranges, average_over
        )
        progress = AliveBarProgress(duration, nb_pics)
    else:
        progress = None

    # creating library
    library(libname, camera, control_ranges, average_over, path, progress=progress)

    # returning path to created file
    return path

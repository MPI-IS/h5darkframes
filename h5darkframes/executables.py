import os
import typing
import alive_progress
import logging
from pathlib import Path
from .camera import Camera
from .progress import AliveBarProgress
from .create_library import library
from .toml_config import read_config
from .duration_estimate import estimate_total_duration

_root_dir = Path(os.getcwd())


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


def get_logs_path() -> Path:
    path = Path(_root_dir) / "darkframes.logs"
    return path


def darkframes_config(camera_class: typing.Type[Camera], **kwargs) -> Path:
    # path to configuration file
    path = get_darkframes_config_path(check_exists=False)
    # generating file with decent default values
    camera_class.generate_config_file(path, **kwargs)
    # returning path to generated file
    return path


class _no_progress_bar:
    def __init__(
        self,
        duration: int,
        dual_line: bool = True,
        title: str = "darkframes library creation",
    ):
        pass

    def __enter__(self):
        return None

    def __exit__(self, _, __, ___):
        return


def _append_user_feedback(path: Path) -> bool:
    question = str(
        f"a file {path} already exists. "
        "It will be updated with new pictures. Continue ? [y/n]"
    )
    while True:
        answer = input(question)
        if answer.lower().strip() == "y":
            return True
        if answer.lower().strip() == "n":
            return False


def darkframes_library(
    camera_class: typing.Type[Camera],
    libname: str,
    progress_bar: bool,
    dump: typing.Optional[Path],
    dump_format: typing.Optional[str],
    **camera_kwargs,
) -> Path:

    # path to configuration file
    config_path = get_darkframes_config_path()

    # path to library file
    path = get_darkframes_path(check_exists=False)

    # if a file already exists, exiting
    if path.is_file():
        append = _append_user_feedback(path)
        if not append:
            raise RuntimeError("user exit")

    # reading configuration file
    control_ranges, average_over = read_config(config_path)

    # configuring the camera
    camera = typing.cast(Camera, camera_class.configure(config_path, **camera_kwargs))

    # estimating duration and number of pics
    duration, nb_pics = estimate_total_duration(camera, control_ranges, average_over)

    # adding a progress bar
    if progress_bar:
        progress_context_manager = alive_progress.alive_bar
    else:
        progress_context_manager = _no_progress_bar

    # logging what is happening
    # in a file (in the current directory)
    logfile = get_logs_path()
    file_handler = logging.FileHandler(logfile)
    logging.basicConfig(level=logging.INFO, handlers=(file_handler,))

    # creating library
    with progress_context_manager(
        nb_pics,
        dual_line=True,
        title="darkframes library creation",
    ) as progress_instance:
        progress_bar_: typing.Optional[AliveBarProgress]
        if progress_instance:
            progress_bar_ = AliveBarProgress(duration, nb_pics, progress_instance)
        else:
            progress_bar_ = None
        library(
            libname,
            camera,
            control_ranges,
            average_over,
            path,
            progress=progress_bar_,
            dump=dump,
            dump_format=dump_format,
        )

    # stopping camera
    camera.stop()

    # returning path to created file
    return path

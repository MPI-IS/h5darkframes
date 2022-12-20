import typing
import cv2
import os
import logging
import argparse
import numpy as np
from pathlib import Path
from .get_image import ImageNotFoundError
from .types import Params, Controllables
from .image_library import ImageLibrary
from .image_stats import ImageStats
from . import executables
from .fuse_libraries import fuse_libraries
from . import validation
from .substract import substract


def execute(f: typing.Callable[[], None]) -> typing.Callable[[], None]:
    def run():
        print()
        try:
            f()
        except Exception as e:
            import traceback

            print(traceback.format_exc())
            print(f"error ({e.__class__.__name__}):\n{e}\n")
            exit(1)
        print()
        exit(0)

    return run


@execute
def asi_zwo_darkframes_config():

    try:
        from .asi_zwo import AsiZwoCamera
    except ImportError:
        raise ImportError(
            "failed to import camera_zwo_asi. See: https://github.com/MPI-IS/camera_zwo_asi"
        )

    # reading camera index
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--index",
        type=int,
        required=False,
        help="index of the camera to use (0 if not specified)",
    )
    args = parser.parse_args()
    if args.index:
        index = args.index
    else:
        index = 0

    path = executables.darkframes_config(AsiZwoCamera, index=index)

    print(
        f"Generated the darkframes configuration file {path}.\n"
        "Edit and call zwo-asi-darkframes to generate the darkframes "
        "library file."
    )


@execute
def asi_zwo_darkframes_library():

    try:
        from .asi_zwo import AsiZwoCamera
    except ImportError:
        raise ImportError(
            "failed to import camera_zwo_asi. See: https://github.com/MPI-IS/camera_zwo_asi"
        )

    # the user must give a name to the library
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--name",
        type=str,
        required=True,
        help="name of the library",
    )

    # the user may require images to be saved
    parser.add_argument(
        "--fileformat",
        type=str,
        required=False,
        help=str(
            "if specified, all image taken will also be dumped "
            "in the current directory in files of the specified "
            "format (*.npy is numpy). Meant for debug."
        ),
    )

    args = parser.parse_args()

    if args.fileformat:
        directory = Path(os.getcwd())
        fileformat = args.fileformat
    else:
        directory = None
        fileformat = None

    # using the first camera
    camera_kwargs = {"index": 0}

    # which camera we use
    camera_class = AsiZwoCamera

    # creating the library
    progress_bar = True
    path = executables.darkframes_library(
        camera_class, args.name, progress_bar, directory, fileformat, **camera_kwargs
    )

    # informing user
    print(f"\ncreated the file {path}\n")


@execute
def darkframes_perform() -> None:

    import camera_zwo_asi
    import cv2

    config = Path(os.getcwd()) / "zwo_asi.toml"
    if not config.is_file():
        raise FileNotFoundError(
            "failed to find camera zwo asi configuration file: " f"{config}"
        )

    camera = camera_zwo_asi.Camera(0)
    camera.configure_from_toml(config)

    print("---capturing image")
    image = camera.capture().get_image()

    controls = camera.get_controls()
    temperature = int(0.5 + controls["Temperature"].value / 10.0)
    exposure = controls["Exposure"].value
    param = (temperature, exposure)
    print("---image param:", param)

    path = executables.get_darkframes_path()
    with ImageLibrary(path) as il:

        try:
            neighbors = il.get_interpolation_neighbors(param)
        except ValueError:
            neighbors = [il.get_closest(param)]
        print("---neighbors")
        for n in neighbors:
            print("\t", n)

        print("---generating darkframe")
        if param in neighbors:
            darkframe, _ = il.get(param)
        else:
            darkframe = il.generate_darkframe(param, neighbors)

        print("---substracting darkframe")
        subimage = substract(image, darkframe)

        img_path = Path(os.getcwd()) / "image.tiff"
        darkframe_path = Path(os.getcwd()) / "darkframe.tiff"
        subimage_path = Path(os.getcwd()) / "subimage.tiff"

        print("---printing files")
        cv2.imwrite(str(img_path), image)
        cv2.imwrite(str(darkframe_path), darkframe)
        cv2.imwrite(str(subimage_path), subimage)


@execute
def darkframes_validation() -> None:

    path = executables.get_darkframes_path()
    validation.print_leave_one_out(path)


def _darkframes_info_pretty(library: ImageLibrary) -> None:

    controllables: Controllables = library.controllables()

    from rich.table import Table
    from rich.console import Console
    from rich.progress import track

    table = Table(title="configurations")
    for controllable in controllables:
        table.add_column(controllable)

    stat_keys = ("shape", "min", "max", "avg", "std")
    for key in stat_keys:
        table.add_column(key)

    print()
    params: Params = sorted(library.params())
    for param in track(params, description="reading images..."):
        row: typing.List[str] = []
        for p in param:
            row.append(str(p))
        try:
            c = {controllable: p for controllable, p in zip(controllables, param)}
            image, _ = library.get(c)
        except ImageNotFoundError:
            for key in stat_keys:
                row.append("-")
        else:
            image_stats = ImageStats(image)
            row.extend(image_stats.pretty())
        table.add_row(*row)

    print()
    console = Console()
    console.print(table)
    print()


def _darkframes_info_fast(library: ImageLibrary, stats: bool) -> None:

    params: Params = library.params()
    controllables: Controllables = library.controllables()
    print(f"\nconfigurations\n{'-'*14}")
    image_stats = ""
    for param in params:
        if stats:
            try:
                c = {controllable: p for p, controllable in zip(param, controllables)}
                image, _ = library.get(c)
            except ImageNotFoundError:
                image_stats = "image not found"
            else:
                image_stats = str(ImageStats(image))
        print(
            "\t".join(
                [
                    f"{controllable}: {p}"
                    for p, controllable in zip(param, controllables)
                ]
            )
            + f"\t\t{image_stats}"
        )
    print()


@execute
def darkframes_info():

    # if user passes the --stats flag, stats of pictures will be displayed
    parser = argparse.ArgumentParser()
    parser.add_argument("--stats", action=argparse.BooleanOptionalAction)
    parser.add_argument("--pretty", action=argparse.BooleanOptionalAction)
    args = parser.parse_args()

    # path to configuration file
    path = executables.get_darkframes_path()

    with ImageLibrary(path) as library:

        # basic infos
        library_name = library.name()
        control_ranges = library.ranges()

        if isinstance(control_ranges, list):
            control_ranges = control_ranges[0]

        nb_pics = library.nb_pics()
        print(
            str(
                f"\nLibrary: {library_name}\n"
                f"Image Library of {nb_pics} pictures.\n\n"
                f"parameters\n{'-'*10}"
            )
        )

        # control ranges used to create the file
        def _print_range(control_ranges_):
            for name, cr in control_ranges_.items():
                print(f"{name}:\t{cr}")

        if isinstance(control_ranges, list):
            for control_ranges_ in control_ranges:
                _print_range(control_ranges_)
        else:
            _print_range(control_ranges)

        if not args.stats:
            _darkframes_info_fast(library, args.stats)
            return

        if not args.pretty:
            _darkframes_info_fast(library, args.stats)
        else:
            _darkframes_info_pretty(library)


@execute
def darkframe_neighbors():

    path = executables.get_darkframes_path()
    with ImageLibrary(path) as il:

        controllables = il.controllables()

        parser = argparse.ArgumentParser()

        # each control parameter has its own argument
        for control in controllables:
            parser.add_argument(
                f"--{control}",
                type=int,
                required=True,
                help="the value for the control",
            )

        args = parser.parse_args()

        param = {control: int(getattr(args, control)) for control in controllables}

        try:
            il.get(param)
        except ImageNotFoundError:
            pass
        else:
            print("in the darkframes library")
            return

        try:
            neighbors = il.get_interpolation_neighbors(param)
        except ValueError:
            pass
        else:
            print("interpolation neighbors:")
            for neighbor in neighbors:
                print(neighbor)

        neighbor = il.get_closest(param)
        print("closest neighbor:")
        print(neighbor)


@execute
def darkframe_display():

    path = executables.get_darkframes_path()
    library = ImageLibrary(path)
    controllables = library.controllables()

    parser = argparse.ArgumentParser()

    # each control parameter has its own argument
    for control in controllables:
        parser.add_argument(
            f"--{control}", type=int, required=True, help="the value for the control"
        )

    # to make the image more salient
    parser.add_argument(
        "--multiplier",
        type=int,
        required=False,
        default=1,
        help="pixels values will be multiplied by it",
    )

    # optional resize
    parser.add_argument(
        "--resize",
        type=float,
        required=False,
        default=1.0,
        help="resize of the image during display",
    )

    args = parser.parse_args()

    control_values = {control: int(getattr(args, control)) for control in controllables}

    image, image_controls = library.get(control_values, nparray=True)

    if args.multiplier != 1.0:
        image = image * args.multiplier

    if args.multiplier != 1.0:
        image64 = image.astype(np.uint64)
        image64 = image64 * args.multiplier
        image64 = np.clip(image64, 0, np.iinfo(np.uint16).max)
        image = image64.astype(np.uint16)

    if args.resize != 1.0:
        shape = tuple([int(s / args.resize + 0.5) for s in image.shape])
        image = cv2.resize(image, shape, interpolation=cv2.INTER_NEAREST)

    cv2.imshow(str(image_controls), image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


@execute
def fuse():

    # the user must give a name to the library
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--name",
        type=str,
        required=True,
        help="name of the resulting library",
    )
    args = parser.parse_args()

    # we will attempt to fuse all
    # "hdf5" files present in the current
    # folder
    root_dir = Path(os.getcwd())
    files = list(root_dir.glob("*.hdf5"))

    # no hdf5 file, exiting
    if not files:
        raise FileNotFoundError(
            "failed to find any *.hdf5 file in the " "current folder"
        )

    # the file into which all libraries will be fused
    target_path = root_dir / "darkframes.hdf5(fused)"

    # it already exists, exiting
    if target_path.is_file():
        raise ValueError(f"can not generate {target_path}: " "file already exists")

    # logging, for user information
    logging.basicConfig(
        level=logging.INFO,
        format="[%(levelname)s] %(asctime)s | %(name)s |  %(message)s",
        datefmt="%d-%b-%y %H:%M:%S",
    )

    # fusing
    fuse_libraries(args.name, target_path, files)

import typing
import argparse
from .image_library import ImageLibrary
from . import executables


def execute(f: typing.Callable[[], None]) -> typing.Callable[[], None]:
    def run():
        print()
        try:
            f()
        except Exception as e:
            print(f"error:\n{e.__class__.__name__}: {e}\n")
            exit(1)
        print()
        exit(0)

    return run


def zwo_asi(f: typing.Callable[[], None]) -> typing.Callable[[], None]:
    def run():
        try:
            from .asi_zwo import AsiZwoCamera
        except ImportError:
            raise ImportError(
                "failed to import camera_zwo_asi. See: https://github.com/MPI-IS/camera_zwo_asi"
            )
        f()

    return run


@execute
@zwo_asi
def asi_zwo_darkframes_config():

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

    path = executables.darkframes_config(camera,index=index)

    print(
        f"Generated the darkframes configuration file {path}.\n"
        "Edit and call zwo-asi-darkframes to generate the darkframes "
        "library file."
    )


@execute
@zwo_asi
def asi_zwo_darkframes_library():

    # in case there are more than 1 camera connected
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--index",
        type=int,
        required=False,
        help="index of the camera to use (0 if not specified)",
    )

    # the user must give a name to the library
    parser.add_argument(
        "--name",
        type=str,
        required=True,
        help="name of the library",
    )

    # handle to the camera
    args = parser.parse_args()
    if args.index:
        index = args.index
    else:
        index = 0
    camera_class = 
    camera = Camera(index)  # noqa: F821

    # generating the library
    with alive_progress.alive_bar(
            estimated_duration,
            dual_line=True,
            title="darkframes library creation",
    ) as alive:
        progress_bar = AliveProgressBar(duration, nb_pics, alive)
        path = executables.darkframes_library(camera, args.name, progress_bar)

    # informing user
    print(f"\ncreated the file {path}\n")


@execute
def darkframes_info():

    # path to configuration file
    path = executables.get_darkframes_path()

    library = ImageLibrary(path)

    library_name = library.name()

    control_ranges = library.params()

    nb_pics = 1
    for cr in control_ranges.values():
        nb_pics = nb_pics * len(cr.get_values())

    r = [
        str(
            f"Library: {library_name}\n"
            f"Image Library of {nb_pics} pictures.\n"
            f"parameters\n{'-'*10}"
        )
    ]

    for name, cr in control_ranges.items():
        r.append(str(cr, name))

    print()
    print("\n".join(r))
    print()


@execute
def darkframe_display():

    path = executables.get_darkframes_path()

    library = ImageLibrary(path)
    controls = list(library.params().keys())

    parser = argparse.ArgumentParser()

    # each control parameter has its own argument
    for control in controls:
        parser.add_argument(
            f"--{control}", type=int, required=True, help="the value for the control"
        )

    # to make the image more salient
    parser.add_argument(
        "--multiplier",
        type=float,
        required=False,
        default=1.0,
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

    control_values = {control: int(getattr(args, control)) for control in controls}

    image, image_controls = library.get(control_values)

    if args.multiplier != 1.0:
        image._data = image.get_data() * args.multiplier

    params = ", ".join(
        [f"{control}: {value}" for control, value in image_controls.items()]
    )

    image.display(label=params, resize=args.resize)

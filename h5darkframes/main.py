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
    args = parser.parse_args()

    # using the first camera
    camera_kwargs = {"index": 0}

    # which camera we use
    camera_class = AsiZwoCamera

    # creating the library
    progress_bar = True
    path = executables.darkframes_library(
        camera_class, args.name, progress_bar, **camera_kwargs
    )

    # informing user
    print(f"\ncreated the file {path}\n")


@execute
def darkframes_info():

    # path to configuration file
    path = executables.get_darkframes_path()

    with ImageLibrary(path) as library:

        library_name = library.name()

        control_ranges = library.params()

        nb_pics = 1
        for cr in control_ranges.values():
            nb_pics = nb_pics * len(cr.get_values())

        r = [
            str(
                f"Library: {library_name}\n"
                f"Image Library of {nb_pics} pictures.\n\n"
                f"parameters\n{'-'*10}"
            )
        ]

        for name, cr in control_ranges.items():
            r.append(f"{name}: {cr}")

        configs = library.configs()
        r.append(f"\nconfigurations\n{'-'*14}")
        for config in configs:
            r.append("\t".join([f"{key}: {value}" for key, value in config.items()]))

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

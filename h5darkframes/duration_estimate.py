import typing
from collections import OrderedDict
from .camera import Camera
from .control_range import ControlRange


def estimate_total_duration(
    camera: Camera,
    control_ranges: OrderedDict[str, ControlRange],
    avg_over: int,
) -> typing.Tuple[int, int]:
    """
    Return an estimation of how long capturing all darkframes will
    take (in seconds).

    Returns
    -------
       the expected duration (in seconds) and the number of pictures
       that will be taken.
    """

    all_values: typing.List[typing.Dict[str, int]] = list(
        ControlRange.iterate_controls(control_ranges)
    )
    total_time_ = sum(
        [
            camera.estimate_picture_time(
                {control: values[control] for control in control_ranges.keys()}
            )
            * avg_over
            for values in all_values
        ]
    )
    total_time = int(total_time_ + 0.5)
    nb_pics = len(all_values) * avg_over
    return total_time, nb_pics

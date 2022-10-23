import alive_progress
import typing
from collections import OrderedDict
from .control_range import ControlRange
from .camera import Camera


AliveBarProgress = alive_progress.core.progress.__AliveBarHandle


def _estimate_total_duration(
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

    controls = list(control_ranges.keys())
    all_values = list(
        ControlRange.iterate_controls([control_ranges[control] for control in controls])
    )
    total_time = sum(
        [
            camera.estimate_picture_time(
                {control: value for control, value in zip(controls, values)}
            )
            * avg_over
            for values in all_values
        ]
    )
    nb_pics = len(all_values) * avg_over
    return total_time, nb_pics


class Progress:
    def __init__(
        self,
        camera: Camera,
        control_ranges: typing.OrderedDict[str, ControlRange],
        avg_over: int,
    ):
        self._estimated_duration, self._nb_pics = _estimate_total_duration(
            camera, control_ranges, avg_over
        )

    def reach_control_feedback(
        self,
        control: str,
        current_value: int,
        target_value: int,
        tolerance: int,
        duration: float,
        timeout: float,
    ) -> None:
        pass

    def picture_taken_feedback(
        self, controls: typing.OrderedDict[str, int], time_delta: float, nb_pics: int
    ) -> None:
        raise NotImplementedError()


class AliveBarProgress(Progress):
    def __init__(
        self,
        camera: Camera,
        control_ranges: typing.OrderedDict[str, ControlRange],
        avg_over: int,
    ):
        super().__init__(camera, control_ranges, avg_over)
        self._bar = alive_progress.alive_bar(
            super()._estimated_duration,
            dual_line=True,
            title="darkframes library creation",
        )
        self._pics = 0

    def read_control_feedack(
        self,
        control: str,
        current_value: int,
        target_value: int,
        tolerance: int,
        duration: float,
        timeout: float,
    ) -> None:
        f = str(
            f"setting {control} to {target_value} "
            f"(tolerance of {tolerance}) "
            f"running for {duration} with timeout of {timeout}"
        )
        self._bar.text(f)

    def picture_taken_feedback(
        self, controls: typing.OrderedDict[str, int], time_delta: float, nb_pics: int
    ) -> None:
        self._pics += nb_pics
        self._bar(int(time_delta) + 0.5)
        str_controls = ", ".join([f"{key}: {value}" for key, value in controls.items()])
        self._bar.text = str(
            f"taking picture {self._pics}/{super()._nb_pics} " f"({str_controls})"
        )

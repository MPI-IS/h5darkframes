from .camera import Camera


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
        _iterate_controls([control_ranges[control] for control in controls])
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
    nb_pics = len(all_controls) * avg_over
    return total_time, nb_pics


class Progress:
    def __init__(
        self,
        camera: Camera,
        control_ranges: typing.OrderedDict[str, int],
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
    )->None:
        pass
        
    def update(self, time_delta, nb_pics) -> None:
        raise NotImplementedError()

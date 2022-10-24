import alive_progress
import typing


class Progress:
    def __init__(
        self,
        duration: int,
        nb_pics: int,
    ):
        self._estimated_duration = duration
        self._nb_pics = nb_pics

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
        duration: int,
        nb_pics: int,
    ):
        super().__init__(duration, nb_pics)
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

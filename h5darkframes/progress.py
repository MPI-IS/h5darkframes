import typing


class Progress:
    def __init__(
        self,
        duration: int,
        nb_pics: int,
    ):
        self._estimated_duration = duration
        self._nb_pics = nb_pics

    def config_feedback(
        self,
        control: str,
        current_value: int,
        target_value: int,
        tolerance: int,
        duration: float,
        timeout: float,
    ) -> None:
        raise NotImplementedError()

    def picture_feedback(
            self, controllables: Controllables, param: Param
    ) -> None:
        raise NotImplementedError()


class AliveBarProgress(Progress):
    def __init__(self, duration: int, nb_pics: int, bar):
        super().__init__(duration, nb_pics)
        self._bar = bar
        self._pics = 0

    def config_feedback(
        self,
        control: str,
        current_value: int,
        target_value: int,
        tolerance: int,
        duration: float,
        timeout: float,
    ) -> None:
        duration_ = "{:0.2f}".format(duration)
        f = str(
            f"setting {control} to {target_value}: {current_value} "
            f"(tolerance of {tolerance}) "
            f"running for {duration_} with timeout of {timeout}"
        )
        self._bar.text(f)

    def picture_feedback(
            self, controllables: Controllables, param: Param
    ) -> None:
        self._pics += nb_pics
        self._bar(nb_pics)
        str_controls = ", ".join([f"{key}: {value}" for key, value in zip(controllables,param)])
        self._bar.text = str(
            f"taking picture {self._pics}/{self._nb_pics} " f"({str_controls})"
        )

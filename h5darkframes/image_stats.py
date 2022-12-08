import typing
from numpy import typing as npt
import numpy as np


class ImageStats:
    def __init__(self, image: npt.ArrayLike) -> None:
        self.shape: typing.Tuple[int, ...] = image.shape  # type: ignore
        self.min = np.min(image)
        self.max = np.max(image)
        self.avg = np.average(image)  # type: ignore
        self.std = np.std(image)  # type: ignore

    def pretty(self) -> typing.List[str]:
        return [
            str(self.shape),
            str(self.min),
            str(self.max),
            str("%.2f" % self.avg),
            str("%.2f" % self.std),
        ]

    def __str__(self):
        return str(
            f"shape: {self.shape} min: {self.min} max: {self.max} "
            f"average: {'%.2f' % self.avg} std: {'%.2f' % self.std}"
        )

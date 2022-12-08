import typing
import numpy as np
from numpy import typing as npt
import h5darkframes as dark


class PseudoH5File:
    def __init__(
        self,
        controllables: dark.types.Controllables,
        param_images: dark.types.ParamImages,
    ) -> None:
        self._d: typing.Dict[str, typing.Union[int, npt.ArrayList]] = {}
        self._controllables = controllables
        self._add(self._d, param_images)

    @staticmethod
    def _add(
        main_d: typing.Dict[str, typing.Union[int, npt.ArrayList]],
        param_images: dark.types.ParamImages,
    ) -> None:

        param: typing.Tuple[int, ...]
        image: npt.ArrayLike

        for param, image in param_image.items():
            d = main_d
            for value in param:
                try:
                    d = d[value]
                except KeyError:
                    d[value] = {}
                    d = d[value]

            d["image"] = image


def test_get_neighbors():
    def _image(value: int) -> npt.ArrayLike:
        return np.zeros((10, 10), np.uint16) + value

    def _param(x: int, y: int) -> typing.Tuple[typing.Tuple[int, int], npt.ArrayLike]:
        return ((x, y), _image(x + y))

    controllables = ("row", "column")

    rows = (1, 3)
    cols = (3, 5, 7, 9)

    param_images: dark.types.ParamImages = {
        p[0]: p[1] for p in [_param(x, y) for x in rows for y in cols]
    }

    h5 = PseudoH5File(controllables, param_images)

    target = (2, 4)

    neighbors = dark.neighbors.get_neighbors(h5, target)

    expected = ((1, 3), (3, 3), (3, 5), (1, 5))

    for e in expected:
        assert e in neighbors

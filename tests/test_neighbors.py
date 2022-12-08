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
        self._d: typing.Dict[typing.Any, typing.Any] = {}
        self._controllables = controllables
        self._add(self._d, param_images)

    @staticmethod
    def _add(
        main_d: typing.Dict[typing.Any, typing.Any],
        param_images: dark.types.ParamImages,
    ) -> None:

        param: typing.Tuple[int, ...]
        image: npt.ArrayLike

        for param, image in param_images.items():
            d = main_d
            for value in param:
                try:
                    d = d[str(value)]
                except KeyError:
                    d[str(value)] = {}
                    d = d[str(value)]

            d["image"] = image
            
    def get(self)->typing.Dict[typing.Any,typing.Any]:
        return self._d

def test_neighbor_indexes():

    values = [0,1,2,3,4,5,6,7]
    
    target = 5
    low,high = dark.neighbors._neighbor_indexes(values,target)
    assert low == 5
    assert high is None

    target = 0
    low,high = dark.neighbors._neighbor_indexes(values,target)
    assert low == 0
    assert high is None

    target = 7
    low,high = dark.neighbors._neighbor_indexes(values,target)
    assert low == 7
    assert high is None

    target = -1
    low,high = dark.neighbors._neighbor_indexes(values,target)
    assert low is None
    assert high is None

    target = 8
    low,high = dark.neighbors._neighbor_indexes(values,target)
    assert low is None
    assert high is None

    target = 3
    values = [0,1,2,4,5,6]
    low,high = dark.neighbors._neighbor_indexes(values,target)
    assert low == 2
    assert high == 3
    

def test_get_neighbors():
    def _image(value: int) -> npt.ArrayLike:
        return np.zeros((2, 2), np.uint16) + value

    def _param(x: int, y: int) -> typing.Tuple[typing.Tuple[int, int], npt.ArrayLike]:
        return ((x, y), _image(x + y))

    controllables = ("row", "column")

    rows = (1, 3)
    cols = (3, 5, 7, 9)

    param_images: dark.types.ParamImages = {
        p[0]: p[1] for p in [_param(x, y) for x in rows for y in cols]
    }

    h5 = PseudoH5File(controllables, param_images).get()

    target = (2, 4)
    neighbors = dark.neighbors.get_neighbors(h5, target)
    assert len(neighbors)==4
    expected = ((1, 3), (3, 3), (3, 5), (1, 5))
    for e in expected:
        assert e in neighbors

    average_image = dark.neighbors.average_neighbors(
        target,(1,3),(3,9),neighbors
    )
    s = [sum(e) for e in expected]
    expected_image_value = sum([sum(e) for e in expected])/len(expected)
    assert average_image[0][0] == expected_image_value
    
    target = (0, 0)
    neighbors = dark.neighbors.get_neighbors(h5, target)
    assert not neighbors

    target = (4, 4)
    neighbors = dark.neighbors.get_neighbors(h5, target)
    assert not neighbors

    target = (4,9)
    neighbors = dark.neighbors.get_neighbors(h5, target)
    assert not neighbors
    closest,_ = dark.get_image.get_image(target,h5,False,True)
    assert closest[0][0] == 12  # (3+9)

    target = (3,2)
    neighbors = dark.neighbors.get_neighbors(h5, target)
    assert not neighbors
    closest,_ = dark.get_image.get_image(target,h5,False,True)
    assert closest[0][0] == 6  # (3+3)


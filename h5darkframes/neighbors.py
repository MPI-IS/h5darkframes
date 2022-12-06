import typing
import h5py
import copy
from numpy import typing as npt
from .types import Controllables, Ramges, Params, ParamImages


def _neighbors(
    h5: h5py.File,
    target_values: typing.Tuple[int, ...],
    neighbors: ParamImages,
    current: typing.List[int] = [],
    index: int = 0,
) -> bool:

    if "image" in h5.keys():
        img: npt.ArrayLike = hdf5_file["image"]
        neighbors[current] = img
        return True

    keys = sorted(list([int(k) for k in h5.keys()]))
    d = [abs(target_values[index] - k) for k in keys]
    index_min = min(range(len(d)), key=d.__getitem__)
    if index_min == 0:
        lower, higher = None, None if target < keys[index_min] else 0, 1
    elif index_min == len(d) - 1:
        lower, higher = (
            None,
            None if target > keys[index_min] else len(d) - 2,
            len(d) - 1,
        )
    else:
        lower, higher = (
            index_min,
            index_min + 1 if target > keys[index_min] else index_min - 1,
            index_min,
        )
    if lower is None or higher is None:
        return False
    for item in (lower, higher):
        current_ = copy.deepcopy(current)
        current_.append(item)
        inside = _get_neighbors(
            h5[str(keys[item])], target_values, current_, index + 1, neighbors
        )
        if not inside:
            return False


def get_neighbors(h5: h5py.File, target_values=typing.Tuple[int, ...]) -> ParamImages:

    neighbors: typing.List[typing.List[int]] = []
    current: typing.List[typing.Tuple[typing.List[int], npt.ArrayLike]] = []
    index: int = 0
    inside = _neighbors(h5, target_values, neighbors, current, index)
    if not inside:
        return {}
    return neighbors


def average_neighbors(
    target_values: typing.Tuple[int, ...],
    min_values: typing.Tuple[int, ...],
    max_values: typing.Tuple[int, ...],
    images: ParamImages,
) -> npt.ArrayLike:
    def _normalize(
        values: typing.Tuple[int, ...],
        min_values: typing.Tuple[int, ...],
        max_values: typing.Tuple[int, ...],
    ) -> typing.Tuple[...]:
        return tuple([int(((v - min_) / (max_ - min_)) + 0.5)])

    def _distance(v1: typing.Tuple[int, ...], v2: typing.Tuple[int, ...]) -> float:
        return math.sqrt(sum([(a - b) ** 2 for a, b in zip(v1, v2)]))

    normalized = {
        values: _normalize(values, min_values, max_values) for values in images.keys()
    }

    distances = {
        values: _distance(target_values, normalized[values]) for values in images.keys()
    }

    sum_distances = sum(distances.values())

    distances = {values: d / sum_distances for values, d in distances.items()}

    r: typing.Optional[ntp.ArrayLike] = None

    for values, image in images.items():
        d = distances[values]
        if r is None:
            r = d * image
        else:
            r += d * image

    return r

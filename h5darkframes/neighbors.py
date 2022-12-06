import math
import typing
import h5py
import copy
from numpy import typing as npt
from .types import Controllables, Ranges, Params, ParamImages


def _neighbor_indexes(
        distances: typing.List[int],
        values: typing.List[int],
        target: int
)->typing.Tuple[typing.Optional[int],typing.Optional[int]]:

    index_min = min(range(len(distances)), key=distances.__getitem__)
    if index_min == 0:
        lower, higher = (None, None) if target < values[index_min] else (0, 1)
    elif index_min == len(distances) - 1:
        lower, higher = (
            (None, None) if target > values[index_min] else (
                len(distances) - 2,
                len(distances) - 1
            )
        )
    else:
        lower, higher = (
            (index_min, index_min + 1) if target > values[index_min] else (
                index_min - 1,
                index_min
            )
        )
    return lower, higher


def _neighbors(
    h5: h5py.File,
    target_values: typing.Tuple[int, ...],
    neighbors: ParamImages,
    current: typing.List[int] = [],
    index: int = 0,
) -> bool:

    if "image" in h5.keys():
        img: npt.ArrayLike = h5["image"]
        neighbors[tuple(current)] = img
        return True

    keys = sorted(list([int(k) for k in h5.keys()]))
    target: int = target_values[index]
    d = [abs(target-k) for k in keys]
    lower, higher = _neighbor_indexes(d,keys,target)

    if lower is None or higher is None:
        return False

    for item in (lower, higher):
        current_ = copy.deepcopy(current)
        current_.append(item)
        inside = _neighbors(
            h5[str(keys[item])], target_values, neighbors, current_, index + 1
        )
        if not inside:
            return False

    return True


def get_neighbors(h5: h5py.File, target_values=typing.Tuple[int, ...]) -> ParamImages:

    neighbors: ParamImages = {}
    current: typing.List[int] = []
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
) -> typing.Optional[npt.ArrayLike]:

    if not images:
        return None
    
    def _normalize(
        values: typing.Tuple[int, ...],
        min_values: typing.Tuple[int, ...],
        max_values: typing.Tuple[int, ...],
    ) -> typing.Tuple[int,...]:
        return tuple([int(((v - min_) / (max_ - min_)) + 0.5) for v,min_,max_ in zip(values,min_values,max_values)])

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

    r: typing.Optional[npt.ArrayLike] = None

    for values, image in images.items():
        d = distances[values]
        if r is None:
            r = (d * image).astype(image.dtype)  # type: ignore
        else:
            r += (d * image).astype(image.dtype)  # type: ignore

    return r

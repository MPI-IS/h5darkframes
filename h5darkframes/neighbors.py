import math
import typing
import h5py
import copy
from numpy import typing as npt
from .types import ParamImages


def _neighbor_indexes(
    values: typing.List[int], target: int
) -> typing.Tuple[typing.Optional[int], typing.Optional[int]]:

    distances = [abs(target - v) for v in values]

    index_min = min(range(len(distances)), key=distances.__getitem__)

    if values[index_min] == target:
        return index_min, None

    if index_min == 0:
        lower, higher = (None, None) if target < values[index_min] else (0, 1)
    elif index_min == len(distances) - 1:
        lower, higher = (
            (None, None)
            if target > values[index_min]
            else (len(distances) - 2, len(distances) - 1)
        )
    else:
        lower, higher = (
            (index_min, index_min + 1)
            if target > values[index_min]
            else (index_min - 1, index_min)
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
    lower, higher = _neighbor_indexes(keys, target)

    for item in (lower, higher):
        if item is not None:
            current_ = copy.deepcopy(current)
            current_.append(keys[item])
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
) -> npt.ArrayLike:
    def _normalize(
        values: typing.Tuple[int, ...],
        min_values: typing.Tuple[int, ...],
        max_values: typing.Tuple[int, ...],
    ) -> typing.Tuple[float, ...]:
        return tuple(
            [
                ((v - min_) / (max_ - min_))
                for v, min_, max_ in zip(values, min_values, max_values)
            ]
        )

    def _distance(v1: typing.Tuple[float, ...], v2: typing.Tuple[float, ...]) -> float:
        return math.sqrt(sum([(a - b) ** 2 for a, b in zip(v1, v2)]))

    normalized: typing.Dict[typing.Tuple[int, ...], typing.Tuple[float, ...]]
    normalized = {
        values: _normalize(values, min_values, max_values) for values in images.keys()
    }

    normalized_target = _normalize(target_values, min_values, max_values)

    distances: typing.Dict[typing.Tuple[float, ...], float]
    distances = {
        values: _distance(normalized_target, normalized[values])
        for values in images.keys()
    }

    sum_distances = sum(distances.values())

    distances = {values: d / sum_distances for values, d in distances.items()}

    r: npt.ArrayLike

    for values, image in images.items():
        d = distances[values]
        try:
            r += d * image  # type: ignore
        except NameError:
            r = d * image  # type: ignore
    return r.astype(image.dtype)  # type: ignore

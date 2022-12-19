import math
import typing
from numpy import typing as npt
from .types import ParamImages, Param, NParam, Params, ParamMap


def _normalize(
    values: Param, min_values: Param, max_values: Param
) -> typing.Tuple[float, ...]:
    return tuple(
        [
            ((v - min_) / (max_ - min_))
            for v, min_, max_ in zip(values, min_values, max_values)
        ]
    )


def _distance(v1: NParam, v2: NParam) -> float:
    return math.sqrt(sum([(a - b) ** 2 for a, b in zip(v1, v2)]))


def _closest(
    target_values: NParam,
    params: ParamMap,
) -> Param:
    d = {p: _distance(target_values, np) for p, np in params.items()}
    return sorted(list(params.keys()), key=lambda p: d[p])[0]


def get_neighbors(
    params: Params,
    min_values: Param,
    max_values: Param,
    target_values=Param,
) -> Params:

    try:
        index = params.index(target_values)
    except ValueError:
        pass
    else:
        return [params[index]]

    def _side_neighbor(
        index, target_values: NParam, params: ParamMap, sign: bool
    ) -> typing.Optional[Param]:
        if sign:
            subparams = {
                p: np for p, np in params.items() if np[index] >= target_values[index]
            }
        else:
            subparams = {
                p: np for p, np in params.items() if np[index] < target_values[index]
            }
        if not subparams:
            return None
        return _closest(target_values, subparams)

    ntarget_values = _normalize(target_values, min_values, max_values)
    nparams = {param: _normalize(param, min_values, max_values) for param in params}
    neighbors: Params = []
    for index in range(len(target_values)):
        for sign in (True, False):
            candidate = _side_neighbor(index, ntarget_values, nparams, sign)
            if candidate is not None:
                neighbors.append(candidate)
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

    for values, (image, _) in images.items():
        d = distances[values]
        try:
            r += d * image  # type: ignore
        except NameError:
            r = d * image  # type: ignore
    return r.astype(image.dtype)  # type: ignore

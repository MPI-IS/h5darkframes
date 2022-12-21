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


def interpolation_neighbors(
    params: Params, target_values: Param, fixed_index: int
) -> Params:

    if len(target_values) != 2:
        raise ValueError(
            "darkframes: 'interpolation neighbors' requires "
            f"two dimentional parameters, not {len(target_values)}"
        )

    try:
        index = params.index(target_values)
    except ValueError:
        pass
    else:
        return [params[index]]

    subset = [p for p in params if p[fixed_index] == target_values[fixed_index]]

    if not subset:
        raise ValueError(
            f"failed to find neighbors for {target_values}, no existing darkframe "
            f"associated to value {target_values[fixed_index]}"
        )

    if len(subset) == 1:
        return subset

    other_index = 0 if fixed_index == 1 else 1

    neighbors: Params = []

    sup = sorted(
        [s for s in subset if s[other_index] >= target_values[other_index]],
        key=lambda p: abs(p[other_index] - target_values[other_index]),
    )
    if sup:
        neighbors.append(sup[0])

    sdown = sorted(
        [s for s in subset if s[other_index] < target_values[other_index]],
        key=lambda p: abs(p[other_index] - target_values[other_index]),
    )
    if sdown:
        neighbors.append(sdown[0])

    return neighbors


def closest_neighbors(
    params: Params,
    min_values: Param,
    max_values: Param,
    target_values=Param,
    nb_closest: int = 2,
) -> Params:

    try:
        index = params.index(target_values)
    except ValueError:
        pass
    else:
        return [params[index]]

    ntarget_values = _normalize(target_values, min_values, max_values)
    nparams = {param: _normalize(param, min_values, max_values) for param in params}
    distances = {
        param: _distance(nparam, ntarget_values) for param, nparam in nparams.items()
    }
    return sorted(params, key=lambda p: distances[p])[:nb_closest]


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
        index: int,
        target_values: NParam,
        params: ParamMap,
        sign: bool,
        distances: typing.Dict[Param, float],
    ) -> typing.Optional[Param]:
        if sign is True:
            subparams = {
                p: np for p, np in params.items() if np[index] >= target_values[index]
            }
        else:
            subparams = {
                p: np for p, np in params.items() if np[index] < target_values[index]
            }
        if not subparams:
            return None
        return sorted(list(subparams.keys()), key=lambda p: distances[p])[0]

    def _select_set(
        candidate_sets: typing.List[Params], distances: typing.Dict[Param, float]
    ) -> Params:
        lengths = [len(cs) for cs in candidate_sets]
        max_length = max(lengths)
        lsets = [cs for cs in candidate_sets if len(cs) == max_length]
        if len(lsets) == 1:
            return lsets[0]

        def _dset(params: Params, distances):
            return sum([distances[param] for param in params]) / len(params)

        return sorted(lsets, key=lambda p: _dset(p, distances))[0]

    ntarget_values = _normalize(target_values, min_values, max_values)
    nparams = {param: _normalize(param, min_values, max_values) for param in params}
    distances = {
        param: _distance(nparam, ntarget_values) for param, nparam in nparams.items()
    }

    candidate_sets: typing.List[Params] = []

    for index in range(len(target_values)):
        candidate_set: Params = []
        for sign in (True, False):
            candidate = _side_neighbor(index, ntarget_values, nparams, sign, distances)
            if candidate is not None:
                candidate_set.append(candidate)
        candidate_sets.append(candidate_set)

    return _select_set(candidate_sets, distances)


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

    normalized: typing.Dict[Param, NParam]
    normalized = {
        values: _normalize(values, min_values, max_values) for values in images.keys()
    }

    normalized_target = _normalize(target_values, min_values, max_values)

    inv_distances: typing.Dict[NParam, float]
    inv_distances = {
        values: 1.0 / _distance(normalized_target, normalized[values])
        for values in images.keys()
    }

    sum_distances = sum(inv_distances.values())

    inv_distances = {values: d / sum_distances for values, d in inv_distances.items()}

    r: npt.ArrayLike

    for values, (image, _) in images.items():
        d = inv_distances[values]
        try:
            r += d * image  # type: ignore
        except NameError:
            r = d * image  # type: ignore
    return r.astype(image.dtype)  # type: ignore

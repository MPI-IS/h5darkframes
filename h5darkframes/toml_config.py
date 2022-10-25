import toml
import typing
from collections import OrderedDict
from pathlib import Path
from .control_range import ControlRange


def read_config(path: Path) -> typing.Tuple[typing.OrderedDict[str, ControlRange], int]:
    def _get_range(name: str, config: typing.Mapping[str, typing.Any]) -> ControlRange:
        required_keys = ("min", "max", "step", "threshold", "timeout")
        for rk in required_keys:
            if rk not in config.keys():
                raise ValueError(
                    f"error with darkframes configuration file {path}, "
                    f"controllable {name}: "
                    f"missing required key '{rk}'"
                )
        try:
            min_, max_, step, threshold, timeout = [
                int(config[key]) for key in required_keys
            ]
        except ValueError as e:
            raise ValueError(
                f"error with darkframes configuration file {path}, "
                f"controllable {name}: "
                f"failed to cast value to int ({e})"
            )
        return ControlRange(min_, max_, step, threshold, timeout)

    if not path.is_file():
        raise FileNotFoundError(str(path))
    content = toml.load(str(path))

    try:
        config = content["darkframes"]
    except KeyError:
        raise ValueError(
            f"error with darkframes configuration file {path}: "
            "missing key 'darkframes'"
        )

    required_keys = ("average_over", "controllables")
    for rk in required_keys:
        if rk not in config.keys():
            raise ValueError(
                f"error with darkframes configuration file {path} key 'darkframes': "
                f"missing key '{rk}'"
            )

    try:
        avg_over = int(config["average_over"])
    except ValueError as e:
        raise ValueError(
            f"failed to cast value for 'average_over' ({config['average_over']}) "
            f"to int: {e}"
        )

    controllables = config["controllables"]
    d = OrderedDict()
    for name, values in controllables.items():
        d[name] = _get_range(name, values)
    return (
        d,
        avg_over,
    )

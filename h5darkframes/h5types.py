import typing
from numpy import typing as npt
from .control_range import ControlRange

Controllables = typing.Tuple[str, ...]
"""
List of controllables that have been ranged over to create the file library, in order.
Controllables will be the keys of instances of Ranges.
"""

Ranges = typing.Union[
    typing.List[typing.Dict[str, ControlRange]], typing.OrderedDict[str, ControlRange]
]
"""
Ranges used to create a library files, e.g.

{ "TargetTemp": ControlRange(min,max,step) , "Exposure": ControlRange(min,max,step)  }

If the file has been created by fusing other files, then this is a list, e.g.
[
  { "TargetTemp": ControlRange(min,max,step) , "Exposure": ControlRange(min,max,step)  },
  { "TargetTemp": ControlRange(min,max,step) , "Exposure": ControlRange(min,max,step)  }
]
"""

Param = typing.Tuple[int, ...]
"""
Concrete values of controllables, in order.
"""

NParam = typing.Tuple[float, ...]
"""
Concrete values of controllables, in order (normalized).
"""

Params = typing.List[Param]
"""
Concrete Controllables values associated to a darkframes. The tuples are of the same
length than Contrallables, and in the same order, e.g.
if an instance of Controllables is ["c1","c2"]
and an instance of Params is [1,2], this means the library contains a darkframe for
the configuration {"c1":1, "c2":2}.
"""

NParams = typing.List[NParam]
"""
Normalized list of params
"""

ParamMap = typing.Dict[Param, NParam]
"""
Map between params and their normalized values
"""

ParamImage = typing.Tuple[
    typing.Tuple[int, ...], npt.ArrayLike, typing.Dict[str, typing.Any]
]
"""
Parameter associated with the corresponding image/camera config.
"""

ParamImages = typing.Dict[
    typing.Tuple[int, ...], typing.Tuple[npt.ArrayLike, typing.Dict[str, typing.Any]]
]
"""
Parameters associated with the corresponding image/camera config.
"""

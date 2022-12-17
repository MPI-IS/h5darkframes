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

Param = typing.Tuple[int,...]
"""
Concrete values of controllables, in order.
"""

Params = typing.List[Param]
"""
Concrete Controllables values associated to a darkframes. The tuples are of the same
length than Contrallables, and in the same order, e.g.
if an instance of Controllables is ["c1","c2"]
and an instance of Params is [1,2], this means the library contains a darkframe for
the configuration {"c1":1, "c2":2}.
"""

ParamImage = typing.Dict[Param, npt.ArrayLike, typing.Dict]
"""
The parameters associated with the corresponding image and camera configuration.
"""

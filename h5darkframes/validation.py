import typing
from rich.table import Table
from rich.console import Console
from rich.progress import track
from pathlib import Path
import numpy as np
from .image_library import ImageLibrary
from .types import Param, Params

Stat = typing.Tuple[Param, Params, float, float, float, float]
"""
Param, average, standard deviation, min value, max value
"""


class TempRemove:
    def __init__(self, lib: ImageLibrary, param: Param):
        self._lib = lib
        self._param = param
        if param not in lib.params():
            raise ValueError(
                f"Can not remove param {param} from the image library: "
                f"is not present"
            )

    def __enter__(self):
        _, self._img, self._config = self._lib.rm(self._param)
        return self._img

    def __exit__(self, exception_type, exception_value, exception_traceback):
        self._lib.add(self._param, self._img, self._config, True)


def leave_one_out(p: Path) -> typing.Generator[Stat, None, None]:

    with ImageLibrary(p, edit=True) as lib:

        params = lib.params()

        for param in track(params, "reading darkframes stats"):

            with TempRemove(lib, param) as image:

                neighbors = lib.get_interpolation_neighbors(param)
                dark = lib.generate_darkframe(param, neighbors)

                im32 = image.astype(np.float32)
                dark32 = dark.astype(np.float32)
                diff = np.abs(im32 - dark32)
                min_ = np.min(diff)
                max_ = np.max(diff)
                avg = np.average(diff)
                std = np.std(diff)

                yield param, neighbors, avg, std, min_, max_

        return


def print_leave_one_out(p: Path):

    with ImageLibrary(p) as lib:
        controllables_ = lib.controllables()
        controllables = ", ".join(controllables_)

    table = Table(title="configurations")
    table.add_column(f"param ({controllables})")
    table.add_column("neighbors")
    table.add_column("average")
    table.add_column("standard deviation")
    table.add_column("min value")
    table.add_column("max value")

    for stat in leave_one_out(p):
        param, neighbors, avg, std, min_, max_ = stat
        row = [
            str(param),
            ", ".join([str(n) for n in sorted(neighbors)]),
            f"{avg:2f}",
            f"{std:2f}",
            f"{min_:2f}",
            f"{max_:2f}",
        ]
        table.add_row(*row)

    print()
    console = Console()
    console.print(table)
    print()

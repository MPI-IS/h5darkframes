import typing
import h5py
from numpy import types as npt
from .types import Controllables, Param


def get_params(
    h5: h5py.File,
    controllables: Controllables,
) -> Params:
    """
    Return the list of all configurations to which a corresponding
    image is stored in the library.
    """

    def _append_configs(
        controllables: Controllables,
        h5: h5py.File,
        index: int,
        current: typing.List[int],
        c: Params,
    ):
        if index >= len(controllables):
            c.append(tuple(current))
            return
        for key in sorted(h5.keys()):
            current_ = copy.deepcopy(current)
            current_.append(int(key))
            _append_configs(controllables, h5[key], index + 1, current_, c)

    index: int = 0
    current: typing.List[int] = []
    c: Params = []
    _append_configs(controllables, h5, index, current, c)

    return c


def get_group(
        h5: h5py.File,
        param: Param,
        create: bool
)->typing.Tuple[typing.Optional[h5py.File],bool]:
    """
    Returns the group hosting the darkframe dataset if the hdf5 file
    contains an entry for the provided parameters, None, otherwise.
    If create is True, the group will be created if it does not exists.
    The boolean indicating whether or not the group was created
    is also returned.
    """
    group = h5
    created = False
    for p in param:
        try:
            group = group[str(p)]
        except KeyError:
            if create:
                group = group.require_group(str(p))
                created = True
            else:
                return None,False
    return group, created


def add(
        h5: h5py.File,
        param: Param,
        img: npt.ArrayLike,
        camera_config: typing.Dict,
        overwrite: bool
)->bool:
    """
    Write the image and the camera configuration to the 
    file. If overwrite is False and there is already an image
    corresponding to the parameters, then the data is not
    writen in the file and False is returned.
    """

    create = True
    group,created = group_exists(h5, param, create)

    if not created and not overwrite:
        return False

    group.create_dataset("image", data=img)
    group.attrs["camera_config"] = repr(camera_config)

    return True
    
        

def rm(
        h5: h5py.File,
        param: Param
)-> typing.Optional[ParamImage]:

    groups = [h5]
    group = h5

    for p in param:
        try:
            group = group[str(p)]
        except KeyError:
            return None
        groups.append(group)

    try :
        img = group["image"]
    except KeyError:
        return None

    try:
        config = eval(group["camera_config"])
    except KeyError:
        return None

    del group["image"]
    del group["camera_config"]

    groups.reverse()
    for group in groups:
        if not group:
            del group

    return param, img, config

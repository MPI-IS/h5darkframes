import typing
import numpy as np
from numpy import typing as npt


class DarkframeError(Exception):
    def __init__(
        self,
        img: npt.NDArray,
        dtype=None,
        shape: typing.Optional[typing.Tuple[int, int]] = None,
    ):
        if dtype is not None:
            self._error = str(
                f"darkframe expects an image of type {dtype}, "
                f"got {img.dtype} instead"  # type: ignore
            )
        elif shape is not None:
            self._error = str(
                f"darkframe expects an image of shape {shape}, "
                f"got {img.shape} instead"  # type: ignore
            )
        else:
            self._error = "darkframe substraction error"

    def __str__(self) -> str:
        return self._error


def substract(img: npt.NDArray, darkframe: npt.NDArray) -> npt.NDArray:

    # checking the darkframe is of suitable type/shape
    if not darkframe.dtype == img.dtype:  # type: ignore
        raise DarkframeError(img, dtype=darkframe.dtype)  # type: ignore
    if not darkframe.shape == img.shape:  # type: ignore
        raise DarkframeError(img, shape=darkframe.shape)  # type: ignore

    # substracting
    im64 = img.astype(np.int64)
    dark64 = darkframe.astype(np.int64)  # type: ignore
    sub64 = im64 - dark64
    sub64[sub64 < 0] = 0

    # returning
    return sub64.astype(img.dtype)

import typing
import tempfile
import time
import numpy as np
import h5darkframes as dark
from collections import OrderedDict
from pathlib import Path


def test_control_range_get_values():

    controls = {
        "a": dark.ControlRange(0, 10, 5),
        "b": dark.ControlRange(0, 3, 1),
        "c": dark.ControlRange(0, 15, 3),
    }

    assert controls["a"].get_values() == [0, 5, 10]
    assert controls["b"].get_values() == [0, 1, 2, 3]
    assert controls["c"].get_values() == [0, 3, 6, 9, 12, 15]


def test_reach_control():

    controls = {
        "width": dark.ControlRange(60, 100, 20),
        "height": dark.ControlRange(10, 13, 1, timeout=2),
    }
    with dark.DummyCamera(controls, value=3, dynamic=True) as camera:
        camera.reach_control("width", 60)
        assert camera.get_control("width") == 60
        camera.reach_control("height", 12)
        assert camera.get_control("height") == 12
        start = time.time()
        camera.reach_control("height", 12)
        end = time.time()
        assert camera.get_control("height") == 12
        assert end - start < 0.1


def test_average_images():
    class DummyTaker:
        def __init__(self, shape: typing.Tuple[int, int], value: int):
            self._value = value
            self._shape = shape

        def picture(self):
            return np.zeros(self._shape, dtype=np.uint16) + self._value

    max_value = (np.uint16() - 1).astype(np.uint16)
    demi_value = (max_value / 2).astype(np.uint16)
    values = (max_value, demi_value)

    shape = (1000, 1000)

    avg_over = 50

    for value in values:

        image_taker = DummyTaker(shape, value)
        image = dark.create_library._take_and_average_images(image_taker, avg_over)

        assert image.dtype == np.uint16
        assert image.shape == shape
        assert image[10, 10] == value


def test_create_library():

    controls = OrderedDict()
    controls["width"] = dark.ControlRange(60, 100, 20)
    controls["height"] = dark.ControlRange(10, 13, 1, timeout=2.0)

    avg_over = 3

    with dark.DummyCamera(controls, value=3) as camera:

        with tempfile.TemporaryDirectory() as tmp:

            path = Path(tmp) / "test.hdf5"

            dark.library("testlib", camera, controls, avg_over, path, progress=None)

            with dark.ImageLibrary(path) as il:
                params = il.params()
                for width in (60, 80, 100):
                    for height in (10, 11, 12, 13):
                        assert (width,height) in params

            with dark.ImageLibrary(path) as il:

                closest = dark.GetType.closest
                
                params = il.ranges()
                assert params["width"].min == 60
                assert params["height"].max == 13

                desired = {"width": 60, "height": 10}
                image, camera_config = il.get(desired, closest)
                assert camera_config["width"] == 60
                assert camera_config["height"] == 10

                desired = {"width": 61, "height": 11}
                image, camera_config = il.get(desired, closest)
                assert camera_config["width"] == 60
                assert camera_config["height"] == 11

                desired = {"width": 75, "height": 11}
                image, camera_config = il.get(desired, closest)
                assert camera_config["width"] == 80
                assert camera_config["height"] == 11

                desired = {"width": 75, "height": 14}
                image, camera_config = il.get(desired, closest)
                assert camera_config["width"] == 80
                assert camera_config["height"] == 13

                desired = {"width": 75, "height": 9}
                image, camera_config = il.get(desired, closest)
                assert camera_config["width"] == 80
                assert camera_config["height"] == 10


def test_update_library():

    controls = OrderedDict()
    controls["width"] = dark.ControlRange(60, 100, 20)
    controls["height"] = dark.ControlRange(10, 13, 1, timeout=2.0)

    avg_over = 3

    with dark.DummyCamera(controls, value=3, dynamic=False) as camera:

        with tempfile.TemporaryDirectory() as tmp:

            # creating a library
            path = Path(tmp) / "test.hdf5"
            dark.library("testlib", camera, controls, avg_over, path, progress=None)
            with dark.ImageLibrary(path) as il:
                configs = il.configs()
                assert il.name() == "testlib"
            for width in (60, 80, 100):
                for height in (10, 11, 12, 13):
                    assert {"width": width, "height": height} in configs

            # updating the library: the control ranges are wider
            controls = OrderedDict()
            controls["width"] = dark.ControlRange(60, 140, 20)
            controls["height"] = dark.ControlRange(8, 13, 1, timeout=2.0)
            dark.library("testlib2", camera, controls, avg_over, path, progress=None)
            with dark.ImageLibrary(path) as il:
                configs = il.configs()
                assert il.name() == "testlib2"
            for width in (60, 80, 100, 120, 140):
                for height in (8, 9, 10, 11, 12, 13):
                    assert {"width": width, "height": height} in configs

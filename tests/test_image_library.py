import tempfile
import h5darkframes as dark
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
        "height": dark.ControlRange(10, 13, 1),
    }
    camera = dark.DummyCamera(controls, value=3)
    camera.reach_control("width",60)
    assert camera.get_control("width")==60
    

def test_create_library():

    controls = {
        "width": dark.ControlRange(60, 100, 20),
        "height": dark.ControlRange(10, 13, 1),
    }

    avg_over = 2

    camera = dark.DummyCamera(controls, value=3)

    with tempfile.TemporaryDirectory() as tmp:

        path = Path(tmp) / "test.hdf5"

        dark.library("testlib", camera, controls, avg_over, path, progress=None)

        with dark.ImageLibrary(path) as il:

            params = il.params()
            assert params["width"].min == 60
            assert params["height"].max == 13

            desired = {"width": 60, "height": 10}
            image, camera_config = il.get(desired)
            assert camera_config["width"] == 60
            assert camera_config["height"] == 10

            desired = {"width": 61, "height": 11}
            image, camera_config = il.get(desired)
            assert camera_config["width"] == 60
            assert camera_config["height"] == 11

            desired = {"width": 75, "height": 11}
            image, camera_config = il.get(desired)
            assert camera_config["width"] == 80
            assert camera_config["height"] == 11

            desired = {"width": 75, "height": 14}
            image, camera_config = il.get(desired)
            assert camera_config["width"] == 80
            assert camera_config["height"] == 13

            desired = {"width": 75, "height": 9}
            image, camera_config = il.get(desired)
            assert camera_config["width"] == 80
            assert camera_config["height"] == 10

import tempfile
import h5darkframes as dark
from collections import OrderedDict
from pathlib import Path


def test_fusing_libraries():

    # controls of the first library
    controls1 = OrderedDict()
    controls1["width"] = dark.ControlRange(60, 100, 20)
    controls1["height"] = dark.ControlRange(10, 13, 1, timeout=2.0)

    # controls of the second library
    controls2 = OrderedDict()
    controls2["width"] = dark.ControlRange(20, 100, 20)
    controls2["height"] = dark.ControlRange(13, 15, 1, timeout=2.0)

    avg_over = 3

    # for creating different images in lib1 and lib2
    lib1_value = 1
    lib2_value = 2

    with tempfile.TemporaryDirectory() as tmp:

        # creating the two libraries to fuse
        path1 = Path(tmp) / "test1.hdf5"
        path2 = Path(tmp) / "test2.hdf5"
        with dark.DummyCamera(controls1, value=lib1_value, dynamic=False) as camera:
            dark.library("lib1", camera, controls1, avg_over, path1, progress=None)
        with dark.DummyCamera(controls2, value=lib2_value, dynamic=False) as camera:
            dark.library("lib2", camera, controls2, avg_over, path2, progress=None)

        # fusing the two libraries
        target_path = Path(tmp) / "target.hdf5"
        dark.fuse_libraries("fused", target_path, [path1, path2])

        # checking the target library has
        # been created
        assert target_path.is_file()

        # parsing the created libraries
        lib1 = dark.ImageLibrary(path1)
        lib2 = dark.ImageLibrary(path2)
        target = dark.ImageLibrary(target_path)

        # this was set as argument
        # to the fuse_libraries method
        assert target.name() == "fused"

        # the params of the target library
        # is the list of the params of the libaries
        # that have been fused
        params = target.ranges()

        assert lib1.ranges() in params
        assert lib2.ranges() in params

        # reading all the params
        lib1_params = lib1.params()
        lib2_params = lib2.params()
        target_params = target.params()

        # param1 comes from lib1
        param1 = (60, 11)
        assert param1 in lib1_params
        assert param1 in target_params

        # param2 comes from lib1
        param2 = (80, 13)
        assert param2 in lib1_params
        assert param2 in target_params

        # param3 comes from lib2
        param3 = (40, 15)
        assert param3 in lib2_params
        assert param3 in target_params

        # param4 comes from both lib1 and lib2
        param4 = (100, 13)
        assert param4 in lib1_params
        assert param4 in lib2_params
        assert param4 in target_params

        # image of param1 should have been
        # copies from lib1 to target
        image, config = target.get(param1)
        image1, config1 = lib1.get(param1)

        assert image[0][0] == image1[0][0]
        assert image.shape == image1.shape
        assert config == config1

        # image from param2 should habe
        # been copied from lib2 to target
        image, config = target.get(param3)
        image3, config3 = lib2.get(param3)
        assert image[0][0] == image3[0][0]
        assert image.shape == image3.shape
        assert config == config3

        # image from params should have
        # been copied from lib1 to target.
        # lib2 also has this param,
        # but as it was passed second when fusing,
        # the image in lib2 should not have been
        # copied.
        image, config = target.get(param4)
        image41, config41 = lib1.get(param4)
        image42, config42 = lib2.get(param4)
        assert image[0][0] == image41[0][0]
        assert image.shape == image41.shape
        assert config == config41
        assert image[0][0] != image42[0][0]
        assert config != config42

![unit tests](https://github.com/MPI-IS/h5darkframes/actions/workflows/tests.yaml/badge.svg)
![mypy](https://github.com/MPI-IS/h5darkframes/actions/workflows/python_mypy.yml/badge.svg)

# H5DARKFRAMES (beta)

H5Darkframes is a python library for generating and using darkframes library.
For now, it supports only asi zwo cameras (see [https://github.com/MPI-IS/camera_zwo_asi](https://github.com/MPI-IS/camera_zwo_asi)).

> This is beta, and need some more testing

## Getting Started as a User (using `pip`)

Dependency management with `pip` is easier to set up than with `poetry`, but the optional dependency-groups are not installable with `pip`.

* Create and activate a new Python virtual environment:
  ```bash
  python3 -m venv --copies venv
  source venv/bin/activate
  ```
* Update `pip` and build package:
  ```bash
  pip install -U pip  # optional but always advised
  pip install .       # -e option for editable mode
  ```

Alternatively to building from source, the package can also be installed from [PyPI](https://pypi.org/project/h5darkframes/).

## Getting Started as a Developer (using `poetry`)

Dependency management with `poetry` is required for the installation of the optional dependency-groups.

* Install [poetry](https://python-poetry.org/docs/).
* Install dependencies for package
  (also automatically creates project's virtual environment):
  ```bash
  poetry install
  ```
* Install `dev` dependency group:
  ```bash
  poetry install --with dev
  ```
* Activate project's virtual environment:
  ```bash
  poetry shell
  ```

## Tests (only possible for setup with `poetry`, not with `pip`)

To install `test` dependency group:
```bash
poetry install --with test
```

To run the tests:
```bash
python -m pytest tests
```

## Usage

Assuming that [camera-zwo-asi](https://github.com/MPI-IS/camera_zwo_asi) is installed and a camera is plugged:

### creating a darkframe library

First, a configuration file must be created. In a terminal:

```bash
darkframes-zwoasi-config
```

This will create in the current directory a file ```darkframes.toml``` with a content similar to:

```
[darkframes]
average_over = 5

[camera.controllables]
AutoExpMaxExpMS = 30000
AutoExpMaxGain = 285
AutoExpTargetBrightness = 100
BandWidth = "auto"
CoolerOn = 0
Exposure = 300
Flip = 0
Gain = 400
HighSpeedMode = 0
MonoBin = 0
Offset = 8
TargetTemp = 26
WB_B = 95
WB_R = 52

[camera.roi]
start_x = 0
start_y = 0
width = 4144
height = 2822
bins = 1
type = "raw8"

[darkframes.controllables.TargetTemp]
min = -15
max = 15
step = 3
threshold = 1
timeout = 600

[darkframes.controllables.Exposure]
min = 1000000
max = 30000000
step = 5000000
threshold = 1
timeout = 0.1

[darkframes.controllables.Gain]
min = 200
max = 400
step = 100
threshold = 1
timeout = 0.1
```

You may edit this file to setup:

- your desired camera configuration

- the controllables over which darkframes will be created, and over which range

- the number of pictures that will be averaged per darkframes


For example:

```
[darkframes.controllables.TargetTemp]
min = -15
max = 15
step = 3
threshold = 1
timeout = 600
```

implies that darkframes will be taken for values of temperature -15, -12, -9, ... up to +15.

### creating the darkframes library

Call in a terminal:

```bash
# change "mylibraryname" to a name of your choice
darkframes-zwoasi-library --name mylibraryname
```

You may get stats regarding the library (requires a file 'darkframes.hdf5' in the current directory):

```bash
darkframes-info
```

### using the library

```python

import h5darkframes as dark
import camera_zwo_asi as zwo
from pathlib import Path

# path to the library
path = Path("/path/to/darkframes.hdf5")

# handle over the library
library = dark.ImageLibrary(path)

# handle over the camera
camera = zwo.Camera(0)

# taking a picture. Image is an instance of zwo.Image
image = camera.capture()

# getting the current camera configuration
controls = camera.get_controls()

# "Temperature", "Exposure" and "Gain" must be the
# controllables that have been iterated over
# during the creation of the library
darkframe_target = {
       "Temperature": controls["Temperature"].value,
       "Exposure": controls["Exposure"].value,
       "Gain": controls["Gain"].value
}

# getting the darkframe that is the closest to the target
# darkframe: a numpy array
# darkframe_config: the config of the camera when the darkframe was taken
darkframe, darkframe_config= library.get(darkframe_target)

# optional sanity checks
assert image.get_data().shape == darkframe.shape
assert image.get_data().dtype = darkframe.dtype

# substracting the darkframe
substracted_image = image.get_data()-darkframe
```

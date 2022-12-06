import os
import typing
from pathlib import Path
import numpy as np
from numpy import typing as npt
import matplotlib.pyplot as plt
from rich.progress import track, Progress
from collections import OrderedDict

Temperature = typing.NewType("Temperature", int)
Exposure = typing.NewType("Exposure", int)
Config = typing.Tuple[Temperature, Exposure]
Pixel = typing.Tuple[int, int]
Darkfiles = typing.Dict[Config, typing.List[npt.ArrayLike]]

_shape = (2822, 4144)


def read_files(directory: Path) -> Darkfiles:

    darkfiles: Darkfiles = {}

    files = list(directory.glob("TargetTemp_*_Exposure_*_*.npy"))

    for f in track(files, description="reading images"):

        filename = f.stem
        fields = filename.split("_")
        temperature = Temperature(fields[1])
        exposure = Exposure(fields[3])

        key = (temperature, exposure)
        image = np.load(f)

        images: typing.List[npt.ArrayLike]
        try:
            images = darkfiles[key]
        except KeyError:
            images = []
            darkfiles[key] = images

        images.append(image)

    return darkfiles


def select_pixels(darkfiles: Darkfiles) -> typing.Tuple[Pixel, Pixel, Pixel]:

    pixel_values: typing.Dict[Pixel, float] = {}
    sum_images = np.zeros(_shape)

    for image_list in track(list(darkfiles.values()), "reading pixels"):
        for image in image_list:
            sum_images += image.astype(sum_images.dtype)

    pixel_values = {
        (row, coln): sum_images[row][coln]
        for row in range(_shape[0])
        for coln in range(_shape[1])
    }

    ordered_pixels: typing.List[Pixel] = sorted(
        pixel_values.keys(), key=lambda pixel: pixel_values[pixel]
    )
    nb_pixels = len(ordered_pixels)
    return (
        ordered_pixels[int(nb_pixels / 4)],
        ordered_pixels[int(nb_pixels / 2)],
        ordered_pixels[int(3 * nb_pixels / 4)],
    )


def run():

    darkfiles: Darkfiles = read_files(Path(os.getcwd()))
    configs = list(sorted(darkfiles.keys(), key=lambda t: (int(t[0]), int(t[1]))))

    pixels: typing.Tuple[Pixel, ...] = select_pixels(darkfiles)

    nb_rows = len(pixels)
    nb_colns = len(configs)

    config_coln: typing.OrderedDict[Config:int] = OrderedDict()
    for coln, config in enumerate(configs):
        config_coln[config] = coln

    pixel_row: typing.OrderedDict[Pixel:int] = OrderedDict()
    for row, pixel in enumerate(pixels):
        pixel_row[pixel] = row

    _, axs = plt.subplots(nb_rows, nb_colns)

    with Progress() as progress:

        task = progress.add_task("generating plots", total=len(pixels) * len(configs))

        for pixel_index, pixel in enumerate(pixels):
            for config in configs:
                p = axs[pixel_row[pixel], config_coln[config]]
                images = darkfiles[config]
                values = [image[pixel[0], pixel[1]] for image in images]
                p.hist(values, 10)
                p.set_title(
                    f"pixel {pixel_index}, temp: {config[0]}, exposure: {config[1]}"
                )
                progress.update(task, advance=1)

    plt.show()


if __name__ == "__main__":

    run()

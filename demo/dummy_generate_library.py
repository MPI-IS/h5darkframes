import h5darkframes as dark
from h5darkframes import executables

if __name__ == "__main__":

    library_name = "demo darkframes"
    progress_bar = True

    path = executables.darkframes_library(dark.DummyCamera, library_name, progress_bar)

    print(f"\ncreated {path}\n")

    lib = dark.ImageLibrary(path)
    print(f"Library: {lib.name()}")
    print("darkframes for controls:")
    for config in lib.configs():
        print("\t", config)
    print()
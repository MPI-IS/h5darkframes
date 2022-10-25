import h5darkframes as dark
from h5darkframes import executables

if __name__ == "__main__":

    path = executables.darkframes_config(dark.DummyCamera,value=1)
    print(f"\ncreated {path}\n")

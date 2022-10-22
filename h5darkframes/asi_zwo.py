import camera_zwo_asi as zwo
from .camera import Camera

class AsiZwoCamera(Camera):

    def __init__(self, index):
        self._camera = zwo.Camera(index)

    def picture(self)->npt.ArrayLike:
        """
        Taking a picture
        """
        image = self._camera.capture()
        return image.get_image()

    def configure(self, path: Path)->None:
        """
        Configure the camera from a toml 
        configuration file.
        """
        if not path.is_file():
            raise FileNotFoundError(str(path))
        content = toml.load(str(path))
        if not "ROI" in content:
            raise KeyError(
                f"the key 'ROI' could not be found in {path} "
                "(required for zwo asi cameras)"
            )
        roi = zwo.ROI.from_toml(content)
        self._camera.set_roi(roi)
    
    def estimate_picture_time(
            self
            controls : typing.Mapping[str,int]
    )->float:
        """
        estimation of how long it will take for a picture
        to be taken (typically relevant if one of the control
        is the exposure time)
        """
        if not "Exposure" in control:
            exposure = self._camera.get_controls()["Exposure"].value / 1e6
        else:
            return controls["Exposure"] / 1e6
    
    def set_control(control: str, value: int)->None:
        """
        Changing the configuration of the camera
        """
        if control == "TargetTemp":
            self._camera.set_control("CoolerOn",1)
        self._camera.set_control(control,value)

    def get_control(control: str)->int:
        """
        Getting the configuration of the camera
        """
        control = control if control != "TargetTemp" else "Temperature"
        return self._camera.get_controls()[control].value
        
    @classmethod
    def generate_config_file(cls, path: Path):
        """
        Generate a toml configuration file with reasonable
        default values. User can edit this file and then call
        the method 'from_toml' to get desired instances of ControlRange
        and ROI.
        """
        if not path.parent.is_dir():
            raise FileNotFoundError(
                f"can not generate the configuration file {path}: "
                f"directory {path.parent} not found"
            )
        r: typing.Dict[str, typing.Any] = {}
        r["average_over"] = 5
        roi = self._camera.get_roi().to_dict()
        r["ROI"] = roi
        control_ranges = OrderedDict()
        control_ranges["TargetTemp"] = ControlRange(-15, 15, 3, 1, 600)
        control_ranges["Exposure"] = ControlRange(1000000, 30000000, 5000000, 1, 0.1)
        control_ranges["Gain"] = ControlRange(200, 400, 100, 1, 0.1)
        r["controllables"] = OrderedDict()
        for name, control_range in control_ranges.items():
            r["controllables"][name] = control_range.to_dict()
        with open(path, "w") as f:
            toml.dump(r, f)

        
    



class PseudoH5File:

    def __init__(self,
                 controllables: dark.Controllables,
                 param_images: dark.ParamImages
    )->None:
        self._d: typing.Dict[str,typing.Union[int,npt.ArrayList]] = {}
        self._controllables = controllables
        self._add(self._d, param_images)

    @staticmethod
    def _add(
            main_d: typing.Dict[str,typing.Union[int,npt.ArrayList]],
            param_images: dark.ParamImages
    )->None:
        
        param: typing.Tuple[int,...]
        image: npt.ArrayLike
        
        for param, image in param_image.items():
            d = main_d
            for value in param:
                try:
                    d = d[value]
                except KeyError:
                    d[value] = {}
                    d = d[value]
            
            d["image"] = image

        


def test_get_neighbors():

    params = ()

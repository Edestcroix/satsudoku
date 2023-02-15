import json
import os


REQUIRED_KEYS = ["puzzleDir", "cacheDir", "defaultPuzzleSet", "puzzleSets"]
REQUIRED_PUZZLE_KEYS = ["file", "numPuzzles", "offset", "size"]


# Wrapper around dict that loads a json file and validates it on init, and
# provides a few helper functions to retrieve specific values from the config easier.
# DO NOT modify the config after it is initialized. I would make it immutable, but
# that causes issues with multiprocessing not being able to duplicate the object.
class Config(dict):
    def __init__(self, config_file: str):
        self.__config_file = config_file
        self.__fix = None
        with open(self.__config_file, "r") as f:
            self.__config = json.load(f)

        self.__validate()

        for puzzle_set in self.__config["puzzleSets"].values():
            puzzle_set["file"] = f"{self.__config['puzzleDir']}{puzzle_set['file']}"

        # call super init after we have validated the config.
        # method functions don't operate on super(), only self.__config,
        # but we need to call super() to initialize the dict, and since
        # Config is never meant to be modified, it doesn't matter that
        # two copies of the config exist in memory, since they should be
        # identical at all times.
        # TODO: might be good for method functions to actually operate on super()
        # not self.__config.
        super().__init__(self.__config)

    # on init, ensure that the config is valid, and all required keys and files are present
    def __validate(self):
        if self.__config is None:
            raise ValueError("configParser is not initialized")
        # ensure all required keys are present
        for key in REQUIRED_KEYS:
            if key not in self.__config:
                raise ValueError(f"configParser is missing required key: {key}")
        # in puzzleSets, ensure all required keys are present
        for puzzle_set in self.__config["puzzleSets"].values():
            for key in REQUIRED_PUZZLE_KEYS:
                if key not in puzzle_set:
                    raise ValueError(f"configParser is missing required key: {key}")
                if key == "file" and not os.path.isfile(
                    self.__config["puzzleDir"] + puzzle_set[key]
                ):
                    raise FileNotFoundError(
                        f"configParser is missing required file: {puzzle_set[key]}"
                    )

    def get_config(self) -> dict:
        return self.__config

    def keys(self) -> list:
        return list(self.__config.keys())

    def __getitem__(self, key: str):
        multi_key = key.split(".")
        if len(multi_key) > 1:
            return self.__config[multi_key[0]][multi_key[1]]
        elif self.__fix is not None:
            return self.__config[self.__fix][key]
        return super().__getitem__(key)

    # move the config to a specific key, so getitem will only return values from that key
    def moveto(self, key):
        if key in self.__config:
            self.__fix = key

    # reset the config to the root
    def root(self):
        self.__fix = None

    # return puzzle values in a dict
    def puzzle(self, key: str):
        return self.__config["puzzleSets"][key]

    # return puzzle values in a tuple, with an expected order
    # (don't change the order this returns, other code depends on it)
    def puzzle_values(self, key: str):
        p = self.puzzle(key)
        return p["file"], p["numPuzzles"], p["offset"], p["size"]
        

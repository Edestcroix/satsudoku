import json
import os


REQUIRED_KEYS = ["puzzleDir", "cacheDir", "defaultPuzzleSet", "puzzleSets"]
REQUIRED_PUZZLE_KEYS = ["file", "numPuzzles", "offset", "size"]


# Wrapper around dict that prevents modification, good because this ensures that
# the config will never be modified after it is loaded. (Unless you cast it to a
# regular dict and back, but don't do that)
class lockedDict(dict):
    def __init__(self, data):
        self.__data = data
        super().__init__(self.__data)

    def __getitem__(self, key):
        return self.__data[key]

    def __setitem__(self):
        raise TypeError("lockedDict is immutable")


# Wrapper around dict that loads a json file and validates it on init, and
# locks itself after init to be immutable, ensuring that the config will never
# be modified after it is loaded during runtime. Also provides a few helper
# functions to retrieve specific values from the config easier.
class Config(dict):
    def __init__(self, config_file: str):
        self.__config_file = config_file
        self.__fix = None
        with open(self.__config_file, "r") as f:
            self.__config = json.load(f)

        self.__validate()

        for puzzle_set in self.__config["puzzleSets"].values():
            puzzle_set["file"] = f"{self.__config['puzzleDir']}{puzzle_set['file']}"

        # map all dicts in the config to lockedDicts
        for key in self.__config.keys():
            if type(self.__config[key]) == dict:
                self.__config[key] = lockedDict(self.__config[key])

        # lock the config
        self.__config = lockedDict(self.__config)

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
        

    def __setitem__(self):
        raise TypeError("Config is immutable")

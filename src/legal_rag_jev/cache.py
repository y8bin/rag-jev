from pathlib import Path
from .io import read_json, write_json


class Cache:
    def __init__(self, directory: str, enabled: bool = True):
        self.directory = Path(directory)
        self.enabled = enabled

    def get(self, key: str):
        p = self.directory / key[:2] / (key + ".json")
        return read_json(p) if self.enabled and p.is_file() else None

    def put(self, key: str, value: dict):
        if self.enabled:
            write_json(self.directory / key[:2] / (key + ".json"), value)

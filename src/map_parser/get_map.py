from .map_checker import Map, map_creator
from typing import List
from pathlib import Path
from colorama import Style, Fore
import os


C_RED = Fore.RED
C_CLEAR = Style.RESET_ALL


def get_maps(location: str) -> List[Map]:
    try:
        all_maps: List[Map] = []
        parent_dir = Path(location)
        if not os.access(parent_dir, os.R_OK):
            raise PermissionError(
                f"{C_RED}Cannot access '{location}' directory.{C_CLEAR}")
        if not parent_dir.is_dir():
            raise TypeError(
                f"{C_RED}'{location}' isn't a directory.{C_CLEAR}")
        maps_path = [map for map in parent_dir.rglob("*.txt") if map.is_file()]
        for map in maps_path:
            all_maps.append(map_creator(map))

    except Exception as err:
        raise err

    return all_maps

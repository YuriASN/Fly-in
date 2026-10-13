from .map_checker import Map, map_creator
from typing import List, Dict
import pathlib
from pydantic import BaseModel, Field
from colorama import Style, Fore
import os
import traceback


C_RED = Fore.RED
C_CLEAR = Style.RESET_ALL


class Level(BaseModel):
    name: str = Field(...,
                      description="The name of the level")
    maps_amount: int = Field(default=0,
                             description="The amount of maps this level has.")
    maps: List[Map] = Field(default=[],
                            description="All the maps on this level")


def fix_coordinates(maps: List[Map]) -> None:
    """
    Fix the coordinates of all the maps removing the negative numbers.
    On each map, it finds the lowest negative x and y in a hub,
    and add it's value to all hubs coordinations.
    """
    try:
        for map in maps:
            x = min(map.start_hub.x, map.end_hub.x)
            y = min(map.start_hub.y, map.end_hub.y)
            for hub in map.hubs:
                x = min(hub.x, x)
                y = min(hub.y, y)
            if x != 0 or y != 0:
                for hub in map.hubs:
                    hub.x = hub.x + (x * -1)
                    hub.y = hub.y + (y * -1)

    except Exception as err:
        raise Exception(f"Fixing coordinates: {err}") from err


def get_maps(location: str) -> List[Level]:
    try:
        all_maps: List[Map] = []
        parent_dir = pathlib.Path(location)
        if not os.access(parent_dir, os.R_OK):
            raise PermissionError(
                f"{C_RED}Cannot access '{location}' directory.{C_CLEAR}")
        if not parent_dir.is_dir():
            raise TypeError(
                f"{C_RED}'{location}' isn't a directory.{C_CLEAR}")
        maps_path = [map for map in parent_dir.rglob("*.txt") if map.is_file()]
        for map in maps_path:
            all_maps.append(map_creator(map))

        fix_coordinates(all_maps)
    except Exception as err:
        raise err

    try:
        levels: Dict[str, Level] = {}
        levels_maps: Dict[str, List[Map]] = {}
        for map in all_maps:
            levels_maps.setdefault(map.level, []).append(map)
        for key in levels_maps.keys():
            levels[key] = Level(name=key)
            levels[key].maps.extend(levels_maps[key])
    except Exception as err:
        raise Exception(f"{C_RED}Creating levels: {err}"
                        f"{C_CLEAR}\n\n{traceback.format_exc()}")

    return list(levels.values())

#! .venv/bin python3.10

from .path_finder import get_path, Path
from .path_organizer import order_paths, remove_double
from ..map_parser import get_maps, Map
from typing import List, TypedDict
from colorama import Fore, Style
import traceback


class MapData(TypedDict):
    map: Map
    all_paths: List[Path]


def print_hub_links(all_maps: List[Map]) -> None:
    for each in all_maps:
        print(f"In map {each.name}:")
        hubs = [each.start_hub, *each.hubs, each.end_hub]
        for hub in hubs:
            print(f"\thub {hub.name} has {len(hub.links)} links")
    # exit()


def print_paths(paths: List[Path]) -> None:
    for each in paths:
        hub_list = each.links[0].names[0]
        for conn in each.links:
            hub_list += " -> " + conn.names[1]
        print(f"\t({len(each.links)} - {each.priority} - "
              f"{each.moving / each.turns:.3}) {hub_list}")


def print_maps_paths(all_data: List[MapData]) -> None:

    # Print map name and all it's paths
    for map in all_data:
        print(f"Map {map['map'].name} has paths:\n\t", end="")
        print_paths(map["all_paths"])


if __name__ == "__main__":
    try:
        all_data: List[MapData] = []
        all_maps = get_maps("maps")
        # print_hub_links(all_maps)
        print("Maps loaded")
        # Get Paths for each map
        for each in all_maps:
            print(f"Getting paths from: '{each.name}'")
            paths = get_path(each.start_hub, each.end_hub.name, [], [])
            if not paths:
                raise Exception(
                    f"Map '{each.name}' has no path linking hubs start to end")
            all_data.append(
                {"map": each,
                 "all_paths": paths
                 }
            )
        print("All paths loaded")
        # print_maps_paths(all_data)
        for each in all_data:
            print(f"\n{Fore.GREEN}Map '{each['map'].name}':\n"
                  f"Normal:{Style.RESET_ALL}")
            print_paths(each["all_paths"])
            each["all_paths"] = order_paths(each["all_paths"])
            print(f"\n{Fore.GREEN}Ordered:{Style.RESET_ALL}\n")
            print_paths(each["all_paths"])
            each["all_paths"] = remove_double(each["all_paths"])
            print(f"\n{Fore.GREEN}Removed doubles:{Style.RESET_ALL}\n")
            print_paths(each["all_paths"])
            print("-" * 50)

    except KeyboardInterrupt as interr:
        print(f"{interr}\n\n{traceback.format_exc()}")
    except BaseException as err:
        print(f"{err}\n\n{traceback.format_exc()}")

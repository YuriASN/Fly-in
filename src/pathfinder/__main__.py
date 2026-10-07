#! .venv/bin python3.10

from .path_finder import get_path, Path
from ..map_parser import get_maps, Map
from typing import List, TypedDict


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


def print_maps_paths(all_data: List[MapData]) -> None:
    # Print map name and all it's paths
    for map in all_data:
        print(f"Map {map['map'].name} has paths:")
        for path in map["all_paths"]:
            hub_list = path.path[0].names[0]
            for conn in path.path:
                hub_list += " -> " + conn.names[1]
            print(f"\t{hub_list}")
            print()


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

        # print_maps_paths(all_data)

    except KeyboardInterrupt as interr:
        raise interr
    except BaseException as err:
        print(err)

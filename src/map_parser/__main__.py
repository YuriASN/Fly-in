#! .venv/bin python3.10

from .get_map import get_maps

if __name__ == "__main__":
    try:
        maps = get_maps("maps")
        for map in maps:
            print(str(map.level) + " | " + map.name)
    except BaseException as err:
        print(err)

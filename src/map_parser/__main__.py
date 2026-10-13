#! .venv/bin python3.10

from .get_map import get_maps

if __name__ == "__main__":
    try:
        levels = get_maps("maps")
        for level in levels:
            print(f"Level: {level.name}")
            for map in level.maps:
                print(f"\t{map.name}")
    except BaseException as err:
        print(err)

#!.venv/bin python3.10

from typing import List
from colorama import Style, Fore
from .path_finder import Path
import pandas as pd
import traceback


C_RED = Fore.RED
C_CLEAR = Style.RESET_ALL


def remove_double(paths: List[Path]) -> List[Path]:
    """
    Remove all the paths that goes though a hub that's already being used.
    (Start and end hub are not counted)
    """
    passed_names: List[str] = []
    removed = 0
    for i in range(len(paths)):
        remove = False
        for link in paths[i - removed].links:
            if link.names[1] in passed_names:
                remove = True
                break
            if len(link.hubs[1].links):
                # Add the hub to the list if it isn't the last hub
                passed_names.append(link.names[1])
        if remove:
            paths.pop(i - removed)
            removed += 1
            if i + removed == len(paths):
                break

    return paths


def order_paths(paths: List[Path]) -> List[Path]:
    """
    Orders the list of Path accordingly to priority and less turns to get more
    drones in the end. Removing paths the double use a hub.
    Returns the ordered list.
    """
    try:
        df = pd.DataFrame({
            "path": paths,
            "priority": [path.priority for path in paths],
            "ratio": [path.moving / path.turns for path in paths]
        })
        df = df.sort_values(
            ["priority", "ratio"], ascending=False)

        sorted_list = [
            Path.model_validate(row)
            for row in df["path"]
        ]

        # sorted_list = remove_double(sorted_list) # Implement here or outside
    except Exception as err:
        raise Exception(f"{C_RED}Ordering paths: {err}{C_CLEAR}\n"
                        f"{traceback.format_exc()}") from err

    return sorted_list

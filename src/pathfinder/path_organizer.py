#!.venv/bin python3.10

from typing import List
from colorama import Style, Fore
from .path_finder import Path
import pandas as pd
import traceback


C_RED = Fore.RED
C_CLEAR = Style.RESET_ALL


def _remove_double(paths: List[Path]) -> List[Path]:
    """
    Remove all the connections that are already used by another path.
    This leaves only the connection that will lead to a different path.
    That way when a turn is being done it doesn't have to search nothing
    on the hubs that already changed.
    """
    try:
        passed_names: List[str] = []
        for path in paths:
            removed = 0
            for i in range(len(path.links)):
                # If next hub has being used, pop the connection
                if path.links[i - removed].names[1] in passed_names:
                    path.hub_names.remove(path.links[i - removed].names[0])
                    path.links.pop(i - removed)
                    removed += 1
                # If not append the hub to the list of passed
                elif len(path.links[i - removed].hubs[1].links):
                    passed_names.append(path.links[i - removed].names[1])
        return paths
    except Exception as err:
        raise Exception(f"While removing double: {err}")


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

        sorted_list = _remove_double(sorted_list)
        return sorted_list

    except Exception as err:
        raise Exception(f"{C_RED}Ordering paths: {err}{C_CLEAR}\n"
                        f"{traceback.format_exc()}") from err

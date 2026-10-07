#!.venv/bin python3.10

from typing import List
from colorama import Style, Fore
from .path_finder import Path
import pandas as pd
import traceback


C_RED = Fore.RED
C_CLEAR = Style.RESET_ALL


def order_paths(paths: List[Path]) -> List[Path]:
    """
    Orders the list of Path accordingly to priority and less turns to get more drones in the end. Removing paths the double use a connection. Returns the ordered list.
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

    except Exception as err:
        raise Exception(f"{C_RED}Ordering paths: {err}{C_CLEAR}\n"
                        f"{traceback.format_exc()}") from err

    return sorted_list

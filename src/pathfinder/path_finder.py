from ..map_parser import Hub, Connection
from typing import List
from pydantic import Field, BaseModel, ValidationError
import traceback
from colorama import Style, Fore


C_RED = Fore.RED
C_CLEAR = Style.RESET_ALL


class Path(BaseModel):
    links: List[Connection] = Field(
        ..., description="List of valid connections "
        "connecting start_hub to end_hub")
    turns: int = Field(
        ..., description="Total amount of turns a drone need to go through "
        "this path")
    moving: int = Field(
        ..., description="Max amount of drones that the path can move at once")
    priority: int = Field(
        ..., description="Amount of priority hubs on this path")


def get_path(hub: Hub, end: str, all_paths: List[Path],
             conns: List[Connection], turns: int = 0,
             priority: int = 0, moving: int = -1) -> List[Path]:
    """
    Return a list with all the paths available from hub to end.
    It does a recursive search until a blocked hub or end hub are found.
    """
    try:
        for link in hub.links:
            if link.hubs[0].name == hub.name:
                next_hub = link.hubs[1]
            else:
                next_hub = link.hubs[0]
            for each in conns:
                if next_hub.name in each.names:
                    return all_paths
            if next_hub.zone == "blocked":
                return all_paths
            elif next_hub.zone == "restricted":
                turns += 1
            elif next_hub.zone == "priority":
                priority += 1
            if moving == -1:
                moving = min(link.max_drones, next_hub.max_drones)
            else:
                moving = min([link.max_drones, next_hub.max_drones, moving])
            if moving == 0:
                return all_paths
            conns.append(link)
            turns += 1

            if next_hub.name == end:
                all_paths.append(
                    Path(links=conns, turns=turns,
                         moving=moving, priority=priority))
                conns.pop()
                return all_paths
            else:
                all_paths = get_path(next_hub, end, all_paths,
                                     conns, turns, priority, moving)
                conns.pop()

    except ValidationError as err:
        raise Exception(f"{C_RED}Getting path from map:\n"
                        f"\t{err}{C_CLEAR}") from err
    except Exception as err:
        raise Exception(f"{C_RED}Getting path from map:\n"
                        f"\t{err}{C_CLEAR}\n\n{traceback.format_exc()}")

    return all_paths

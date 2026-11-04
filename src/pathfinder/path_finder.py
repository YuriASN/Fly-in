from map_parser import Hub, Connection
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
            turns_add = 1
            priority_add = 0
            if link.hubs[0].name == hub.name:
                next_hub = link.hubs[1]
            else:
                next_hub = link.hubs[0]
            if any(next_hub.name in conn.names for conn in conns):
                    continue
            if next_hub.zone == "blocked":
                continue
            elif next_hub.zone == "restricted":
                turns_add += 1
            elif next_hub.zone == "priority":
                priority_add = 1
            if moving == -1:
                moving_new = min(link.max_drones, next_hub.max_drones)
            else:
                moving_new = min(
                    [link.max_drones, next_hub.max_drones, moving]
                )
            if moving_new == 0:
                continue
            conns.append(link)

            if next_hub.name == end:
                all_paths.append(
                    Path(links=list(conns), turns=turns + turns_add,
                         moving=moving_new, priority=priority + priority_add))
                conns.pop()
                continue
            else:
                all_paths = get_path(next_hub, end, all_paths,
                                     conns, turns + turns_add,
                                     priority + priority_add, moving_new)
                conns.pop()

        return all_paths

    except ValidationError as err:
        raise Exception(f"{C_RED}Getting path from map:\n"
                        f"\t{err}{C_CLEAR}") from err
    except Exception as err:
        raise Exception(f"{C_RED}Getting path from map:\n"
                        f"\t{err}{C_CLEAR}\n\n{traceback.format_exc()}")

    return all_paths

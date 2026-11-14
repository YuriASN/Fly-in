from .map_checker import Map

""" DELETE
Run everything from end to start to free the hubs the drones are going into.
from last hub:
    If next hub, move drone to the hub or connection if hub is retricted.
    (Always checking if where ever it's going (conn or hub) is free to receive)
    if curr_hub is restricted, check if prev connection has drones to move to it.
    how to cache a turn to be used at step_backwards
"""

def step_forward(map: Map) -> Map:
    """
    Do a turn on the drones movement
    """
    print("forward, no cache")#
    try:
        for path in map.paths:
            conns = reversed(path.links)
            for conn in conns:
                prev_hub, next_hub = conn.hubs[0], conn.hubs[1]
                # If drones in connection (next_hub is restricted).
                if conn.drone_count:
                    # Move from connection to next_hub.
                    while conn.drone_count:
                        next_hub.put_drone(conn.pop_drone())
                    # Move from prev_hub to connection.
                    while prev_hub:
                        conn.put_drone(prev_hub.pop_drone())
                # If hub is normal and prev_hub has drones, move to the next.
                elif prev_hub.drone_count:
                    while prev_hub.drone_count:
                        next_hub.put_drone(prev_hub.pop_drone())
        map.turn += 1
        return map

    except Exception as err:
        raise Exception(f"While stepping forward: {err}\n")


def step_backwards(map: Map) -> Map:
    """
    Rollback the last drone movement
    """
    print("backward, no cache")#
    map.turn -= 1
    return map

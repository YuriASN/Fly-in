from .map_checker import Map


def step_forward(map: Map) -> Map:
    """
    Do a turn on the drones movement
    """
    try:
        #Need to change secondary paths to have only the connections that the main path doesn't have creating a drone flag to tell if can move
        #for path in map.paths:
        path = map.paths[0]
        #print(f"Using path:\n\t{path.links[0].names[0]} -> {' -> '.join([link.names[1] for link in path.links])}")#
        conns = reversed(path.links)
        for conn in conns:
            prev_hub, next_hub = conn.hubs[0], conn.hubs[1]
            # If drones in connection (next_hub is restricted).
            if conn.drone_count:
                # Move from connection to next_hub.
                while conn.drone_count and next_hub.max_drones > next_hub.drone_count:
                    next_hub.put_drone(conn.pop_drone())
                # Move from prev_hub to connection.
                while prev_hub and conn.max_drones > conn.drone_count:
                    conn.put_drone(prev_hub.pop_drone())
            # If hub is normal and prev_hub has drones, move to the next.
            elif prev_hub.drone_count:
                while prev_hub.drone_count and next_hub.max_drones > next_hub.drone_count:
                    next_hub.put_drone(prev_hub.pop_drone())
        map.turn += 1
        return map

    except Exception as err:
        raise Exception(f"While stepping forward: {err}\n")

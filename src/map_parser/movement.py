from .map_checker import Map


def step_forward(map: Map) -> Map:
    """
    Do a turn on the drones movement
    """
    try:
        turn = map.turn
        #Run the paths together. Run main path until a hub on another path shows up running that hub too. then run the other path until the same point, and get back running the main path until another one shows up. MAYBE use this implementation below on a secondary function and just do the loop here.
        for path in map.paths:
            conns = reversed(path.links)
            for conn in conns:
                prev_hub, next_hub = conn.hubs[0], conn.hubs[1]
                # If drones in connection (next_hub is restricted).
                if conn.drone_count:
                    pop_count = 0
                    # Move from connection to next_hub.
                    for i in range(conn.drone_count):
                        if next_hub.max_drones > next_hub.drone_count:
                            popped = conn.pop_drone(turn,
                                                    i - pop_count)
                            # If drone can be moved
                            if popped:
                                next_hub.put_drone(popped, turn)
                                next_hub.drones_coming -= 1
                                pop_count += 1
                        else:
                            print("Hub can't fit the drone from the "
                                  "connection. This shouldn't happen.")
                            break
                    pop_count = 0
                    # Move from prev_hub to connection.
                    for i in range(prev_hub.drone_count):
                        # Checks if connection and hub can support the drone
                        if (
                            conn.max_drones > conn.drone_count
                            and next_hub.max_drones > conn.drone_count
                            and next_hub.drones_coming < next_hub.max_drones
                        ):
                            popped = prev_hub.pop_drone(turn,
                                                        i - pop_count)
                            if popped:
                                conn.put_drone(popped, turn)
                                next_hub.drones_coming += 1
                                pop_count += 1
                        else:
                            break

                # If hub is normal and prev_hub has drones, move to the next.
                elif prev_hub.drone_count:
                    pop_count = 0
                    for i in range(prev_hub.drone_count):
                        if (next_hub.max_drones > next_hub.drone_count):
                            popped = prev_hub.pop_drone(turn, i - pop_count)
                            if popped:
                                next_hub.put_drone(popped, turn)
                                pop_count += 1
                        else:
                            break

        map.turn += 1
        return map

    except Exception as err:
        raise Exception(f"While stepping forward: {err}\n")

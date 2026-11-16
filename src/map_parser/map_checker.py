"""
This module Creates the map along with all it's itens and handles it's
movements.
"""
from __future__ import annotations
from pydantic import (
    BaseModel, Field, model_validator, ValidationError, TypeAdapter)
from typing import List, Tuple, Optional, Dict, Literal
from colorama import Style, Fore
from collections import Counter
from pathlib import Path
from abc import ABC
import traceback


C_RED = Fore.RED
C_CLEAR = Style.RESET_ALL
Zones = Literal["normal", "restricted", "priority", "blocked"]


class DuplicatedError(BaseException):
    """
    Duplicated value
    """
    pass


class Coordinates(BaseModel):
    x: int = 0
    y: int = 0


class MapSnapshot(BaseModel):
    turn: int
    start_hub: Hub
    end_hub: Hub
    hubs: List[Hub]
    connections: List[Connection]

    def __init__(self, turn: int, start_hub: Hub, end_hub: Hub,
                 hubs: List[Hub], connections: List[Connection]) -> None:
        try:
            super().__init__(
                turn=turn,
                start_hub=start_hub,
                end_hub=end_hub,
                hubs=hubs,
                connections=connections
                )
        except Exception as err:
            raise Exception(f"Creating map snapshot: {err}")


class Drone(BaseModel):
    move_turn: int = Field(
        default=0, description="The turn when it can leave the connection")
    next_hub: Optional["Hub"] = Field(
        default=None, description="Next hub it'll go to, when on a link")


class DroneHandlers(ABC, BaseModel):
    max_drones: int = Field(
        default=1, ge=0, description="Max of drones it supports")
    drones_in: List[Drone] = Field(
        default=[], description="Current drones on it")
    drone_count: int = Field(
        default=0, description="The amount of drones on it")

    def put_drone(self, drone: Drone) -> None:
        """
        Add a drone to the drones_in list and increase the drone count.
        """
        try:
            self.drones_in.append(drone)
            self.drone_count += 1
        except Exception as err:
            raise Exception(f"Putting drone at '{type(self)}':\n\t{err}")

    def pop_drone(self, index: int = 0) -> Drone:
        """
        Remove the drone at the 'index' from the drones_in list and
        decrease the drone count.
        """
        if not self.drone_count:
            raise ValueError(f"No drone to pop on the '{type(self)}'.")
        try:
            self.drone_count -= 1
            return self.drones_in.pop(index)
        except Exception as err:
            raise Exception(f"Removing drone from '{type(self)}':\n\t{err}")


class Hub(DroneHandlers):
    name: str = Field(
        ..., description="Name of the hub")
    zone: Zones = Field(
        default="normal", description="The type of the zone")
    x: int = Field(
        ..., description="X coordinate of the hub")
    y: int = Field(
        ..., description="Y coordinate of the hub")
    color: str = Field(
        ..., description="Color to representate the hub")
    links: List["Connection"] = Field(
        default=[], description="The connections this Hub has outgoing")

    @model_validator(mode="after")
    def validade_hub(self) -> "Hub":
        all_zones = ["normal", "restricted", "priority", "blocked"]
        name = self.name
        if "-" in name:
            raise ValueError(
                f"Name '{name}' contains dashes.")
        if any(c.isspace() for c in name):
            raise ValueError(f"Name '{name}' has spaces.")
        if any(c.isspace() for c in self.color):
            raise ValueError(f"{name}'s color '{self.color}' isn't valid.")
        if self.zone not in all_zones:
            raise ValueError(f"{name}'s zone '{self.zone}' isn't valid.")

        return self


class Connection(DroneHandlers):
    names: List[str] = Field(
        ..., min_length=2, max_length=2, description="Names of both hubs")
    hubs: Tuple[Hub, Hub] = Field(
        ..., description="Tuple with the 2 hubs connected")

    @model_validator(mode="after")
    def conn_validate(self) -> "Connection":
        # Validate if connection is duplicated
        hub1_links = [
            "_".join(sorted(link.names)) for link in self.hubs[0].links]
        hub2_links = [
            "_".join(sorted(link.names)) for link in self.hubs[1].links]
        if len(set(hub1_links)) != len(hub1_links) or \
           len(set(hub2_links)) != len(hub2_links):
            raise DuplicatedError(
                            "There's more than one connection in between "
                            f"'{self.hubs[0].name}' and '{self.hubs[1].name}'")

        return self

    def add_to_hub(self) -> None:
        # Add connection to outgoing hub
        self.hubs[0].links.append(self)


class Map(BaseModel):
    level: str = Field(..., description="Level of the map")
    name: str = Field(..., description="Name of the map")
    start_hub: Hub = Field(..., description="Hub where all the drones start")
    end_hub: Hub = Field(..., description="Goal hub for the drones")
    hubs: List[Hub] = Field(..., description="All the other hubs on the map")
    connections: List[Connection] = Field(
        ..., min_length=1, description="All the connections on the map")
    turn: int = Field(default=0, description="Current turn")
    grid_size: Coordinates = Field(default_factory=Coordinates,
                                   description="Size of the grid")
    total_drones: int = Field(..., ge=1,
                              description="Total amount of drones on this map")
    paths: List = Field(
        default=[], description="All the available paths on the map")

    @model_validator(mode="after")
    def validate_map(self) -> "Map":
        # Validate the level
        if self.level == "maps":
            self.level = ""
        # Validate Hub duplicated names
        duplicates = [
            name
            for name, count in Counter(item.name for item in self.hubs).items()
            if count > 1
        ]
        if duplicates:
            raise DuplicatedError(f"The {duplicates} are duplicated hubs!")

        return self

    def move(self, go_turn: int) -> None:
        """
        Move the map to the turn provided as an argument.
        It first checks if there's a snapshot of that turn done, and only if
        not it do the changes for the turn saving it on the snapshot.

        Args:
            go_turn: int = The turn the map has to be on it.
        """
        try:
            if go_turn < 0:
                raise ValueError(
                    f"Turn value '{go_turn}' is invalid.")
            if not self.paths:
                raise ValueError(
                    "Moving the map, no 'paths' provided."
                )

            # If it's first call creates the snapshot of turn 0
            if not hasattr(self, "_snapshots"):
                self._snapshots = {self.turn: MapSnapshot(
                    self.turn,
                    self.start_hub.model_copy(deep=True),
                    self.end_hub.model_copy(deep=True),
                    [hub.model_copy(deep=True) for hub in self.hubs],
                    [conn.model_copy(deep=True) for conn in self.connections]
                )}

            if go_turn == self.turn:
                return

            # If turn exists on a snapshot, just use it.
            if go_turn in self._snapshots.keys():
                self.turn = self._snapshots[go_turn].turn
                self.start_hub = self._snapshots[go_turn].start_hub
                self.end_hub = self._snapshots[go_turn].end_hub
                self.hubs = self._snapshots[go_turn].hubs
                self.connections = self._snapshots[go_turn].connections
                return

            # Call step forward to move the drones to the turn
            from .movement import step_forward
            if go_turn > self.turn:
                while go_turn != self.turn:
                    self = step_forward(self)
                    self._snapshots.update(
                        {self.turn: MapSnapshot(
                            self.turn,
                            self.start_hub.model_copy(deep=True),
                            self.end_hub.model_copy(deep=True),
                            [hub.model_copy(deep=True)
                             for hub in self.hubs],
                            [conn.model_copy(deep=True)
                             for conn in self.connections]
                             )})
            else:
                raise ValueError(f"Turn {go_turn} should be on the snapshot!")

        except Exception as err:
            raise Exception(f"Moving the map: {err}")


def map_creator(map_file: Path) -> Map:
    def hub_factory(value: str) -> Hub:
        try:
            _zone_adapter: TypeAdapter[Zones] = TypeAdapter(Zones)
            zone = _zone_adapter.validate_python("normal")
            zone_flag = False
            name, x, y = value.split(" ")[:3]
            if value.find("[") != -1:
                color, max_drones = "", 1
                values = value[value.find("[") + 1:value.rfind("]")].split(" ")
                for each in values:
                    if each.startswith("zone"):
                        if zone_flag:
                            raise DuplicatedError(
                                f"On hub '{name}' zone is duplicated!")
                        raw_zone = each.split("=")[1]
                        zone = _zone_adapter.validate_python(raw_zone)
                        zone_flag = True
                    elif each.startswith("color"):
                        if color:
                            raise DuplicatedError(
                                f"On hub '{name}' color is duplicated!")
                        color = each.split("=")[1]
                    elif each.startswith("max_drones"):
                        if max_drones != 1:
                            raise DuplicatedError(
                                f"On hub '{name}' max_drones is duplicated!")
                        max_drones = int(each.split("=")[1])
                    else:
                        raise KeyError(
                            f"'{each.split('=')[0]}' isn't a valid "
                            "metadata for a hub!")
            hub = Hub(name=name, zone=zone, x=int(x), y=int(y),
                      color=color, max_drones=max_drones)

        except (ValidationError, DuplicatedError) as err:
            raise Exception(f"Error validating hub: {err}")
        except Exception as err:
            raise Exception(f"Getting data for a hub: {err}")

        return hub

    def connection_factory(
            value: str, start: Hub, end: Hub, hubs: List[Hub]) -> Connection:
        try:
            max_drones = 1
            if value.find("[") != -1:
                metadata = value[value.find("[") + 1:value.rfind("]")]
                value = value[:value.find(" ")]
                if not metadata.startswith("max_link_capacity"):
                    raise KeyError(f"'{metadata.split('=')[0]}' isn't a valid "
                                   "metada for a connection!")
                max_drones = int(metadata.split("=")[1])
            points = value.split("-")
            if points[0] == points[1]:
                raise ValueError("Connection is in and out of the same hub "
                                 f"'{points[0]}'")
            objects_by_name: Dict[str, Hub] = {
                obj.name: obj for obj in [*hubs, start, end]}
            hub1 = objects_by_name.get(points[0])
            hub2 = objects_by_name.get(points[1])
            if not hub1:
                raise ValueError(f"hub '{points[0]}' doesn't exist.")
            if not hub2:
                raise ValueError(f"hub '{points[1]}' doesn't exist.")
            conn = Connection(names=value.split("-"),
                              hubs=(hub1, hub2), max_drones=max_drones)
            conn.add_to_hub()

        except (ValidationError, DuplicatedError) as err:
            raise Exception(f"Error validating hub: {err}")
        except Exception as err:
            raise Exception(f"Getting data for a connection: {err}")
        return conn

    try:
        hubs: List[Hub] = []
        connections: List[Connection] = []
        drones: List[Drone] = []
        with map_file.open("r") as file:
            while True:
                line = file.readline()
                if not line:
                    break
                if line.strip().startswith("#") or line.isspace():
                    continue
                key, value = line.split(":")
                if key == "hub":
                    hubs.append(hub_factory(value.strip()))
                elif key == "start_hub":
                    start_hub: Hub = hub_factory(value.strip())
                elif key == "end_hub":
                    end_hub: Hub = hub_factory(value.strip())
                elif key == "connection":
                    connections.append(
                        connection_factory(value.strip(), start_hub,
                                           end_hub, hubs))
                elif key == "nb_drones":
                    if drones:
                        raise DuplicatedError(
                            "Variable 'nb_drones' is duplicated!")
                    nb_drones = int(value)
                    if nb_drones < 1:
                        raise ValueError(
                            f"Number of drones '{nb_drones}'"
                            "isn't greater than 0!"
                        )
                    for _ in range(int(value)):
                        drones.append(Drone())
        name = map_file.name[map_file.name.find("_") + 1:]
        name = name[:name.rfind(".")].replace("_", " ").title()
        start_hub.drones_in = drones
        start_hub.drone_count = len(drones)
        end_hub.max_drones = nb_drones
        map = Map(name=name, level=map_file.parent.name,
                  start_hub=start_hub, end_hub=end_hub,
                  hubs=hubs, connections=connections, total_drones=nb_drones)

    except (ValidationError, DuplicatedError) as err:
        raise Exception(
            f"{C_RED}Creating map '{map_file.name}': {err}{C_CLEAR}")
    except Exception as err:
        raise Exception(f"{C_RED}Creating map '{map_file.name}': {err}"
                        f"{C_CLEAR}\n\n{traceback.format_exc()}")

    return map

from pydantic import BaseModel, Field, model_validator, ValidationError
from typing import List, Tuple, Optional
from colorama import Style, Fore
from collections import Counter
from pathlib import Path
import traceback


C_RED = Fore.RED
C_CLEAR = Style.RESET_ALL


class DuplicatedError(BaseException):
    """
    Duplicated value
    """
    pass


class Drone(BaseModel):
    move_turn: int = Field(
        default=0, description="The turn when it can leave the connection")
    next_hub: Optional["Hub"] = Field(
        default=None, description="Next hub it'll go to, when on a link")


class Hub(BaseModel):
    name: str = Field(
        ..., description="Name of the hub")
    zone: str = Field(
        ..., description="The type of the zone")
    x: int = Field(
        ..., description="X coordinate of the hub")
    y: int = Field(
        ..., description="Y coordinate of the hub")
    color: str = Field(
        ..., description="Color to representate the hub")
    max_drones: int = Field(
        default=1, ge=0, description="Max of drones the hub supports")
    drones_in: List[Drone] = Field(
        default=[], description="Current drones on the hub")
    links: List["Connection"] = Field(
        default=[], description="The connections this Hub has")

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


class Connection(BaseModel):
    names: List[str] = Field(
        ..., min_length=2, max_length=2, description="Names of both hubs")
    hubs: Tuple[Hub, Hub] = Field(
        ..., description="Tuple with the 2 hubs connected")
    max_drones: int = Field(
        default=1, ge=1, description="Max of drones the link supports")
    drones_in: List[Drone] = Field(
        default=[], description="List of Drone on the link")

    @model_validator(mode="after")
    def conn_validate(self) -> "Connection":
        # Add connection to both hubs
        self.hubs[0].links.append(self)
        self.hubs[1].links.append(self)

        # Validate if connection is duplicated
        hub1_links = [id(link) for link in self.hubs[0]]
        hub2_links = [id(link) for link in self.hubs[1]]
        if len(set(hub1_links)) != len(hub1_links) or \
           len(set(hub2_links)) != len(hub2_links):
            raise DuplicatedError(
                            "There's more than one connection in between "
                            f"'{self.hubs[0].name}' and '{self.hubs[1].name}'")

        return self


class Map(BaseModel):
    level: Optional[str] = Field(..., description="Level of the map")
    name: str = Field(..., description="Name of the map")
    start_hub: Hub = Field(..., description="Hub where all the drones start")
    end_hub: Hub = Field(..., description="Goal hub for the drones")
    hubs: List[Hub] = Field(..., description="All the other hubs on the map")
    connections: List[Connection] = Field(
        ..., min_length=1, description="All the connections on the map")
    turn: int = Field(default=0, description="Current turn")

    @model_validator(mode="after")
    def validate_map(self) -> "Map":
        # Validate the level
        if self.level == "maps":
            self.level = None
        # Validate Hub duplicated names
        duplicates = [
            name
            for name, count in Counter(item.name for item in self.hubs).items()
            if count > 1
        ]
        if duplicates:
            raise DuplicatedError(f"The {duplicates} are duplicated hubs!")

        return self


def map_creator(map_file: Path) -> Map:
    def hub_factory(value: str) -> Hub:
        try:
            name, x, y = value.split(" ")[:3]
            if value.find("[") != -1:
                zone, color, max_drones = "", "", 1
                values = value[value.find("[") + 1:value.rfind("]")].split(" ")
                for each in values:
                    if each.startswith("zone"):
                        if zone:
                            raise DuplicatedError(
                                f"On hub '{name}' zone is duplicated!")
                        zone = each.split("=")[1]
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
                if not zone:
                    zone = "normal"
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
            objects = [*hubs, start, end]
            objects_by_name = {obj.name: obj for obj in objects}
            hub1 = objects_by_name.get(points[0])
            hub2 = objects_by_name.get(points[1])
            if not hub1:
                raise ValueError(f"hub '{points[0]}' doesn't exist.")
            if not hub2:
                raise ValueError(f"hub '{points[1]}' doesn't exist.")
            conn = Connection(names=value.split("-"),
                              hubs=(hub1, hub2), max_drones=max_drones)

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
                if line.startswith("#") or line.isspace():
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
                    for _ in range(int(value)):
                        drones.append(Drone())
        map = Map(name=map_file.name, level=map_file.parent.name,
                  start_hub=start_hub, end_hub=end_hub,
                  hubs=hubs, connections=connections)

    except (ValidationError, DuplicatedError) as err:
        raise Exception(
            f"{C_RED}Creating map '{map_file.name}': {err}{C_CLEAR}")
    except Exception as err:
        raise Exception(f"{C_RED}Creating map '{map_file.name}': {err}"
                        f"{C_CLEAR}\n\n{traceback.format_exc()}")

    return map

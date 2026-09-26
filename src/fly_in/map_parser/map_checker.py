from pydantic import BaseModel, Field, model_validator, ValidationError
from typing import List, Dict, Any, Tuple
from colorama import Style, Fore
from collections import Counter
import traceback


C_ERROR = Fore.RED
C_CLEAR = Style.RESET_ALL


class Drone(BaseModel):
    move_turn: int = Field(
        default=0, description="The turn when it can leave the connection")
    next_hub: Hub | None = Field(
        default=None, description="Next hub it'll go to, when on a link")


class Hub(BaseModel):
    name: str = Field(...,
                      description="Name of the hub")
    zone: str = Field(...,
                      description="The type of the zone")
    x: int = Field(..., ge=0,
                   description="X coordinate of the hub")
    y: int = Field(..., ge=0,
                   description="Y coordinate of the hub")
    color: str = Field(...,
                       description="Color to representate the hub")
    max_drones: int = Field(default=1, ge=0,
                            description="Max of drones the hub supports")
    drones_in: List[Drone] = Field(default=[],
                           description="Current drones on the hub")

    @model_validator(mode="after")
    def validade_hub(self) -> "Hub":
        all_zones = ["normal", "restricted", "priority", "blocked"]
        name = self.name
        if "-" in name:
            raise ValidationError(
                f"{C_ERROR}Name '{name}' contains dashes.{C_CLEAR}")
        if any(c.isspace() for c in name):
            raise ValidationError(
                f"{C_ERROR}Name '{name}' has spaces.{C_CLEAR}")
        if any(c.isspace() for c in self.color):
            raise ValidationError(
                f"{C_ERROR}{name}'s color '{self.color}' isn't valid."
                f"{C_CLEAR}")
        if self.zone not in all_zones:
            raise ValidationError(
                f"{C_ERROR}{name}'s zone '{self.zone}' isn't valid."
                f"{C_CLEAR}")

        return self


class Connection(BaseModel):
    hubs: Tuple[Hub, Hub] = Field(...,
                      description="Tuple with the 2 hubs connected")
    max_drones: int = Field(default=1, ge=1,
                            description="Max of drones the link supports")
    drones_in: List[Drone] = Field(default=[],
                                   description="List of Drone on the link")


class Map(BaseModel):
    start_hub: Hub = Field(...,
                           description="Hub where all the drones start")
    end_hub: Hub = Field(...,
                         description="Goal hub for the drones")
    hubs: List[Hub] = Field(...,
                            description="All the other hubs on the map")
    connections: List[Connection] = Field(
        ..., description="All the connections on the map")
    turn: int = Field(default=0,
                      description="Current turn")

    @model_validator(mode="after")
    def validate_map(self) -> Map:
        # Validate Hub duplicated names
        duplicates = [
            name
            for name, count in Counter(item.name for item in self.hubs).items()
            if count > 1
        ]
        if duplicates:
            raise ValidationError(
                f"{C_ERROR}The {duplicates} are duplicated hubs!{C_CLEAR}")

        # Validate duplicated connections
        total_conn = len(self.connections)
        for i in range(total_conn - 1):
            hubs1_name = [each.name for each in self.connections[i].hubs]
            for j in range(i + 1, total_conn):
                hubs2_name = [each.name for each in self.connections[i].hubs]
                if set(hubs1_name) == set(hubs2_name):
                    raise ValidationError(
                        f"{C_ERROR}There's more than one connection in between"
                        f" '{hubs1_name[0]}' and '{hubs1_name[1]}'{C_CLEAR}")

        return self


def map_creator(map_file: str) -> Map:
    def hub_factory(value: str) -> Hub:
        try:
            name, x, y = value.split(" ")
            if value.find("[") != -1:
                zone, color, max_drones = "", "", 1
                values = value[value.find("[") + 1:value.rfind("]")].split(" ")
                for each in values:
                    if each.startswith("zone"):
                        if zone:
                            raise ValidationError(
                                f"{C_ERROR}On hub '{name}' zone is "
                                f" duplicated!{C_CLEAR}")
                        zone = each.split("=")[1]
                    elif each.startswith("color"):
                        if color:
                            raise ValidationError(
                                f"{C_ERROR}On hub '{name}' color is "
                                f" duplicated!{C_CLEAR}")
                        color = each.split("=")[1]
                    elif each.startswith("max_drones"):
                        if max_drones:
                            raise ValidationError(
                                f"{C_ERROR}On hub '{name}' max_drones is "
                                f" duplicated!{C_CLEAR}")
                        max_drones = int(each.split("=")[1])
                    else:
                        raise ValidationError(
                            f"{C_ERROR}'{each.split("=")[0]}' isn't a valid "
                            f"metadata for a hub!{C_CLEAR}")
                if not zone:
                    zone = "normal"
            hub = Hub(name=name, zone=zone, x=int(x), y=int(y),
                      color=color, max_drones=max_drones)

        except ValidationError as err:
            raise ValidationError(f"{C_ERROR}Error validating hub: {err}"
                                  f"{C_CLEAR}")
        except Exception as err:
            raise Exception(f"{C_ERROR}Getting data for a hub\n"
                            f"{traceback.format_exc()}{C_CLEAR}")

        return hub

    def connection_factory(
            value: str, start: Hub, end: Hub, hubs: List[Hub]) -> Connection:
        try:
            max_drones = 1
            if value.find("[") != -1:
                metadata = value[value.find("[") + 1:value.rfind("]")]
                value = value[:value.find(" ")]
                if not metadata.startswith("max_link_capacity"):
                    raise ValidationError(
                        f"{C_ERROR}'{metadata.split("=")[0]}' isn't a valid "
                        f"metada for a connection!{C_CLEAR}")
                max_drones = int(metadata.split("=")[1])
            points = value.split("-")
            if points[0] == points[1]:
                raise ValidationError(f"{C_ERROR}Connection is in and out of"
                                      f"the same hub '{points[0]}'{C_CLEAR}")
            hubs_names = [each.name for each in hubs]
            if any(point in hubs_names for point in points):
                for each in hubs:
                    if points[0] == each.name:
                        hub1 = each
                        points[0] = ""
                    elif points[1] == each.name:
                        hub2 = each
                        points[1] = ""
            if points[0] == start.name:
                hub1 = start
            elif points[0] == end.name:
                hub1 = end
            if points[1] == start.name:
                hub2 = start
            elif points[1] == end.name:
                hub2 = end
            
            conn = Connection(hubs=(hub1, hub2), max_drones=max_drones)
        except ValidationError as err:
            raise ValidationError(f"{C_ERROR}Error validating hub: {err}"
                                  f"{C_CLEAR}")
        except Exception as err:
            raise Exception(f"{C_ERROR}Getting data for a connection\n"
                            f"{traceback.format_exc()}{C_CLEAR}")
        return conn

    try:
        hubs: List[Hub] = []
        connections: List[Connection] = []
        drones: List[Drone] = []
        with open(map_file, "r") as file:
            while True:
                line = file.readline()
                if not line:
                    break
                if line.startswith("#") or line.isspace():
                    continue
                key, value = line.split(":")
                if key == "hub":
                    hubs.append(hub_factory(value))
                elif key == "connection":
                    connections.append(connection_factory(value, start_hub,
                                                          end_hub, hubs))
                elif key == "nb_drones":
                    if drones:
                        raise ValidationError(
                            f"{C_ERROR}Variable 'nb_drones' is duplicated!"
                            f"{C_CLEAR}")
                    for _ in range(int(value)):
                        drones.append(Drone())
                elif key == "start_hub":
                    start_hub: Hub = hub_factory(value)
                elif key == "end_hub":
                    end_hub: Hub = hub_factory(value)
        map = Map(start_hub=start_hub, end_hub=end_hub,
                  hubs=hubs, connections=connections)

    except ValidationError as err:
        raise err
    except Exception as err:
        raise Exception(f"{C_ERROR}Creating map: {err}\n"
                        f"{traceback.format_exc()}{C_CLEAR}")

    return map

import tkinter as tk
from typing import Tuple, List, Dict, TypedDict
from map_parser import Level, Map
from colorama import Fore, Style
from functools import partial
import traceback


C_RED = Fore.RED
C_CLEAR = Style.RESET_ALL


class LevelData(TypedDict):
    frame: tk.LabelFrame
    maps: List[tk.Button]


def get_curr_screen_size() -> Tuple[int, int]:
    """
    Workaround to get the size of the current screen in a multi-screen setup.

    Returns:
        int: width
        int: height
    """
    root = tk.Tk()
    root.update_idletasks()
    root.attributes('-fullscreen', True)
    root.state('iconic')
    geometry = root.winfo_geometry()
    root.destroy()

    x_index = geometry.find("x")
    plus_index = geometry.find("+")
    return int(geometry[:x_index]), int(geometry[x_index + 1:plus_index])


class Application(tk.Tk):
    def __init__(self, levels: List[Level]) -> None:
        try:
            self.screen_x, self.screen_y = get_curr_screen_size()
            tk.Tk.__init__(self, className="Fly-In")
            self.configure(
                width=int(self.screen_x * 0.8),
                height=int(self.screen_y * 0.8),
                padx=2, pady=2
            )
        except Exception as err:
            raise Exception(f"{C_RED}Initializing tkinter: {err}"
                            f"{C_CLEAR}\n\n{traceback.format_exc()}")

        self.current_map: tk.Frame | None = None
        self.get_levels_grid(levels)
        self.menu_widget()
        self.home_loader()
        self.grid()

    def clear_grid(self) -> None:
        grids = self.grid_slaves(row=1)
        for grid in grids:
            grid.grid_forget()

    def map_put(self, map: Map) -> None:
        def color_check(root: tk.Tk, color: str) -> bool:
            try:
                self.winfo_rgb(color)
                return True
            except tk.TclError:
                return False

        def put_hub(canvas: tk.Canvas, color: str, letter: str,
                    x: int, y: int, name: str) -> None:
            canvas.create_oval(x + 40, y + 20, x + 120, y + 60,
                               fill=color, outline="black", width=2)
            canvas.create_text(x + 80, y + 40, text=name, fill=letter,
                               font=("Arial", 10))

        try:
            self.clear_grid()
            """ full_grid = tk.LabelFrame(self, text=map.name, labelanchor="nw",
                                      padx=6, pady=6) """
            map_root = tk.LabelFrame(self, text=map.name, labelanchor="nw",
                                     font=("Arial", 10))
            hub_tk = tk.Canvas(map_root,
                               width=map.grid_size.x * 160,
                               height=map.grid_size.y * 80)
            for hub in [*map.hubs, map.start_hub, map.end_hub]:
                letter = "black"
                color = hub.color
                if color == "black":
                    letter = "white"
                if not color_check(self, color):
                    color = "white"
                put_hub(hub_tk, color, letter,
                        hub.x * 160, hub.y * 80, hub.name)
            hub_tk.grid()
            map_root.grid(row=1, column=0, padx=4, pady=4, sticky="nw")
            self.update_idletasks()
            self.geometry("")
            

        except Exception as err:
            raise Exception(f"{C_RED}While putting map '{map.name}': {err}"
                            f"{C_CLEAR}\n\n{traceback.format_exc()}")

    def get_levels_grid(self, levels: List[Level]) -> None:
        """
        Saves the whole level grid for future use
        """
        try:
            self.levels: List[LevelData] = []
            for level in levels:
                new_lf = tk.LabelFrame(self, labelanchor="nw", text=level.name,
                                    padx=6, pady=6)
                maps_buttoms: List[tk.Button] = []
                for map in level.maps:
                    maps_buttoms.append(
                        tk.Button(new_lf, text=map.name, padx=6, pady=6,
                                command=partial(self.map_put, map)
                                )
                                )
                self.levels.append({
                    "frame": new_lf,
                    "maps": maps_buttoms
                })
        except Exception as err:
            raise Exception(f"{C_RED}Getting Levels frame and maps buttons: "
                            f"{err}{C_CLEAR}\n\n{traceback.format_exc()}")

    def home_loader(self) -> None:
        "Goes to the map choosing screen"
        try:
            if self.current_map:
                self.current_map.grid_forget()
                self.current_map.destroy()
                self.current_map == None
            self.clear_grid()
            for i, each in enumerate(self.levels):
                each["frame"].grid(row=1, column=i)
                for j, buttom in enumerate(each["maps"]):
                    buttom.grid(column=0, row=j)

        except Exception as err:
            raise Exception(f"{C_RED}Loading map: {err}"
                            f"{C_CLEAR}\n\n{traceback.format_exc()}")

    def menu_widget(self) -> None:
        def quit_widget(self) -> None:
            self.menu.quit_button = tk.Button(self.menu, text="Quit",
                                              padx=6, pady=6,
                                              font=("Arial", 10),
                                              command=self.quit)
            self.menu.quit_button.grid(row=0, column=1)

        def home_widget(self) -> None:
            self.menu.home_buttom = tk.Button(self.menu, text="Home",
                                              padx=6, pady=6,
                                              font=("Arial", 10),
                                              command=self.home_loader)
            self.menu.home_buttom.grid(row=0, column=0)

        try:
            self.menu = tk.LabelFrame(self, labelanchor="nw", text="Menu",
                                      padx=6, pady=6, font=("Arial", 10))
            quit_widget(self)
            home_widget(self)
            self.menu.grid(row=0, column=0, sticky="NW")

        except Exception as err:
            raise Exception(f"{C_RED}Creating menu: {err}"
                            f"{C_CLEAR}\n\n{traceback.format_exc()}")

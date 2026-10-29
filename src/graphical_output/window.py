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
        CELL_W, CELL_H = 160, 80

        def color_check(color: str) -> bool:
            try:
                self.winfo_rgb(color)
                return True
            except tk.TclError:
                return False

        def put_hub(canvas, color, letter, x, y, name):
            canvas.create_oval(x + 40, y + 20, x + 120, y + 60,
                            fill=color, outline="black", width=2)
            canvas.create_text(x + 80, y + 40, text=name, fill=letter,
                            font=("Arial", 10))

        try:
            self.clear_grid()
            map_root = tk.LabelFrame(self, text=map.name, labelanchor="nw",
                                    font=("Arial", 10))
            full_w = map.grid_size.x * CELL_W
            full_h = map.grid_size.y * CELL_H
            # Cap the *visible* size to a portion of the screen
            max_w = int(self.winfo_screenwidth() * 0.9)
            max_h = int(self.winfo_screenheight() * 0.8)

            hub_canvas = tk.Canvas(map_root,
                                   width=min(full_w, max_w),
                                   height=min(full_h, max_h),
                                   highlightthickness=0)

            for hub in [*map.hubs, map.start_hub, map.end_hub]:
                letter = "white" if hub.color == "black" else "black"
                color = hub.color if color_check(hub.color) else "white"
                put_hub(hub_canvas, color, letter,
                        hub.x * CELL_W, hub.y * CELL_H, hub.name)

            scroll_y = tk.Scrollbar(map_root, orient=tk.VERTICAL,
                                    command=hub_canvas.yview)
            scroll_x = tk.Scrollbar(map_root, orient=tk.HORIZONTAL,
                                    command=hub_canvas.xview)
            hub_canvas.configure(xscrollcommand=scroll_x.set,
                                 yscrollcommand=scroll_y.set)
            hub_canvas.bind("<MouseWheel>",
                            lambda e: hub_canvas.yview_scroll(
                                -1 * (e.delta // 120), "units"))
            hub_canvas.bind("<Shift-MouseWheel>",
                            lambda e: hub_canvas.xview_scroll(
                                -1 * (e.delta // 120), "units"))
            x1, y1, x2, y2 = hub_canvas.bbox("all")
            hub_canvas.configure(scrollregion=(x1, y1, x2, y2))

            # Layout: canvas at (0,0), vertical bar at (0,1), horizontal bar at (1,0)
            hub_canvas.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)
            scroll_y.grid(row=0, column=1, sticky="ns")
            scroll_x.grid(row=1, column=0, sticky="ew")

            map_root.grid(row=1, column=0, padx=4, pady=4, sticky="nsew")

            self.update_idletasks()
            

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

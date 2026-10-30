import tkinter as tk
from typing import Tuple, List, TypedDict
from map_parser import Level, Map, Connection
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
        CELL_W, CELL_H, MARGIN = 160, 80, 40
        HUB_W, HUB_H = CELL_W // 2, CELL_H // 2

        def color_check(color: str) -> bool:
            try:
                self.winfo_rgb(color)
                return True
            except tk.TclError:
                return False

        def put_hub(canvas: tk.Canvas, color: str, letter: str,
                    x: int, y: int, name: str) -> None:
            """
            Places a hub on the canvas using x and y pixel coordinates.
            """
            x += CELL_W // 2
            y += CELL_H // 2
            canvas.create_oval(x, y, x + HUB_W, y + HUB_H,
                               fill=color, outline="black", width=2)
            canvas.create_text(x + HUB_W // 2, y + HUB_H // 2,
                               text=name, fill=letter, font=("Arial", 10))

        def put_conn(canvas: tk.Canvas, conn: Connection) -> None:
            """
            Places the conn inside the canvas using it's hubs to figure out
            the coordinates.
            """
            # Coordinates position for the width plus space
            x_left = HUB_W - 10  # Left of cicle
            x_middle = int(HUB_W * 1.5)  # Middle of circle width
            x_right = HUB_W * 2 + 10  # Right of circle

            # Coordinates position for the height plus space
            y_top = HUB_H - 10  # Top of circle
            y_middle = int(HUB_H * 1.5)  # Middle of circle height
            y_bottom = HUB_H * 2 + 10  # Bottom of circle

            hub1_x, hub1_y = conn.hubs[0].x, conn.hubs[0].y
            hub2_x, hub2_y = conn.hubs[1].x, conn.hubs[1].y

            x1 = hub1_x * CELL_W + MARGIN + x_right
            y1 = hub1_y * CELL_H + MARGIN + y_middle
            x2 = hub2_x * CELL_W + MARGIN + x_left
            y2 = hub2_y * CELL_H + MARGIN + y_middle

            if hub1_x == hub2_x:
                x1 = hub1_x * CELL_W + MARGIN + x_middle
                x2 = hub2_x * CELL_W + MARGIN + x_middle
                y1 = hub1_y * CELL_H + MARGIN + y_bottom
                y2 = hub2_y * CELL_H + MARGIN + y_top
                if hub1_y > hub2_y:
                    y1 = hub1_y * CELL_H + MARGIN + y_top
                    y2 = hub2_y * CELL_H + MARGIN + y_bottom
            elif hub1_x > hub2_x:
                x1 = hub1_x * CELL_W + MARGIN + x_left
                x2 = hub2_x * CELL_W + MARGIN + x_right

            canvas.create_line(x1, y1, x2, y2)

        try:
            self.clear_grid()
            map_root = tk.LabelFrame(self, text=map.name, labelanchor="nw",
                                     font=("Arial", 10))
            full_w = map.grid_size.x * CELL_W + MARGIN * 2
            full_h = map.grid_size.y * CELL_H + MARGIN * 2
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
                        hub.x * CELL_W + MARGIN, hub.y * CELL_H + MARGIN,
                        hub.name)

            for conn in map.connections:
                put_conn(hub_canvas, conn)

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

            # Canvas at (0,0), vertical bar at (0,1), horizontal bar at (1,0)
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
                self.current_map = None
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

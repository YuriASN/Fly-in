import tkinter as tk
from typing import Tuple, List, TypedDict
from map_parser import Level, Map, Connection, step_backwards, step_foward
from pathfinder import get_path, Path
from colorama import Fore, Style
from functools import partial
from time import sleep
import traceback


C_RED = Fore.RED
C_CLEAR = Style.RESET_ALL
FONT = "Arial"
FONT_SZ = 10


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
            self.title("Window")
        except Exception as err:
            raise Exception(f"{C_RED}Initializing tkinter: {err}"
                            f"{C_CLEAR}\n\n{traceback.format_exc()}")

        self.map_frame: tk.LabelFrame | None = None
        self.map: Map | None = None
        self.paths: List[Path] | None = None
        self.get_levels_grid(levels)
        self.menu_widget()
        self.control_widget()
        self.home_loader()
        self.grid()

    def clear_grid(self, row: int | None = None) -> None:
        grids = self.grid_slaves(row=row)
        for grid in grids:
            if grid.cget("text") != "Menu":
                grid.grid_forget()

    def move_foward(self) -> None:
        if not self.map or not self.paths:
            raise ValueError(f"{C_RED}No map or path available to move foward"
                             f"{C_CLEAR}\n\n{traceback.format_exc()}")
        self.map = step_foward(self.map, self.paths)
        if self.map.turn == 1:
            self.control_widget(backward=True)
        if self.map.total_drones == len(self.map.end_hub.drones_in):
            self.control_widget(foward=False, play=False)
        self.map_put(self.map)

    def move_backwards(self) -> None:
        if not self.map or not self.paths:
            raise ValueError(f"{C_RED}No map or path available to move"
                             f"backwards{C_CLEAR}\n\n{traceback.format_exc()}")
        if not self.map.turn:
            raise ValueError(f"{C_RED}No movement done to undo!"
                             f"{C_CLEAR}\n\n{traceback.format_exc()}")
        self.map = step_backwards(self.map, self.paths)
        if self.map.turn == 0:
            self.control_widget(backward=False)
        self.map_put(self.map)

    def play_pause(self) -> None:
        if not self.map:
            raise ValueError(f"{C_RED}No map available to play!"
                             f"{C_CLEAR}\n\n{traceback.format_exc()}")
        pass
        while len(self.map.end_hub.drones_in) is not self.map.total_drones:
            self.move_foward()
            sleep(0.5)

    def control_widget(self, foward: bool | None = None,
                       backward: bool | None = None,
                       play: bool | None = None) -> None:
        def foward_widget(activate: bool) -> None:
            if activate:
                self.foward_button.configure(state="normal")
            else:
                self.foward_button.configure(state="disabled")

        def backward_widget(activate: bool) -> None:
            if activate:
                self.backward_button.configure(state="normal")
            else:
                self.backward_button.configure(state="disabled")

        def play_pause_widget(activate: bool) -> None:
            if activate:
                self.play_button.configure(state="normal")
            else:
                self.play_button.configure(state="disabled")

        if not all([foward, backward, play]):
            self.control_frame = tk.LabelFrame(self, labelanchor="nw",
                                               text="Controls", padx=6, pady=6,
                                               font=(FONT, FONT_SZ),
                                               name="control")
            self.foward_button = tk.Button(
                self.control_frame, text=">>", padx=6, pady=6,
                font=(FONT, FONT_SZ), command=self.move_foward)
            self.foward_button.grid(row=0, column=2)

            self.backward_button = tk.Button(
                self.control_frame, text="<<", padx=6, pady=6,
                font=(FONT, FONT_SZ), state="disabled",
                command=self.move_backwards)
            self.backward_button.grid(row=0, column=0)

            self.play_button = tk.Button(
                self.control_frame, text="> / ||", padx=6, pady=6,
                font=(FONT, FONT_SZ),
                command=self.play_pause)
            self.play_button.grid(row=0, column=1)

        if isinstance(foward, bool):
            foward_widget(foward)
        if isinstance(backward, bool):
            backward_widget(backward)
        if isinstance(play, bool):
            play_pause_widget(play)

    def map_put(self, map: Map) -> None:
        CELL_W, CELL_H, MARGIN = 240, 120, 60
        HUB_RELATION = 1.7
        HUB_W, HUB_H = int(CELL_W // HUB_RELATION), int(CELL_H // HUB_RELATION)

        def color_check(color: str) -> bool:
            try:
                self.winfo_rgb(color)
                return True
            except tk.TclError:
                return False

        def put_hub(canvas: tk.Canvas, color: str, letter: str,
                    x: int, y: int, name: str, drones: int) -> None:
            """
            Places a hub on the canvas using x and y pixel coordinates.
            """
            x += HUB_W
            y += HUB_H
            canvas.create_oval(x, y, x + HUB_W, y + HUB_H, fill=color,
                               outline=color,
                               activefill="cyan", activeoutline="blue")
            canvas.create_text(
                x + HUB_W // 2, y + HUB_H // 2, state="disabled",
                text=name.capitalize() + "\nDrones: " + str(drones),
                justify="center", offset="center", fill=letter,
                font=(FONT, FONT_SZ))

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

            # Coordinates to move the drone count out of the line
            text_x, text_y = 0, -10
            justf = "center"

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
                text_x = 10
                justf = "left"
                text_y = 0
                if hub1_y > hub2_y:
                    y1 = hub1_y * CELL_H + MARGIN + y_top
                    y2 = hub2_y * CELL_H + MARGIN + y_bottom
            elif hub1_x > hub2_x:
                x1 = hub1_x * CELL_W + MARGIN + x_left
                x2 = hub2_x * CELL_W + MARGIN + x_right
            if hub1_y > hub2_y:
                text_x = -10
                justf = "right"
                text_y = 0
            elif hub1_y < hub2_y:
                text_x = 10
                justf = "left"
                text_y = 0

            tag = "_".join(conn.names)
            canvas.create_line(x1, y1, x2, y2, tags=tag,
                               smooth=True, width=2, activefill="red")
            canvas.create_text(text_x + x1 + (x2 - x1) // 2,
                               text_y + y1 + (y2 - y1) // 2, tags=tag,
                               font=(FONT, FONT_SZ), activefill="red",
                               text=str(len(conn.drones_in)), justify=justf)

            # Bind tags of line and text to change both colors when hovering
            canvas.tag_bind(tag, "<Enter>",
                            lambda e: canvas.itemconfig(tag, fill="red"))

            canvas.tag_bind(tag, "<Leave>",
                            lambda e: canvas.itemconfig(tag, fill="black"))

        try:
            if not self.map:
                self.map = map.model_copy(deep=True)
                self.paths = get_path(
                    self.map.start_hub, self.map.end_hub.name, [], [])

            self.clear_grid(row=1)
            if not self.map_frame:
                self.map_frame = tk.LabelFrame(
                    self, text=map.name, labelanchor="nw",
                    font=(FONT, FONT_SZ), name=map.name.lower())
            full_w = map.grid_size.x * CELL_W + MARGIN * 2
            full_h = map.grid_size.y * CELL_H + MARGIN * 2

            # Cap the *visible* size to a portion of the screen
            max_w = int(self.winfo_screenwidth() * 0.9)
            max_h = int(self.winfo_screenheight() * 0.8)

            hub_canvas = tk.Canvas(self.map_frame,
                                   width=min(full_w, max_w),
                                   height=min(full_h, max_h),
                                   highlightthickness=0)

            for conn in map.connections:
                put_conn(hub_canvas, conn)

            for hub in [*map.hubs, map.start_hub, map.end_hub]:
                letter = "white" if hub.color == "black" else "black"
                color = hub.color if color_check(hub.color) else "white"
                put_hub(hub_canvas, color, letter,
                        hub.x * CELL_W + MARGIN, hub.y * CELL_H + MARGIN,
                        hub.name, len(hub.drones_in))

            # Set scroll for big maps
            scroll_y = tk.Scrollbar(self.map_frame, orient=tk.VERTICAL,
                                    command=hub_canvas.yview)
            scroll_x = tk.Scrollbar(self.map_frame, orient=tk.HORIZONTAL,
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

            self.map_frame.grid(row=1, column=0, padx=4, pady=4, sticky="nsew")

            # Update the control frame if changed
            if not self.control_frame.winfo_ismapped():
                self.control_frame.grid(row=0, column=0, sticky="N")

            # Activate home button if not activated
            if self.home_button.cget("state") != "normal":
                self.home_button.configure(state="normal")

            self.update_idletasks()

        except Exception as err:
            print(f"{C_RED}While putting map '{map.name}': {err}"
                  f"{C_CLEAR}\n\n{traceback.format_exc()}")
            self.home_loader()

    def get_levels_grid(self, levels: List[Level]) -> None:
        """
        Saves the whole level grid for future use
        """
        try:
            self.levels: List[LevelData] = []
            for level in levels:
                new_lf = tk.LabelFrame(self, labelanchor="nw", text=level.name,
                                       padx=6, pady=6, name=level.name.lower())
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
            if self.map_frame:
                self.home_button.configure(state="disabled")

                self.map_frame.destroy()
                self.map_frame = None

                self.map = None
                self.paths = None

                self.control_widget(foward=True, backward=False, play=True)
                self.control_frame.grid_forget()

                self.clear_grid()
            for i, each in enumerate(self.levels):
                for j, buttom in enumerate(each["maps"]):
                    buttom.grid(column=0, row=j)
                each["frame"].grid(row=1, column=i)

        except Exception as err:
            raise Exception(f"{C_RED}Loading map: {err}"
                            f"{C_CLEAR}\n\n{traceback.format_exc()}")

    def menu_widget(self) -> None:
        def quit_widget(self) -> None:
            quit_button = tk.Button(
                self.menu_frame, text="Quit", padx=6, pady=6,
                font=(FONT, FONT_SZ), command=self.quit)
            quit_button.grid(row=0, column=1)

        def home_widget(self) -> tk.Button:
            home_button = tk.Button(
                self.menu_frame, text="Home", padx=6, pady=6,
                font=(FONT, FONT_SZ), command=self.home_loader,
                state="disabled")
            home_button.grid(row=0, column=0)

            return home_button

        try:
            self.menu_frame = tk.LabelFrame(
                self, labelanchor="nw", text="Menu", padx=6, pady=6,
                font=(FONT, FONT_SZ), name="menu")
            quit_widget(self)
            self.home_button = home_widget(self)
            self.menu_frame.grid(row=0, column=0, sticky="NW")

        except Exception as err:
            raise Exception(f"{C_RED}Creating menu: {err}"
                            f"{C_CLEAR}\n\n{traceback.format_exc()}")

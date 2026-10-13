#!.venv/bin pyhton3.10
from .window import Application
from ..map_parser import get_maps

if __name__ == "__main__":
    try:
        app = Application(get_maps("maps"))
        
        app.mainloop()

    except Exception as err:
        print(err)

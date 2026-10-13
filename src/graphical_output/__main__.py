#!.venv/bin pyhton3.10
from .window import Application

if __name__ == "__main__":
    try:
        from ..map_parser import get_maps
        app = Application(get_maps("maps"))
        
        app.mainloop()

    except Exception as err:
        print(err)

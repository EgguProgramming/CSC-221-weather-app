# NAME: Melody
# Program Status: Commenting
# Description:
"""
This program will initiate a crash handler and then initiate the UI handler. This is
where you will run the program.
"""

import ui_backend
import weather_microservice
import ui_handler
import sys
import os

# Pass the sequence of events onto PyQT5 and ui_handler.py
def main():
    ui_handler.init_app()


# multipleinterfaces (07/06/2011) https://stackoverflow.com/a/6598286
# extremely useful in handling errors
def crash_handler(exctype, value, traceback):
    # If the error is specifically called by the user to end the program, end without
    # stalling or handling the error
    if exctype is SystemExit or exctype is KeyboardInterrupt:
        sys.exit(0)

    # print the error instead of crashing
    traceback.print_exception(exctype, value, traceback)

# If the file is being run as the main application and not being imported, setup the
# crash handler and start the GUI
if __name__ == '__main__':
    sys.excepthook = crash_handler
    main()

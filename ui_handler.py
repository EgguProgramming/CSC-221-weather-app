# NAME: Melody
# Program Status: Commenting
# Description:
"""
This program acts as the front-facing interface where the user interacts with data
and submits requests to be handled by the backend and then the microservice. The
user may enter a location or zipcode, click an entry from the dropdown or press submit,
then continue
"""

# The process of adding comments is going to be long and rigorous
import datetime
import math
import random
import sys
import time
from typing import Any

import ui_backend
from PyQt5.QtCore import Qt, QTimer, QStringListModel, QEvent
from PyQt5.QtGui import QFont, QPixmap, QIcon
from PyQt5.QtWidgets import QApplication, QLabel, QPushButton, QWidget, QHBoxLayout, QVBoxLayout, QBoxLayout, QFrame, \
    QSizePolicy, QScrollArea, QSpacerItem, QLineEdit, QDialog, QCompleter
from dataclasses import dataclass

# Properly formatted data that can be used by the frontend with minimal processing
@dataclass
class PanelCondition:
    cur_temp : float# current temperature in F
    high_temp : float # high temp of the day in F
    low_temp : float # low temp of the day in F
    wind_speed : float # wind speed of the day in MPH
    wind_dir : str # wind direction of the day, formatted to str
    will_rain : bool # will it rain liquid water
    amount_precip : float # How much precipitation
    cur_condition : str # cur conditions label
    cur_condition_desc : str # Current conditions blurb
    cur_condition_id : str # current condition id for icon
    humidity : int # humidity in percent
    date:str # Date of the record in UTC
    feels_like : float # What temp it feels liek outside in F
    air_pressure : float # Air pressure currently in HPA
    visibility : Any # visibility in meters
    sunset : int # time of sunset, unix epoch
    sunrise : int # time of sunrise, unix epoch
    weather_time : int # Time the current conditions were last updated
    time_zone : int # time zone of the location in seconds offset from UTC

# The QT Company ltd (2026) https://doc.qt.io/archives/qtforpython-5/
# Useful for grasping the core basics of the framework


# John Lim (12/03/2019) https://www.pythonguis.com/tutorials/qscrollarea/
# Referenced so that I may implement scrolling to the widget
# The scrollable area with the forecast panels
class PanelScrollZone(QScrollArea):
    def __init__(self):
        super().__init__()

        self.content = PanelContainer() # The content zone with panels

        self.setWidgetResizable(True)

        self.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }

            QScrollBar::handle:vertical {
                color: #C5C5D5;
                background:transparent;
                border-radius: 25px;
                min-width: 20px;
            }

            QScrollBar::add-page:vertical,
            QScrollBar::sub-page:vertical {
                background: #ABABBB;
            }

            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                width: 0px;
            }
            """)

        self.setWidget(self.content)

# The container, within the scrollzone, containing each forecast panel
class PanelContainer(QWidget):
    def __init__(self):
        super().__init__()

        self.panel_list = [] # List of panels
        self.layout = QVBoxLayout() # Layout of each panel

        self.layout.setSpacing(45)
        self.layout.setContentsMargins(50, 65, 65, 35)

        self.setLayout(self.layout)

    # Add new panels with updated information
    def update_panels(self, conditions=list[PanelCondition]):
        cond_list = [] # List of each condition passed by ui_backend
        for day_index in range(7):
            condition = conditions[day_index] # The condition for day of index, date of condition = current day + (index + 1)
            cond_list.append(condition)

        for panel in self.panel_list:
            self.layout.removeWidget(panel) # If there are already panels, remove and delete them.
            panel.deleteLater() # Let the garbage collector handle it

        self.panel_list = [] # Reset list of panels back to nothing once they've been managed. Garbage collector should handle it from here
        for index in range(7):
            panel = Panel(cond_list[index]) # A Single panel built from a day's condition
            self.layout.addWidget(panel)
            self.panel_list.append(panel)
            # panel.setFixedWidth(300)

# A forecast panel containing weather information, generic template
class Panel(QFrame):
    def __init__(self, conditions: PanelCondition):
        super().__init__()

        self.content = QHBoxLayout() # the content layout in the panel
        self.sub_frame = QFrame() # The frame background of the panel
        self.sub_frame_layout = QVBoxLayout() # The layout of the 4 forecast card
        self.emoji_label = ui_backend.get_image_from_preload_icon(conditions.cur_condition_id) # Image displaying the current condition icon
        self.weather_desc = QLabel() # Description of the weather
        self.date_label = QLabel() # Label containing the date of the forecast

        self.infos_group_vertical = QVBoxLayout() # the group of smaller forecast cards, vertically stacked
        self.infos_group_horizontal1 = QHBoxLayout() # The group of top horizontal cards
        self.infos_group_horizontal2 = QHBoxLayout() # The group of bottom horizontal cards

        self.temperature_label = QLabel() # The big label showing the temperature for the forecast

        self.info_high_temp_frame = HighLowInfoFrame(True, conditions.high_temp) # Frame showing the high temp of the day
        self.info_low_temp_frame = HighLowInfoFrame(False, conditions.low_temp) # frame showing the low temp of the day
        self.info_amount_precip_frame = AmountPrecipInfoFrame(conditions.amount_precip, conditions.will_rain) # Frame showing the expected precipitation amount for the day

        self.info_wind_frame = WindInfoFrame(conditions.wind_speed, conditions.wind_dir) # frame showing the wind speed and direction for the dat
        self.info_humidity_Frame = HumidityInfoFrame(conditions.humidity) # frame showing forecast humidity in percent

        self.infos_group = QFrame() # Group of every information

        self.temp_sub_layout = QVBoxLayout() # layout with the date and temperature

        self.setStyleSheet("""
        border-radius: 10px;
        background-color: qlineargradient(
            x1:1.0, y1:1.0,
            x2:0.0, y2:0.0,
            stop:0 #C6C6D6,
            stop:1 #F0F0FF
        );
        border-width: 0;
            """)


        self.info_amount_precip_frame.setStyleSheet(self.styleSheet())

        self.content.setSpacing(0)

        self.sub_frame.setStyleSheet("""
        border-radius: 10px;
        background-color: #D0D0E0;
        border-width: 0;
    """)

        self.sub_frame.setFixedWidth(110)

        self.sub_frame.setLayout(self.sub_frame_layout)
        self.sub_frame_layout.setContentsMargins(5, 5, 5, 5)

        self.emoji_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.emoji_label.setToolTip(conditions.cur_condition)

        self.weather_desc.setText(conditions.cur_condition_desc)
        self.weather_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.weather_desc.setStyleSheet("color: #4F4F60; background: #ACACCE; font-size:18px")
        self.weather_desc.setWordWrap(True)

        self.date_label.setText(conditions.date)
        self.date_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.date_label.setStyleSheet("color: #606080; background: transparent; padding-top: 0px; margin-top: 0px;")

        self.temperature_label.setText(f"{conditions.cur_temp:.0f}°F")
        self.temperature_label.setFont(QFont("Arial", 35))
        self.temperature_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.temperature_label.setStyleSheet(
            "color: #353545; padding: 25px; background: #E0E0EF; margin-top: 0px; font-weight: bold;")
        self.temperature_label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        self.temperature_label.setFixedWidth(250)

        self.infos_group.setStyleSheet("""
        border-radius: 10px;
        background-color: qlineargradient(
            x1:1.0, y1:1.0,
            x2:0.0, y2:0.0,
            stop:0 #A6A6B6,
            stop:1 #B5B5D4
        );
        border-width: 0;
        """)
        self.infos_group.setFixedHeight(200)

        self.infos_group_horizontal1.addWidget(self.info_high_temp_frame)
        self.infos_group_horizontal1.addWidget(self.info_low_temp_frame)
        self.infos_group_horizontal1.addWidget(self.info_amount_precip_frame)

        self.info_wind_frame.setStyleSheet(self.styleSheet())
        self.info_humidity_Frame.setStyleSheet(self.styleSheet())

        self.infos_group_horizontal2.addWidget(self.info_wind_frame)
        self.infos_group_horizontal2.addWidget(self.info_humidity_Frame)

        self.infos_group_vertical.addLayout(self.infos_group_horizontal1)
        self.infos_group_vertical.addLayout(self.infos_group_horizontal2)
        self.infos_group.setLayout(self.infos_group_vertical)

        self.sub_frame.setLayout(self.sub_frame_layout)
        # self.sub_frame_layout.addSpacing(75)
        self.sub_frame_layout.addWidget(self.emoji_label)
        self.sub_frame_layout.addWidget(self.weather_desc)
        # self.sub_frame_layout.addSpacing(75)

        self.content.addWidget(self.sub_frame)

        self.content.addLayout(self.temp_sub_layout)

        self.temp_sub_layout.setContentsMargins(15, 15, 15, 15)
        self.temp_sub_layout.addWidget(self.date_label)
        self.temp_sub_layout.addWidget(self.temperature_label)
        # self.content.addWidget(self.forecast_label)
        self.content.addWidget(self.infos_group)

        self.setLayout(self.content)


# The core weather app displaying the side bar and the scroll area of panels
class WeatherApp(QWidget):
    # Geeks4Geeks (3/26/2020) https://www.geeksforgeeks.org/python/pyqt5-how-to-change-font-and-size-of-label-text/
    # Font usage and label stylization
    # The QT Company (9/10/2026) https://doc.qt.io/qt-6/stylesheet-reference.html
    # The QT Company (9/10/2026) https://doc.qt.io/qt-6/stylesheet-examples.html
    # For finding styling resources not stated on the page above
    def __init__(self):
        super().__init__()
        self.resize(1300, 850)
        self.setStyleSheet("""
        background-color: qlineargradient(
            x1:0.2, y1:0.4,
            x2:0.8, y2:1,
            stop:0 #FAFAFA,
            stop:0.45 #F0F0FF,
            stop:1 #EBEBFB
            );
                """)


        self.general_layout = QHBoxLayout() # The layout of everything on the screen
        self.panels = PanelScrollZone() # panels containing the forecast objects
        self.side_bar = WeatherSideBar(self.panels.content) # The sidebar with the current conditions and search bar

        self.general_layout.setContentsMargins(0, 0, 0, 0)

        self.general_layout.addWidget(self.side_bar)
        self.general_layout.addWidget(self.panels)

        self.setLayout(self.general_layout)

# The sidebar object containing the search and current conditions
class WeatherSideBar(QFrame):
    def __init__(self, panels: PanelContainer):
        super().__init__()

        self.content = QVBoxLayout() # The content of everything in the side bar
        self.search_group = AutoFillingTextLine(panels, self) # The group with the search bar, question mark, and enter button
        self.search_huh = QPushButton() # The help button next to the search bar
        self.pixmap_huh = QPixmap() # Since the load from preload method passes a label, I need to intialize the button
        self.search_enter = QPushButton() # The enter button next to the help button and search bar
        self.pixmap_enter = QPixmap() # once more, the button does not work with load from preload in ui_backend.
        self.infos = SidebarInfo() # The info on the sidebar, with current conditions and time for the location selected

        self.content.setSpacing(50)

        self.setFixedWidth(375)
        self.setStyleSheet("""background-color: qlineargradient(
        x1:0, y1:0, x2:1, y2:1,
        stop:0 #CACAEA,
        stop:1 #BABACA); 
        border-width:0;""")

        self.search_huh.setToolTip("Help.")
        self.pixmap_huh.loadFromData(ui_backend.icon_preload_map["huh"])
        self.search_huh.setIcon(QIcon(self.pixmap_huh))

        self.search_enter.setToolTip("Enter.")
        self.pixmap_enter.loadFromData(ui_backend.icon_preload_map["enter"])
        self.search_enter.setIcon(QIcon(self.pixmap_enter))

        # When you press [  -> ], search
        self.search_enter.clicked.connect(self.search_group.on_enter_button_pressed)
        # When you press the (?) Button, show the help
        self.search_huh.clicked.connect(lambda: ui_backend.show_alert_box(self,"Enter the name of a city, or a zip code into the search box, A dropdown menu will appear if applicable. Press the enter button to view the weather for the selected location."))
        self.search_group.add(self.search_huh)
        self.search_group.add(self.search_enter)

        self.content.addWidget(self.search_group)
        self.content.addWidget(self.infos)

        self.setLayout(self.content)
# When entering a location, autofill with geocode data from OpenWeatherMap's API
class AutoFillingTextLine(QFrame):
    def __init__(self, panel_parent : PanelContainer, sidebar_parent : WeatherSideBar):
        super().__init__()
        self.panel_parent = panel_parent # The forecast panels
        self.sidebar_parent = sidebar_parent # The sidebar
        self.update_timer : QTimer = QTimer(self) # A timer to loop, check if user as not entered anything
        self.init_timer()

        self.saved_lat_long = [] # The last selected lat_long by the user
        self.current_lat_long_list = [] # The list of lat long entires
        self.current_locations_list = [] # the list of location entries

        self.setMaximumHeight(75)

        self.autofill_tracker = ui_backend.AutofillTracker() # Check if its time to send the autofill request or not
        self.autofill_list = QStringListModel([]) # the list to autofill with
        self.autofill = QCompleter(self.autofill_list) # The autofill dropdown menu
        self.search_bar = QLineEdit() # The search bar the user enters a location/zip into

        self.setStyleSheet("""
                border-radius: 10px;
                background-color: #D0D0E0;
                border-width: 0;""")
        self.content = QHBoxLayout() # The layout of each element, stacked horizontally
        self.setLayout(self.content)
        # self.setFixedHeight(75)

        self.search_bar.setPlaceholderText("Enter a city name, or zip code.")
        self.search_bar.setStyleSheet("""
                background-color: #E7E7F0""")
        self.search_bar.setToolTip("Enter a city name, or zip code.")
        self.search_bar.textEdited.connect(self.keystroke_entered)
        self.search_bar.returnPressed.connect(self.on_enter_button_pressed)


        self.autofill.setCompletionMode(QCompleter.CompletionMode.UnfilteredPopupCompletion)
        self.search_bar.setCompleter(self.autofill)
        self.autofill.activated.connect(self.register_new_lat_long_selection)

        self.add(self.search_bar)

    # the djokatu (07/22/2019) https://www.reddit.com/r/learnpython/comments/cglpkt/an_update_loop_in_a_gui_pyqt5/
    # assistance in adding an update loop to an object
    def init_timer(self):
        # I had initially done 1000 since that's the threshold, but if
        # you're not going to hold and the time since your last entered a key was 750ms ago,
        # then the timer updates, you'll really have to wait 1.750 seconds until the autofill
        # occurs
        self.update_timer.setInterval(50)
        self.update_timer.setSingleShot(False)
        self.update_timer.timeout.connect(self.check_if_autofill)
        self.update_timer.start()

    # Paul Colby (05/29/2023) https://forum.qt.io/topic/145440/how-do-i-update-a-qcompleter-with-a-new-strings-list/2
    # A bit of help on dynamic elements in a completer
    # Autofills when the user stops typing
    def add_new_autofill(self):
        results = ui_backend.get_list_of_locations_from_name(self.search_bar.text()) # Results as returned by the API for geocode suggestions

        list_of_location_names = [] # String representations of location names
        for location_whole in results:
            # handle in event of mismatch
            list_of_location_names.append(location_whole[0])
        self.autofill_list.setStringList(list_of_location_names)
        self.autofill.complete()

        self.current_lat_long_list = results
        self.current_locations_list = list_of_location_names

    # When you select an autofill, remember its lat/long
    def register_new_lat_long_selection(self):
        index_of_selection = self.current_locations_list.index(self.search_bar.text()) # which number entry the user selected, 0-4
        self.saved_lat_long = [self.current_lat_long_list[index_of_selection][1], self.current_lat_long_list[index_of_selection][2]]

    # When you press a key, restart the tracker and associated values
    def keystroke_entered(self):
        self.saved_lat_long = []
        self.current_lat_long_list = []
        self.current_locations_list = []
        self.autofill_list.setStringList([])
        self.autofill_tracker.text_edit()

    # If should autofill, then do
    def check_if_autofill(self):
        if self.autofill_tracker.is_autofilled: return
        if self.autofill_tracker.check_time():
            self.add_new_autofill()
        else:
            pass

    # When the user pressed the enter button, wether it be via UI or via keyboard,
    # update visuals
    def on_enter_button_pressed(self):
        use_lat_long = []
        # If no saved lat/long
        if not self.saved_lat_long:
            list_of_locations = ui_backend.get_list_of_locations_from_name(self.search_bar.text()) # list of locations suggested by the API
            # If yes locations
            if list_of_locations:
                use_location = list_of_locations[0] # location to use
                if type(list_of_locations) is list:
                    use_lat_long = [use_location[1], use_location[2]]
                else:
                    # Zip codes return a single element
                    use_lat_long = [use_location["lat"], use_location["lon"]]
            else:
                ui_backend.show_alert_box(self, "Your search returned no results. Please try again.")
                return
        else:
            use_lat_long = self.saved_lat_long

        self.update_panels_with_weather_data(use_lat_long)
        self.sidebar_parent.infos.update_infos(use_lat_long)
        # ui_backend.update_panels(self.panel_parent)

    # Get the weather for a location specifically
    def get_weather_for_location(self, coordinates : list[float]):
        return ui_backend.get_weather_conditions_by_coordinates(coordinates[0], coordinates[1])

    # Update the info panels with new info
    def update_panels_with_weather_data(self, location : list[float]):
        weather = self.get_weather_for_location(location)
        ui_backend.update_panels(self.panel_parent, weather)

    # add a widget to the layout
    def add(self, widget_to_add : QWidget):
        self.content.addWidget(widget_to_add)

# The left bar with information on it
class SidebarInfo(QFrame):
    def __init__(self):
        super().__init__()
        self.setLayout(QVBoxLayout())

        self.setStyleSheet("""
        border-radius: 10px;
        background-color: #D0D0E0;
        border-width: 0;
        """)

        self.info_text_style_sheet = """
        color: #353545; 
        background: transparent;
        """

        self.top_label = QLabel() # Top label merely stating current conditions at top of bar
        self.city_name_label = QLabel() # Text stating the city name
        self.date_label = QLabel() # Label showing the date and time of the location selected

        self.wind_temp_group = QHBoxLayout() # Group containing the wind and temp data
        self.high_low_humidity_group = QHBoxLayout() # Group containing the daily high low, and current humidity
        self.pressure_visibility_group = QHBoxLayout() # Group containing the current air pressure and visibility
        self.sunriseset_group = QHBoxLayout() # group containing the sun rise and set times

        self.temp_frame = CurrentTempFrame() # Frame contining current temp info
        self.wind_frame = CurrentWindFrame() # Frame containing current wind info
        self.precip_frame = CurrentPrecipFrame() # Frame containing current precipitation info

        self.high_frame = HighLowInfoFrame(True, math.nan) # Frame containing daily high
        self.low_frame = HighLowInfoFrame(False, math.nan) # Frame containing daily low
        self.humidity_frame = HumidityInfoFrame(math.nan, False) # Frame containing current humidity

        self.pressure_frame = CurrentAirPressureFrame() # Frame containing current air pressure
        self.visibility_frame = CurrentVisibilityFrame() # Frame containing current visibility

        self.sunrise_frame = SunsetOrRiseInfoFrame(False) # Frame containing daily sunrise time
        self.sunset_frame = SunsetOrRiseInfoFrame(True) # Frame containing daily sunset time

        self.top_label.setStyleSheet("background: #C5C5D3; color: #353545; font-weight: bold; font-size:28px;")
        self.top_label.setText(" Current Conditions")
        self.add(self.top_label)

        self.layout().setSpacing(5)

        self.city_name_label.setStyleSheet(self.info_text_style_sheet + "font-weight: bold; font-size: 22px;")
        self.city_name_label.setWordWrap(True)

        self.date_label.setStyleSheet(self.info_text_style_sheet)

        self.wind_temp_group.addWidget(self.temp_frame)
        self.wind_temp_group.addWidget(self.wind_frame)

        self.sunriseset_group.addWidget(self.sunrise_frame)
        self.sunriseset_group.addWidget(self.sunset_frame)

        self.pressure_visibility_group.addWidget(self.pressure_frame)
        self.pressure_visibility_group.addWidget(self.visibility_frame)

        self.high_low_humidity_group.addWidget(self.high_frame)
        self.high_low_humidity_group.addWidget(self.low_frame)
        self.high_low_humidity_group.addWidget(self.humidity_frame)

        self.add(self.city_name_label)
        self.add(self.date_label)
        self.add(self.precip_frame)
        self.layout().addLayout(self.wind_temp_group)
        self.layout().addLayout(self.high_low_humidity_group)
        self.layout().addLayout(self.pressure_visibility_group)
        self.layout().addLayout(self.sunriseset_group)

        # self.update_infos("Winchester, Virginia", PanelCondition.get_random_condition())

    def update_infos(self, lat_long : list[float]):
        cur_return = ui_backend.get_current_conditions(lat_long) # return of current conditions with extra data
        current_conditions = cur_return[0] # current conditions in pretty, readable format
        city_name = cur_return[1] # City name where conditions have occured
        time_of_data_collection = ui_backend.get_formatted_time_from_timestamp(current_conditions.weather_time+current_conditions.time_zone) # when data was collected
        now = ui_backend.get_formatted_time_from_timestamp(time.time()+current_conditions.time_zone) # Current time at city
        txt_of_time = f"{now[0].month}/{now[0].day}/{now[0].year}, Local time: {now[1]}:{now[0].minute:02.0f} {now[2]}\nData collected {ui_backend.format_str_based_on_delta_t(time.time() - current_conditions.weather_time)}" # local date, time, and when the data was collected.

        # If data was collected previously, state when
        if now[0].day != time_of_data_collection[0].day:
            txt_of_time += f"({time_of_data_collection[0].day}/{time_of_data_collection[1].day}/{time_of_data_collection[1].year})"

        # Update all the frames with new info
        self.city_name_label.setText(city_name)
        self.date_label.setText(txt_of_time)
        self.temp_frame.set_text(current_conditions.cur_temp, current_conditions.feels_like)
        self.wind_frame.update_infos(current_conditions.wind_speed, current_conditions.wind_dir)
        self.precip_frame.update_infos(current_conditions.will_rain, current_conditions.amount_precip, current_conditions.cur_condition_id, current_conditions.cur_condition)
        self.high_frame.update_infos(current_conditions.high_temp)
        self.low_frame.update_infos(current_conditions.low_temp)
        self.humidity_frame.update_infos(current_conditions.humidity)
        self.pressure_frame.update_infos(f"{current_conditions.air_pressure}hPa")
        self.visibility_frame.update_infos(current_conditions.visibility)
        # Pass a time-zone adjusted sunset/sunrise value
        self.sunrise_frame.update_infos(current_conditions.sunrise+current_conditions.time_zone)
        self.sunset_frame.update_infos(current_conditions.sunset+current_conditions.time_zone)

    # add element to layout
    def add(self, widget_to_add : QWidget):
        self.layout().addWidget(widget_to_add)

# Generic class that allows quick styling and easy adding
class GenericInfoFrame(QFrame):
    def __init__(self, use_hbox : bool = True):
        super().__init__()

        # Generic text stylesheet
        self.info_text_style_sheet = """
        color: #353545; 
        background: transparent;
        """

        self.setStyleSheet("""
        border-radius: 10px;
        background-color: qlineargradient(
            x1:1.0, y1:1.0,
            x2:0.0, y2:0.0,
            stop:0 #C6C6D6,
            stop:1 #F0F0FF
        );
        border-width: 0;""")

        # allow user to choose a horizontal or vertical layout
        if use_hbox:
            self.content = QHBoxLayout()
        else:
            self.content = QVBoxLayout()
        self.content.setContentsMargins(5,5,5,5)
        self.setLayout(self.content)

        self.content.setSpacing(2)
        self.content.setAlignment(Qt.AlignmentFlag.AlignCenter)

    # simple and quick adding elements to the group
    def add(self, widget):
        self.content.addWidget(widget)

# Info frame that can contain the time the sun will rise or set for a specific location.
class SunsetOrRiseInfoFrame(GenericInfoFrame):
    def __init__(self, sunset : bool):
        super().__init__()

        is_sunset_or_sunrise = "sunset" if sunset else "sunrise" # Text representation of sunset or sunrise
        self.image_label = ui_backend.get_image_from_preload_icon(is_sunset_or_sunrise,[65,65]) # Image graphic of the sunrise/set icon
        self.text_label = QLabel() # Text label of the time the sun will rise


        self.setToolTip("Time of "+is_sunset_or_sunrise)

        self.image_label.setStyleSheet(self.info_text_style_sheet)
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.text_label.setStyleSheet(self.info_text_style_sheet+"font-size:20px;")
        self.text_label.setWordWrap(True)
        self.text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.text_label.setText("N/A")

        self.add(self.image_label)
        self.add(self.text_label)

    # From a passed unix epoch timestamp, display a properly formatted time
    def update_infos(self, time : int):
        time_as_object = ui_backend.get_formatted_time_from_timestamp(time) # Unix epoch timestamp converted to a timedate object

        self.text_label.setText(f"{time_as_object[1]}:{time_as_object[0].minute:02.0f} {time_as_object[2]}")

# A frame containing the current visibility in m or km for an area
class CurrentVisibilityFrame(GenericInfoFrame):
    def __init__(self):
        super().__init__()

        self.setToolTip("Current visibility")

        self.image_label = ui_backend.get_image_from_preload_icon("visibility",[65,65]) # The image of the visibility icon
        self.text_label = QLabel() # The text label saying how far one can see

        self.image_label.setStyleSheet(self.info_text_style_sheet)
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.text_label.setStyleSheet(self.info_text_style_sheet+"font-size:22px;")
        self.text_label.setWordWrap(True)
        self.text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.text_label.setText("N/A")

        self.add(self.image_label)
        self.add(self.text_label)

    # From a passed value, format it to display the visibility
    def update_infos(self, visibility):
        self.text_label.setText(ui_backend.format_meters_to_km(visibility))

# A frame containing the current air pressure for an area
class CurrentAirPressureFrame(GenericInfoFrame):
    def __init__(self):
        super().__init__()

        self.setToolTip("Current air pressure")

        self.image_label = ui_backend.get_image_from_preload_icon("barometer",[45,45]) # Image showing the barometer / air pressure icon
        self.text_label = QLabel() # label showing the air pressure in hPa

        self.image_label.setStyleSheet(self.info_text_style_sheet)
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.text_label.setStyleSheet(self.info_text_style_sheet+"font-size:22px;")
        self.text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.text_label.setText("N/A")

        self.add(self.image_label)
        self.add(self.text_label)

    # Update the text label to show the air pressure
    def update_infos(self, pressure):
        self.text_label.setText(pressure)

# A frame containing current conditions and precipitation expections
class CurrentPrecipFrame(GenericInfoFrame):
    def __init__(self):
        super().__init__()

        self.layout_a = QHBoxLayout() # Layout containing the weather icon - exists so that when the icon is added and removed it stays on the right
        self.layout_b = QVBoxLayout() # Layout containing current conditions and short-term precipitation outlook

        self.temp_spacer = QSpacerItem(15,0) # Temporary spacing between the weather icon and the conditions, is not needed when a real icon is loaded

        self.cond_label = QLabel() # Label with the current conditions
        self.precip_label = QLabel() # Label with the expected precipitation

        self.precip_icon = None # Define as empty
        self.set_new_icon("huh")

        self.content.addLayout(self.layout_a)
        self.content.addSpacerItem(self.temp_spacer)
        self.content.addLayout(self.layout_b)

        self.cond_label.setStyleSheet(self.info_text_style_sheet+"font-size:22px; padding: 3px;")
        self.cond_label.setWordWrap(True)
        self.cond_label.setText("???")
        self.cond_label.setWordWrap(True)

        self.precip_label.setStyleSheet(self.info_text_style_sheet)
        # self.precip_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.precip_label.setStyleSheet("color: #606080; font-size: 17px; padding: 3px;")
        self.precip_label.setFixedWidth(200)
        self.precip_label.setText("N/A")
        self.precip_label.setWordWrap(True)

        self.layout_b.addWidget(self.cond_label)
        self.layout_b.addWidget(self.precip_label)

    # Change the weather icon to a new icon
    def set_new_icon(self, icon_id):
        # If the icon has been set, then remove it so it may be replaced
        if self.precip_icon is not None:
            self.layout_a.removeWidget(self.precip_icon)
        else:
            self.content.removeItem(self.temp_spacer)

        scale = 100 # scaling of the icon
        if icon_id == "huh":
            scale = 50 # If the icon is a question mark, make it bigger

        self.precip_icon = ui_backend.get_image_from_preload_icon(icon_id, [scale, scale])
        self.precip_icon.setStyleSheet(self.info_text_style_sheet)

        self.layout_a.addWidget(self.precip_icon)

        # self.precip_icon.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

    # Update the current conditions, icon, and short-term precipitation outlook
    def update_infos(self, is_rain : bool, precip_amount : float, icon_id : str, condition_desc : str):
        self.set_new_icon(icon_id)

        self.setToolTip("Current conditions and expected precipitation.")

        # If there's weather, display the percent, if theres no weather, display as none
        precip_dat = ui_backend.get_rain_or_snow_from_model(is_rain, precip_amount)
        if precip_dat[0]:
            weather_type = "rain" if is_rain else "snow" # To display "rain" or "snow" as a string
            self.precip_label.setText(f"There will be {ui_backend.format_mm_to_units(precip_amount)} of {weather_type} in the hour.")
        else:
            self.precip_label.setText("There is no precipitation within the hour.")

        self.cond_label.setText("Current Conditions: "+condition_desc)

# The frame containing humidity info for a location
class HumidityInfoFrame(GenericInfoFrame):
    # if math.nan is passed as humidity, then this instance of the frame is a current
    # conditions frame, that means it should be left-to-right and have different stylization
    def __init__(self, humidity : int, side_by_side : bool = True):
        super().__init__(side_by_side)

        self.setToolTip("Humidity")

        size = 50 # Size of the icon,
        if math.isnan(humidity):
            size = 60
        self.render_humidity_label = ui_backend.get_image_from_preload_icon("humidity",[size,size]) # Image label of the humidiity icon
        self.humidity_label_text = QLabel() # Text label of the  humidity icon
        txt = "" # Text to display on the label
        size_add = "" # font-size to add to the stylesheet - if this frame is a current condition then it should be slightly bigger

        self.render_humidity_label.setStyleSheet(self.info_text_style_sheet)

        if math.isnan(humidity):
            txt = "N/A"
        else:
            txt = f"{humidity:.0f}%"

        self.humidity_label_text.setText(txt)
        self.humidity_label_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if math.isnan(humidity):
            size_add = "font-size: 22px;"
        self.humidity_label_text.setStyleSheet(self.info_text_style_sheet + size_add)

        self.add(self.render_humidity_label)
        self.add(self.humidity_label_text)

    # Update the text label with new humidity info
    def update_infos(self, humidity:float):
        self.humidity_label_text.setText(f"{humidity:.0f}%")

# Frame containing current wind speed and direction
class WindInfoFrame(GenericInfoFrame):
    # Wind speed/direction for a forecast
    def __init__(self, wind_speed : int, wind_dir : str):
        super().__init__()

        self.setToolTip("Wind speed and direction.")

        self.render_wind_label = ui_backend.get_image_from_preload_icon("wind",[50,50]) # Image of the wind icon
        self.wind_label_text = QLabel() # Text of the wind speed/direction

        self.render_wind_label.setStyleSheet(self.info_text_style_sheet)
        self.render_wind_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.wind_label_text.setText(f"{wind_speed:.2f} mph going {wind_dir}")
        self.wind_label_text.setStyleSheet(self.info_text_style_sheet)
        self.wind_label_text.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.add(self.render_wind_label)
        self.add(self.wind_label_text)

# Info frame containing the amount of precipitation for a forecast
class AmountPrecipInfoFrame(GenericInfoFrame):
    def __init__(self, amount_precip : float, will_rain : bool):
        super().__init__(False)
        self.setToolTip("Chance of precipitation.")
        self.setMinimumHeight(100) # If not set, it will expand unnecessarily

        self.render_chance_precip_label = ui_backend.get_image_from_preload_icon("chancePrecip",[40,40]) # the image icon of the precipitation amount
        self.amount_precip_label = QLabel() # The label displaying the amount of precipitation in mm, inches, or feet
        precip_dat = ui_backend.get_rain_or_snow_from_model(will_rain, amount_precip) # The data of if it will rain or snow, and how much

        self.render_chance_precip_label.setStyleSheet(self.info_text_style_sheet)
        self.render_chance_precip_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # If it is going to precipitate, display so
        #Valle Nevado, Santiago Metropolitan Region, CL, is a good
        # region to test the snow vs rain display as it will snow this week of 9/17/2026
        if precip_dat[0]:
            precip_display = ui_backend.format_mm_to_units(amount_precip)
            self.amount_precip_label.setText(f"{precip_display} of {precip_dat[1]}fall")
        # Else, don't display "0 mm of snow expected", instead display no precipitation expected
        else:
            self.amount_precip_label.setText("No precipitation expected.")
        self.amount_precip_label.setStyleSheet(self.info_text_style_sheet + "font-size: 18px;")
        self.amount_precip_label.setWordWrap(True)
        self.amount_precip_label.setFixedWidth(150)
        self.amount_precip_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.add(self.render_chance_precip_label)
        self.add(self.amount_precip_label)
        self.setContentsMargins(3,3,3,3)

# Frame displaying the current wind speed and direction for a location. A new class
# because despite being about the same thing as the forecast wind info, this frame is
# formatted entirely differently
class CurrentWindFrame(GenericInfoFrame):
    def __init__(self):
        super().__init__()

        self.setToolTip("Current wind speed and direction.")

        self.wind_icon = ui_backend.get_image_from_preload_icon("wind",[50,50]) #
        self.wind_label_text = QLabel() # Label showing the speed of the wind
        self.wind_dir_text = QLabel() # Label showing the direction of the wind
        self.sub_vbox = QVBoxLayout() # Vertical Box with the text labels

        self.wind_icon.setStyleSheet("background: transparent;")

        self.wind_label_text.setText("N/A")
        self.wind_label_text.setStyleSheet(self.info_text_style_sheet + "font-size: 25px; font-weight: bold;")
        self.wind_label_text.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        self.wind_dir_text.setText("N/A")
        self.wind_dir_text.setStyleSheet("color: 3A3A4B;font-size: 14px")
        self.wind_dir_text.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        self.add(self.wind_icon)

        self.content.addLayout(self.sub_vbox)
        self.sub_vbox.addWidget(self.wind_label_text)
        self.sub_vbox.addWidget(self.wind_dir_text)

    # Update the windspeed and direction text labels with their proper info
    def update_infos(self, wind_speed : float, wind_dir : str):
        self.wind_label_text.setText(f"{wind_speed:.0f} mph")
        self.wind_dir_text.setText(f"blowing {wind_dir}")

# Frame showing the current temp, its own class for similar reasons to the current wind frame
class CurrentTempFrame(GenericInfoFrame):
    def __init__(self):
        super().__init__()
        self.setToolTip("Current temperature.")

        self.render_temp_img = ui_backend.get_image_from_preload_icon("tempNow",[65,65]) # Thermometer image icon
        self.render_temp_text = QLabel() # Label showing the current temp
        self.feelslike_temp_text = QLabel() # Label showing what it feels like outside rn
        self.sub_layout = QVBoxLayout() # Layout containing the above three items

        self.render_temp_img.setStyleSheet(self.info_text_style_sheet)
        self.render_temp_img.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        self.render_temp_text.setText("N/A")
        self.render_temp_text.setStyleSheet(self.info_text_style_sheet+"font-size: 25px; font-weight: bold;")
        self.render_temp_text.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        self.feelslike_temp_text.setText("N/A")
        self.feelslike_temp_text.setStyleSheet("color: 3A3A4B;font-size: 14px")
        self.feelslike_temp_text.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        self.add(self.render_temp_img)
        self.content.addSpacing(5)
        self.content.addLayout(self.sub_layout)
        self.sub_layout.addWidget(self.render_temp_text)
        self.sub_layout.addWidget(self.feelslike_temp_text)
        self.layout().setContentsMargins(3,3,3,3)

    # Update the text on all the elements with the proper data
    def set_text(self, temp : float, feelslike : float):
        self.render_temp_text.setText(f"{temp:.0f}°F")
        self.feelslike_temp_text.setText(f"feels like {temp:.0f}°F")

# Info frame containing the high or low for the day, can have NaN passed as the temp for the current conditions format, else present as forecast
class HighLowInfoFrame(GenericInfoFrame):
    def __init__(self, is_high : bool, temp : float):
        super().__init__(False)

        img_tag = "tempHigh"
        if not is_high:
            img_tag = "tempLow"
        size = 40
        if math.isnan(temp):
            size = 60
        txt = ""
        if math.isnan(temp):
            txt = "N/A"
        else:
            txt = f"{temp:.0f}°F"

        self.render_temp_label = ui_backend.get_image_from_preload_icon(img_tag, [size, size]) # Image of high or low thermometer
        self.temp_text_label = QLabel() # Label showing the temp

        self.setMaximumWidth(120)

        if is_high:
            self.setToolTip("High temperature for the day.")
        else:
            self.setToolTip("Low temperature for the day.")

        self.render_temp_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.render_temp_label.setStyleSheet(self.info_text_style_sheet)

        self.temp_text_label.setText(txt)
        self.temp_text_label.setStyleSheet(self.info_text_style_sheet+"font-size: 22px;")
        self.temp_text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.add(self.render_temp_label)
        self.add(self.temp_text_label)

    # Update the text with the proper info
    def update_infos(self, temp):
        self.temp_text_label.setText(f"{temp:.0f}°F")

weather_app : WeatherApp = None # Global weather app value
def init_app():
    global weather_app
    ui_backend.preload_weather_icons()
    app = QApplication(sys.argv) # Application
    weather_app = WeatherApp()  # The app
    weather_app.show()
    app.exec_()
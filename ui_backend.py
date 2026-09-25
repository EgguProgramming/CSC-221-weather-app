# NAME: Melody
# Program Status: Commenting
# Description:
"""
This program acts as a layer between the API returns, and the user facing interface.
program presents utilities like transforming api returns, converting units, representing
time, etc.
"""

import concurrent.futures
import datetime
import math
import os
from concurrent.futures.thread import ThreadPoolExecutor

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QLabel, QDialog, QVBoxLayout, QWidget, QFrame
import time

import ui_handler
import weather_microservice
import base64

# GET YOUR API KEY HERE >>> https://home.openweathermap.org/api_keys <<<
API_key = os.environ["API_KEY"] # The API key is the key that tells OpenWeatherMap my identity, and verifies the program is on my behalf
icon_preload_map : dict[str, bytes] = {} # Every icon image as loaded by the preloader, stored as raw bytes
week_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"] # For time formatting, days of the week

# When autofilling the locations a user can choose, it will only send a request after the
# user has stopped typing. An instance of this class manages the timekeeping and giving
# the "ok" to send a request
class AutofillTracker:
    def __init__(self):
        self.time_since_text_was_edited = -1 # since the text was last edited, in unix EPOCH
        self.is_autofilled = False # If the text is currently autofilled, will be used by other systems

    # Compare the time since last press to the current time, and check if against a threshold
    def check_time(self):
        # If, for this instance, text has not been edited yet, then set the first instance to now
        # and terminate the function.
        if self.time_since_text_was_edited == -1:
            self.time_since_text_was_edited = time.time()

        is_threshold = time.time()-self.time_since_text_was_edited > 1
        self.is_autofilled = is_threshold
        return is_threshold

    # When the text is edited by the user, this will reset the counter.
    def text_edit(self):
        self.is_autofilled = False
        self.time_since_text_was_edited = time.time()

# This function will, when being passed an icon ID, get an OpenWeatherMap condition
# icon.
def get_weather_icon(icon_id : str):
    icon_request = weather_microservice.IconRequestData(icon_id) # The parameters for the request of the icon
    icon_data = weather_microservice.send_api_request(weather_microservice.RequestType.WEATHER_ICON, icon_request, API_key) # The data returned by OpenWeatherMap's API
    return icon_data

# Soumit Salman Rahman (7/28/2025) https://towardsdev.com/whats-the-best-way-to-handle-concurrency-in-python-threadpoolexecutor-or-asyncio-85da1be58557
# The Python Software Foundation (9/16/2026) https://docs.python.org/3/library/concurrent.futures.html
# Extremely useful in taking this sequence from ~30 seconds to ~2 via concurrent processing
# This function will, upon starting the program, collect every bitmap graphic used by
# the program and store them for use. Since pulling from a server can take time, especially
# on a weaker connection, pulling it all at once will ultimately save time.
def preload_weather_icons():
    icon_registry = ["01", "02", "03", "04", "09", "10", "11", "13", "50"] # Each possible condition icon on OpenWeatherMap's API
    icon_gists = ["tempHigh", "tempLow", "chancePrecip", "wind", "humidity", "huh", "enter", "tempNow", "barometer", "sunrise", "sunset", "visibility"] # Each Icon I drew on my github Gist
    print("Preloading graphics...")
    preload_progress = 0 # How many files have been preloaded?
    preload_max = (len(icon_registry)*2) + len(icon_gists) # How many files will be preloaded? OpenWeatherMap has a night and day icon for each condition.

    futures = [] # When the program splits the process of getting the icons into
    # multiple sub-processes, instead of passing a value it will pass a promise saying
    # that there will be a value, but it doesn't have it right now. This promise's future
    # is saved, and when the future is made the data has arrived
    with ThreadPoolExecutor(max_workers=8) as executor:
        # For every icon on openweathermap's servers, request it's day and night
        # version
        for icon in icon_registry:
            futures.append(executor.submit(load_weather_icon, icon+"d"))
            futures.append(executor.submit(load_weather_icon, icon+"n"))

        # For every icon in my gist, request its data
        for gist_icon in icon_gists:
            futures.append(executor.submit(load_gist_icon, gist_icon))

        # For every kept promise, save the data sent by the API(s) to memory for
        # quicker calling
        for finished in concurrent.futures.as_completed(futures):
            # update the progress bar
            preload_progress = preload_increment(preload_progress, preload_max)
            icon_name = finished.result()[0] # The name of the icon that was loaded
            icon_data = finished.result()[1] # The data of the icon that was loaded

            # If the icon is a gist icon, then decode it from base64.
            if finished.result()[2]:
                # Save the gist icon to the preload map
                icon_preload_map[icon_name] = base64.b64decode(icon_data)
            else:
                # save the openweathermap icon to the preload map
                icon_preload_map[icon_name] = icon_data

    # Clear the progress bar from the terminal and print a complete statement
    clear_last_line()
    print("Preload complete!")

# Use weather_microservice to ask the OpenWeatherMap server for an icon
def load_weather_icon(icon_id : str):
    if icon_id[-1] != "d" and icon_id[-1] != "n":
        # If the icon id does not end in d(ay) or n(ight), improper data was passed.
        print("Passed illegal icon")
        exit(1)
    icon_infos = weather_microservice.IconRequestData(icon_id) # The params to tell weather_microservices when requesting data.
    icon_data = weather_microservice.send_api_request(weather_microservice.RequestType.WEATHER_ICON, icon_infos, API_key).content # The content sent back by the openweathermap servers
    return [icon_id, icon_data, False]

# Use weather_microservice to ask the github server for an icon
def load_gist_icon(icon_id : str):
    icon_infos = weather_microservice.IconRequestGistData(icon_id) # Params to tell weather-microservices what icon will be asked for
    icon_data = weather_microservice.send_api_request(weather_microservice.RequestType.WEATHER_ICON_GIST, icon_infos, API_key).content # the data returned by github
    return[icon_id, icon_data, True]

# Increase the loading bar by 1
def preload_increment(at : int, max : int):
    at += 1
    # Clear the old loading bar, so that it looks like its growing
    if at > 1:
        clear_last_line()
    pre_string = f"{(at/max*100):02.0f}% - " # The progress in percent
    print(" > " +pre_string + draw_bar(at, max) + " < ") # Print percent and bar
    return at

# The Wikimedia foundation (9/15/2026) https://en.wikipedia.org/wiki/ANSI_escape_code#Terminal_input_sequences
# Use ANSII escape codes to clear the last line in terminal
def clear_last_line():
    print("\r\x1b[1A\r\x1b[2K", end="", flush=True)


def draw_bar(at : int, max : int):
    ret = "[" # string to return
    # Defines the bar to be 35 "blocks" long
    for i in range(35):
        # Make the bar's color match the actual progress
        # N / A = N out of A
        if (at-1)/max >= i/35:
            ret += "▓"
        else:
            ret += "▒"
    ret += "]" # add a closing brace
    return ret

# From an ID and a scale (pixel,pixel), get a QLabel object with an attatched pixmap\
# Martin Fitzpatrick, John Lim (02/04/2020) https://www.pythonguis.com/faq/adding-images-to-pyqt5-applications/
def get_image_from_preload_icon(icon : str, scaled : list[int] = None):
    pix_map = QPixmap() # the pixel map with the icon
    pix_map.loadFromData(icon_preload_map[icon])
    # If a scale has been presented, scale the pixel map upwards
    if scaled is not None:
        pix_map = pix_map.scaled(scaled[0], scaled[1], Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
    return_label = QLabel() # The label to apply the pixel map onto
    return_label.setPixmap(pix_map)
    return return_label


# Martin Fitzpatrick, Leo Well (4/27/2026) https://www.pythonguis.com/tutorials/pyqt-dialogs/
# Show a window with a message, this is used when the user an inputted an incorrect value
def show_alert_box(at, show : str):
    infos_box = QDialog(at) # The info window that appears above the application
    infos_box.setWindowTitle("Alert!!! wwooo wooo wooo")

    infos = QLabel() # The label with text explaining why the alert appeared
    infos.setAlignment(Qt.AlignmentFlag.AlignCenter)
    infos.setText(show)
    infos.setWordWrap(True)
    infos.setFixedWidth(500)
    infos_box.setStyleSheet("""
    background-color: #FFFFFF;
    """)
    infos.setStyleSheet("""
                color: #000000;
                font-size: 25px;
                padding: 50px;""")
    infos_box.setLayout(QVBoxLayout())
    infos_box.layout().addWidget(infos)
    infos_box.exec()
    return infos_box

# From a name of a location, ask weather_microservice to pass a list of up to5 locations
# that openweathermap says match it. Very inaccurate but writing a custom geocoder is
# out of scope of this project.
def get_list_of_locations_from_name(location_name : str):
    # if you can turn the location into a number, it's most likely a zip code.
    try:
        location_zip = int(location_name) # Zip code, if succeeded
        request_data = weather_microservice.send_api_request(weather_microservice.RequestType.ZIP_GEO, weather_microservice.ZipGeolocationData(location_zip), API_key).json() # Get the data from openWeatherMap's server as to the location that pertains to the zip code entered
    except ValueError:
        request_data = weather_microservice.send_api_request(weather_microservice.RequestType.CITY_GEO, weather_microservice.CityGeolocationData(location_name), API_key).json() # Get a list of 5 or less locations that very closely match the user's input

    return_list = [] # The string representation of locations to return
    # If the data returned is a single item,
    if type(request_data) is not list:
        if "lat" in request_data.keys():
            return_list.append([request_data["name"], request_data["lat"], request_data["lon"]])
    else:
        try:
            for location in request_data:
                list_append_val = location["name"] + ", " # The actual display name to put in the list
                # If the location has a state, add that state to the display name
                if "state" in location.keys():
                    list_append_val += location["state"] + ", "
                list_append_val += location["country"]
                return_list.append([list_append_val, location["lat"], location["lon"]])
        except TypeError:
            # if an error arises (eg, empty request or minor error) then just return nothing
            return []
    if len(return_list) == 0:
        # If no errors arise, and the API says that there are no locations that meet with
        # your desire, then return nothing
        return []

    return return_list

# From coordinates, ask weather_microservice to get the next 7 days of weather,
# then return it as a list usable by the frontend
def get_weather_conditions_by_coordinates(lat : float, lon : float):
    api_data_forecast = weather_microservice.send_api_request(weather_microservice.RequestType.WEATHER_FORECAST_16D, weather_microservice.WeatherData(lat, lon), API_key).json() # The data sent by the server
    type_of_call = weather_microservice.RequestType.WEATHER_FORECAST_16D # The type of data being given, to convert to a frontend-usable format

    return convert_to_panelcondition_list(api_data_forecast, type_of_call)

# Ask weather_microservice to get the current conditions and return it in a fashion
# usable by the frontend.
def get_current_conditions(at : list[float]):
    data = weather_microservice.send_api_request(weather_microservice.RequestType.WEATHER_CURRENT, weather_microservice.WeatherData(at[0], at[1]), API_key).json() # The current conditions sent back by the server
    return_condition = get_panel_condition_from_stat(data, 0, False) # The pretty "readable" conditions as needed by the frontend
    return [return_condition, data["name"]+", "+data["sys"]["country"]]

# From a set of conditions, turn it into a list of frontend-usable data structures
def convert_to_panelcondition_list(list_of_conditions : list, type_of_call : weather_microservice.RequestType):
    condition_list = [] # The list to pass to the frontend

    day_offset = 0 # How many days the forecast is ahead of the current day
    # If the forecast is of the 16 day variety, do turn it into a list
    if type_of_call == weather_microservice.RequestType.WEATHER_FORECAST_16D:
        for day_stats in list_of_conditions["list"]:
            day_offset += 1

            this_condition = get_panel_condition_from_stat(day_stats, day_offset, True) # Get a single element of frontend-usable data
            condition_list.append(this_condition) # Add to list and continue

    return condition_list

# From raw data sent by the OpenWeatherMap API, process it into data that can be
# handled / used by frontend.
def get_panel_condition_from_stat(day_stats, day_offset : int, forecast : bool):
    now = datetime.datetime.now() + datetime.timedelta(day_offset) # The day of the weather being send

    # Since we assume imperial units, we'll assume the imperial way of formatting dates (MM/DD/YYYY)
    if forecast:
        will_rain = False # If it is going to percipitate LIQUID water
        precipitate_amount = 0 # If it will precipitate at all

        # Will_rain is slightly misleading in an entirely honest way - while it is
        # a conditional for if it will rain, it is set to false if it will snow. I
        # decided it's not worth it to make a value for will_rain, will_snow,
        # snow_amount, and rain_amount, instead there is will_rain and precipitate_amount
        #
        # If it will rain, it will rain. If it won't rain, if there's precipitation it will
        # snow, if theres no precipitation it will be clear.


        # If it will rain, then say it will rain and precipitate
        if 'rain' in day_stats.keys():
            will_rain = True
            precipitate_amount = day_stats["rain"]
        # If it will snow, then it won't rain but will precipitate
        elif 'snow' in day_stats.keys():
            precipitate_amount = day_stats["snow"]

        # Some values are left as dummy values, eg -1, because it will never be read
        # by the frontend in a forecast instance and does not exist in the API response
        # for 16d forecasts
        this_condition = ui_handler.PanelCondition(day_stats["temp"]["day"], day_stats["temp"]["max"],
                                                   day_stats["temp"]["min"], day_stats["speed"],
                                                   convert_degree_to_wind_direction(day_stats["deg"]),
                                                   will_rain, precipitate_amount, day_stats["weather"][0]["main"],
                                                   day_stats["weather"][0]["description"],
                                                   day_stats["weather"][0]["icon"], day_stats["humidity"],
                                                   f"{week_days[now.weekday()]}, {now.month}/{now.day}/{now.year}", -1, day_stats["pressure"],-1,-1,-1, -1, -1) # The condition in a front-end readable format
    else:
        will_rain = False # if it will rain
        precipitate_amount = 0 # if it will precipitate
        # Follows the same rules as the above will_rain - is copied because of the
        # different formatting in the two responses
        if "rain" in day_stats.keys():
            will_rain = True
            precipitate_amount = day_stats["rain"]["1h"]
        elif "snow" in day_stats.keys():
            precipitate_amount = day_stats["snow"]["1h"]
        # Depite the fact that I like snow more, rain takes priority because it is
        # more common (occuring in all 4 seasons) than snow (occuring in one, at most
        # two seasons)

        vis_val = 0 # the visibility value, response can hold a set or int.
        if type(day_stats["visibility"]) is set:
            vis_val = day_stats["visibility"][0]
        else:
            vis_val = day_stats["visibility"]

        this_condition = ui_handler.PanelCondition(day_stats["main"]["temp"], day_stats["main"]["temp_max"],
                                                   day_stats["main"]["temp_min"], day_stats["wind"]["speed"],
                                                   convert_degree_to_wind_direction(day_stats["wind"]["deg"]),
                                                   will_rain, precipitate_amount, day_stats["weather"][0]["main"],
                                                   day_stats["weather"][0]["description"],
                                                   day_stats["weather"][0]["icon"], day_stats["main"]["humidity"],
                                                   f"{week_days[now.weekday()]}, {now.month}/{now.day}/{now.year}", day_stats["main"]["feels_like"],
                                                   day_stats["main"]["pressure"],vis_val,day_stats["sys"]["sunset"],day_stats["sys"]["sunrise"], day_stats["dt"], day_stats["timezone"]) # the condition sent by the api, mangled and shaped into being frontend-readable

    return this_condition

# Based on how much time, in seconds, have passed since any event return a string
def format_str_based_on_delta_t(delta_t : float):
    div_val = 0 # how much to divide the end value of seconds by
    if delta_t < 60:
        return "A few moments ago"
    elif delta_t < 3600:
        div_val = 60
        unit = "minute"
    elif delta_t < 86400:
        div_val = 3600
        unit = "hour"
    else:
        return "A long time ago"

    time_count = math.floor(delta_t/div_val) # The amount of any unit
    plural_or_single = "s" # Eg, minute / minutes
    # if the value is a one, then don't have a trailing s.
    if time_count == 1:
        plural_or_single = ""

    return f"{time_count} {unit}{plural_or_single} ago"

# uni.edu (9/14/2026) https://uni.edu/storm/Wind%20Direction%20slide.pdf
# Logic and bounds for each notch of wind.
def convert_degree_to_wind_direction(degree : float):
    if degree in range(350, 360) or degree in range(0, 10):
        return "N"
    elif degree in range(10,30):
        return "NNE"
    elif degree in range(30,60):
        return "NE"
    elif degree in range(60,80):
        return "ENE"
    elif degree in range(80,110):
        return "E"
    elif degree in range(110,130):
        return "ESE"
    elif degree in range(130, 150):
        return "SE"
    elif degree in range(150,170):
        return "SSE"
    elif degree in range(170,200):
        return "S"
    elif degree in range(200,220):
        return "SSW"
    elif degree in range(220,240):
        return "SW"
    elif degree in range(240,260):
        return "WSW"
    elif degree in range(260,290):
        return "W"
    elif degree in range(290,310):
        return "WNW"
    elif degree in range(310,330):
        return "NW"
    elif degree in range(330,350):
        return "NNW"
    #There is most surely a quicker way to do this, but I tired :(
    # Melody from 3 days later, so what you're tired now there's this ABOMINATION in my
    # code. I'm tired though, so I won't fix it.
    return "?" # exists to make the linter happy

# Given an amount of precipitation, in mm (the only unit passed by
# OpenWeatherMap for precip.), turn it into feet or inches depending on the significance
# 10mm -> 10mm
# 13mm -> 0.51in
# 645mm -> 2ft, 1 inch
def format_mm_to_units(amount_precip : float):
    precip_in_feet = 0 # Precip amount in feet
    precip_in_inches = 0 # Precip amount in inches
    # since both can display, we need a val for both

    # 25.4mm = 1 inch

    # being over half an inch is enough to go up for me, anything less looks like the
    # program is being over sensitive, any more and it looks like very very much rain.
    if amount_precip > 12.7:
        precip_in_feet = 0
        precip_in_inches = amount_precip / 25.4
        # if theres more than a foot of rain, then convert to feet
        if precip_in_inches > 12:
            precip_in_feet = precip_in_inches // 12
            precip_in_inches -= (12 * (precip_in_feet))

        precip_display = "" # The value to display by the program
        # if theres feet, display feet
        if precip_in_feet > 0:
            precip_display += f"{precip_in_feet:.00f} feet"
            # if inches exist as well, display inches
            if precip_in_inches >= 1:
                precip_display += f", and {precip_in_inches:.0f} inch"
        else:
            # If there's no feet, we just need inches
            precip_display += f"{precip_in_inches:.02f} inch"
        # for plural, display "es" instead of inch
        if precip_in_inches > 1:
            precip_display += "es"
    else:
        # If precip. is too insignificant to be converted at all
        precip_display = str(amount_precip) + " mm"

    return precip_display

# Count how many numbers exist after a float's decimal, up to a limit. Will count past
# zeroes, and count zeroes if theres numbers after in the limit. EG,
# 3 = 0
# 35 = 0
# 54.0 = 0
# 42.1 = 1
# 12.09 = 2
# etc
def count_decimals(value : float, lim : int = 2):
    use_value = value # The value to use when looping, will be modified
    total_decimals = 0 # How many decimals exist that have been counted
    buffer_decimals = 0 # How many zeroes exist since the last decimal, but can't be counted yet

    # Count all numbers, buffered zeroes and non-zeroes included
    while total_decimals+buffer_decimals < lim:
        next_decimal = math.floor((use_value-math.floor(use_value))*10) # Step up
        # If the digit is a zero, buffer it
        if next_decimal == 0:
            buffer_decimals += 1
        # Else, record, reset buffer, continue
        else:
            total_decimals += 1
            total_decimals += buffer_decimals
            buffer_decimals = 0

        use_value *= 10

    return total_decimals

# Format the visiblity, meters, to KM. Was going to support dacameters and hectameters
# but those units are less represented and cause confusions if the user is not familiar
metric_prefixes = ["", "da" "h", "k"]
def format_meters_to_km(value : float):
    steps_up = 0 # How many steps needed to get to the unit
    return_value = value # Value to render, is modified
    if value > 1000: # Kilo = 1000
        return_value = value / 1000
        steps_up = 2

    format_str = format(return_value, "."+str(count_decimals(return_value))+"f") # Formatted number, done this way for modularity, since doing .02f can lead ugly trailing zeroes
    # strip any resistent trailing zeroes from edge rounding cases
    if "." in format_str:
        format_str = format_str.rstrip("0")

    return_value_str = format_str+metric_prefixes[steps_up] # The actual string, with unit, to return
    return return_value_str+"m"

# Decide if the program should use rain or snow as text representation
def get_rain_or_snow_from_model(will_rain, amount_precip):
    is_rain_or_snow = "rain" if will_rain else "snow"
    if amount_precip == 0:
        return[False]
    else:
        return[True, is_rain_or_snow]

# Turn a unit epoch stamp into a time output
def get_formatted_time_from_timestamp(timestamp : int):
    time_as_object = datetime.datetime.fromtimestamp(timestamp, tz=datetime.timezone.utc) # unix epoch as a timedate object
    hour = "00" # Properly displayed hour, the epoch uses 0-23.
    pm_or_am = "AM" # AM OR PM time
    # If the time is midnight or noon reference it as so
    if time_as_object.hour == 0 or time_as_object.hour == 12:
        hour = "12"
    # If over noon, it's PM and reduce the hour by 12
    elif time_as_object.hour > 12:
        pm_or_am = "PM"
        hour = str(time_as_object.hour - 12)
    else:
    # If before noon and not midnight, no changes needed
        hour = str(time_as_object.hour)

    return [time_as_object, hour, pm_or_am]

# Tell the frontend to display new data
def update_panels(panels : ui_handler.PanelContainer, conditions : list[ui_handler.PanelCondition]):
    panels.update_panels(conditions)
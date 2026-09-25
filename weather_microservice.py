# NAME: Melody
# Program Status: Commenting
# Description:
"""
This program acts as an endpoint for ui_backend to get data from APIs, including
openweathermap's forecast and conditions endpoint, openweathermap's icon endpoint,
and github gist's raw user content. I used github gists to store icons I made on an
external platform, making it so that I will only have to submit the 5 files necessary.
easier for you and me
"""

import requests
from enum import StrEnum
from dataclasses import dataclass

# Every type of API request that can be made
class RequestType(StrEnum):
    WEATHER_ICON = "https://openweathermap.org/payload/api/media/file/" # Request a condition icon
    WEATHER_ICON_GIST = "https://gist.github.com/EgguProgramming/2be3795235e87f6f263d47d1ab39ab2f/raw/" # Request a misc. icon
    ZIP_GEO = "http://api.openweathermap.org/geo/1.0/zip?zip=" # Request a location from zip
    CITY_GEO = "https://api.openweathermap.org/geo/1.0/direct?q=" # Request a location from name
    WEATHER_FORECAST_ONECALL = "https://api.openweathermap.org/data/4.0/onecall/timeline/1day?lat=" # Use the onecall endpoint to request the conditions
    WEATHER_FORECAST_16D = "https://api.openweathermap.org/data/2.5/forecast/daily?lat=" # use the 16d endpoint to get the 7day forecase
    WEATHER_CURRENT = "https://api.openweathermap.org/data/2.5/weather?lat=" # Use OpenWeatherMap's traditional API to get the current conditions

# Object holding city name for request
@dataclass
class CityGeolocationData:
    city_name : str

# Object holding icon id for request
@dataclass
class IconRequestData:
    condition_id : int

# Object holding icon id for request
@dataclass
class IconRequestGistData:
    iconName : str

# Object holding zip code for request
@dataclass
class ZipGeolocationData:
    zip_code : int

# Object holding lat/lon for request
@dataclass
class WeatherData:
    lat : float
    lon : float

# Send an api request to an\ specific endpoint with data specified
def send_api_request(request_type : RequestType, data : WeatherData | CityGeolocationData | IconRequestData | IconRequestGistData | ZipGeolocationData, api_key : str):
    request_url = "" # The URL to send the request to
    if request_type == RequestType.CITY_GEO:
        request_url = request_type.value + data.city_name + "&limit=5"
        request_url += "&appid="+str(api_key)
    elif request_type == RequestType.WEATHER_ICON:
        request_url = "https://openweathermap.org/payload/api/media/file/"+ data.condition_id + ".png"
    elif request_type == RequestType.WEATHER_ICON_GIST:
        request_url = request_type + data.iconName + ".txt"
    elif request_type == RequestType.ZIP_GEO:
        request_url = request_type.value + str(data.zip_code)+"&appid="+api_key
    elif request_type == RequestType.WEATHER_FORECAST_ONECALL:
        request_url = f"{request_type.value}{str(data.lat)}&lon={str(data.lon)}&appid={api_key}"
    elif request_type == RequestType.WEATHER_FORECAST_16D:
        request_url = f"{request_type.value}{str(data.lat)}&lon={str(data.lon)}&units=imperial&cnt=7&appid={api_key}"
    elif request_type == RequestType.WEATHER_CURRENT:
        request_url = f"{request_type.value}{str(data.lat)}&lon={str(data.lon)}&units=imperial&appid={api_key}"

    # use requests library to send the request
    return requests.get(request_url)

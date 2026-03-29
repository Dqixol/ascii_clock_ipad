from art import text2art
import datetime
import subprocess
from lunardate import LunarDate
import json
import pytz
import pandas as pd
import geopy
from timezonefinder import TimezoneFinder

from forcast_doi import hourly_doi, air_quality_doi, hourly_url, air_quality_url, current_url, current_doi
wmo_codes = json.load(open("wmo.json", "r"))

def determine_th_st_nd_rd(day):
    if 4 <= day <= 20 or 24 <= day <= 30:
        return "th" 
    else: 
        return ["st", "nd", "rd"][day % 10 - 1]

def getLunarChineseChars(month, day):
    chinese_months = [
        "正月", "二月", "三月", "四月", "五月", "六月", "七月", "八月", "九月", "十月", "冬月", "腊月"
    ]
    chinese_days = [
        "初一", "初二", "初三", "初四", "初五", "初六", "初七", "初八", "初九", "初十",
        "十一", "十二", "十三", "十四", "十五", "十六", "十七", "十八", "十九", "二十",
        "廿一", "廿二", "廿三", "廿四", "廿五", "廿六", "廿七", "廿八", "廿九", "三十"
    ]
    return chinese_months[month-1] + chinese_days[day-1]
class weatherInfo:
    def __init__(self, location_human):
        self.location_human = location_human
        self.location, self.gps_coords = geopy.geocoders.Nominatim(user_agent="myGeocoder").geocode(location_human)
        if self.location is None:
            raise ValueError(f"Could not geocode location: {location_human}")
        if len(self.location.split(",")) > 3:
            self.location = ",".join(self.location.split(",")[:3])
        self.weather_now = None
        self.weather_forcast = None
        self.last_update_time = None
        self.tz = TimezoneFinder().timezone_at(lng=self.gps_coords[1], lat=self.gps_coords[0])
        self.pytz = pytz.timezone(self.tz) if self.tz else None
        self.df_forcast = None
        self.df_air_quality = None
        self.getCurrentCondition()
        self.getDoI()
    
    def getCurrentCondition(self):
        try: 
            data_current = subprocess.getoutput(f'curl -fGsS "{current_url}?latitude={self.gps_coords[0]}&longitude={self.gps_coords[1]}&current={",".join(current_doi)}&timezone={self.tz.replace("/", "%2F")}"')
        except Exception as e:
            print("Error fetching current weather data, retry in 10 seconds...")
            print(e)
            return
        dict_current = json.loads(data_current)
        wmo_res = wmo_codes.get(str(dict_current['current']['weather_code']))
        if wmo_res:
            if dict_current['current']['is_day'] == 1:
                wmo_now_res = wmo_res.get("day")
            else:
                wmo_now_res = wmo_res.get("night")
            image_path = f'static/google-weather-icons/sets/set-2/{wmo_now_res["image"]}.png'
            description = wmo_now_res.get("description")
        else:
            image_path = 'static/google-weather-icons/sets/set-2/tornado.png'
            description = f"Unknown Weather code {dict_current['current']['weather_code']}"
        condition_to_print = {
            "temperature_2m": f"{dict_current['current']['temperature_2m']}{dict_current['current_units']['temperature_2m']}",
            "apparent_temperature": f"{dict_current['current']['apparent_temperature']}{dict_current['current_units']['apparent_temperature']}",
            "relative_humidity_2m": f"{dict_current['current']['relative_humidity_2m']}{dict_current['current_units']['relative_humidity_2m']}",
            "cloud_cover": f"{dict_current['current']['cloud_cover']}{dict_current['current_units']['cloud_cover']}",
            "surface_pressure" : f"{dict_current['current']['surface_pressure']}{dict_current['current_units']['surface_pressure']}",
            "wind_speed_10m" : f"{dict_current['current']['wind_speed_10m']}{dict_current['current_units']['wind_speed_10m']}",
            "wind_gusts_10m" : f"{dict_current['current']['wind_gusts_10m']}{dict_current['current_units']['wind_gusts_10m']}",
            "wmo_description": description,
            "wmo_image_path": image_path,
        }
        self.weather_now = condition_to_print
        self.last_update_time = datetime.datetime.now(tz=self.pytz)

    def getDoI(self):
        while True:
            try:
                details_forcast     = subprocess.getoutput(f'curl -fGsS "{hourly_url     }?latitude={self.gps_coords[0]}&longitude={self.gps_coords[1]}&hourly={",".join(     hourly_doi)}&forecast_days=2&timezone={self.tz.replace("/", "%2F")}"')
                details_air_quality = subprocess.getoutput(f'curl -fGsS "{air_quality_url}?latitude={self.gps_coords[0]}&longitude={self.gps_coords[1]}&hourly={",".join(air_quality_doi)}&forecast_days=2&timezone={self.tz.replace("/", "%2F")}"')
                data_forcast = json.loads(details_forcast)
                data_air_quality = json.loads(details_air_quality)
                break
            except Exception as e:
                print("Error fetching weather data, retry in 10 seconds...")
                print(e)
                return

        now = datetime.datetime.now(tz=self.pytz)
        df_forcast = pd.DataFrame(data_forcast["hourly"])
        df_forcast["time"] = [self.pytz.localize(datetime.datetime.fromisoformat(t)) for t in df_forcast["time"]]
        df_forcast = df_forcast[df_forcast["time"] >= now - datetime.timedelta(minutes=20)]
        df_forcast = df_forcast[df_forcast["time"] < now + datetime.timedelta(days=1, minutes=15)]

        df_air_quality = pd.DataFrame(data_air_quality["hourly"])
        df_air_quality["time"] = [self.pytz.localize(datetime.datetime.fromisoformat(t)) for t in df_air_quality["time"]]
        df_air_quality = df_air_quality[df_air_quality["time"] >= now - datetime.timedelta(minutes=60)]
        df_air_quality = df_air_quality[df_air_quality["time"] < now + datetime.timedelta(days=1, hours=1)]
        try:
            df_air_quality = df_air_quality.set_index("time").drop_duplicates().resample(datetime.timedelta(minutes=1)).interpolate().reset_index()
        except:
            pass
        self.df_forcast = df_forcast
        self.df_air_quality = df_air_quality

    def getDateArt(self):
        now = datetime.datetime.now(tz=self.pytz)
        date_str = now .strftime(f"%a %d{determine_th_st_nd_rd(now.day)} %b") 
        return date_str
    
    def getTimeArt(self):
        now = datetime.datetime.now(tz=self.pytz)
        hour_str = now.strftime("%H")
        minute_str = now.strftime("%M")
        dot_str = ":" if now.second % 2 == 0 else " "
        return f'{hour_str}{dot_str}{minute_str}'
    
    def getTitleArt(self):
        now = datetime.datetime.now(tz=self.pytz)
        lunar_date = LunarDate.fromSolarDate(now.year, now.month, now.day)
        lunar_date_str = getLunarChineseChars(lunar_date.month, lunar_date.day)
        return f'{self.location.strip()}, {lunar_date_str}'

    def getCurrentCondArt(self):
        now = datetime.datetime.now(tz=self.pytz)
        if self.weather_now is None or (now - self.last_update_time).total_seconds() > 20*60:
            self.getCurrentCondition()
        return  f'|               \n' +\
                f'|               \n' +\
                f'|  Temperature: \n' +\
                f'|  Humidity:    \n' +\
                f'|  Cloud cover: \n' +\
                f'|  Wind:        \n', \
                \
                f'Updated {(now - self.last_update_time).total_seconds()/60:.0f} mins ago\n' + \
                f'{self.weather_now["wmo_description"]}\n' + \
                f'{self.weather_now["temperature_2m"]}; feels like {self.weather_now["apparent_temperature"]}\n' + \
                f'{self.weather_now["relative_humidity_2m"]}\n' + \
                f'{self.weather_now["cloud_cover"]}\n' + \
                f'{self.weather_now["wind_speed_10m"]}; gusts {self.weather_now["wind_gusts_10m"]}', \
                \
                self.weather_now["wmo_image_path"]
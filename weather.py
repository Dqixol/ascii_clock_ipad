import datetime
import subprocess
from lunardate import LunarDate
import json
import pytz
import pandas as pd
import requests
import geopy
from timezonefinder import TimezoneFinder
from io import StringIO
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
plt.style.use('dark_background')
import matplotlib.dates as mdates
import numpy as np

from forcast_doi import hourly_doi, air_quality_doi, weather_url, air_quality_url, current_doi
wmo_codes = json.load(open("wmo.json", "r"))

colour_dict = {
    'polar_night' : '#2E3440',
    'polar_dawn'   : '#3B4252',
    'polar_dusk'    : '#434C5E',
    'polar_day'   : '#4C566A',
    'snow_storm' : '#D8DEE9',
    'snow'       : '#E5E9F0',
    'snow_melt'  : '#ECEFF4',
    'frost_green' : '#8FBCBB',
    'frost_cyan'  : '#88C0D0',
    'frost_blue'  : '#81A1C1',
    'frost_dblue' : '#5E81AC',
    'aurora_red'  : '#BF616A',
    'aurora_orange' : '#D08770',
    'aurora_yellow' : '#EBCB8B',
    'aurora_green' : '#A3BE8C',
    'aurora_purple' : '#B48EAD',
}

def determine_th_st_nd_rd(day):
    if 4 <= day <= 20 or 24 <= day <= 30:
        return "th" 
    else: 
        return ["st", "nd", "rd"][day % 10 - 1]

def getLunarChineseChars(month, day, year=None):
    chinese_months = [
        "正月", "貳月", "參月", "肆月", "伍月", "陸月", "柒月", "捌月", "玖月", "拾月", "冬月", "腊月"
    ]
    chinese_days = [
        "初壹", "初貳", "初參", "初肆", "初伍", "初陸", "初柒", "初捌", "初玖", "初拾",
        "拾壹", "拾貳", "拾參", "拾肆", "拾伍", "拾陸", "拾柒", "拾捌", "拾玖", "貳拾",
        "廿壹", "廿貳", "廿參", "廿肆", "廿伍", "廿陸", "廿柒", "廿捌", "廿玖", "參拾"
    ]
    return f'{chinese_months[month-1]}{chinese_days[day-1]}'
class weatherInfo:
    def __init__(self, location_human):
        self.location_human = location_human
        try:
            self.getLocation()
        except Exception as e:
            print("Error fetching location data:")
            print(e)
            raise
        if self.location is None:
            raise ValueError(f"Could not geocode location: {location_human}")
        if len(self.location.split(",")) > 3:
            self.location = ",".join(self.location.split(",")[:3])
        self.weather_now = None
        self.weather_forcast = None
        self.weather_update_time = None
        self.air_quality_update_time = None
        self.tz = TimezoneFinder().timezone_at(lng=self.gps_coords[1], lat=self.gps_coords[0])
        self.pytz = pytz.timezone(self.tz) if self.tz else None
        self.dict_weather = None
        self.dict_air_quality = None
        self.df_forcast = None
        self.df_forcast_smoothed = None
        self.df_air_quality = None
        self.requestMaybe(test_failure=False)

    def requestWrapper(self, url, params):
        response = requests.get(url, params=params)
        if response.status_code != 200:
            print(f"Error fetching from {url}: {response.status_code}")
            data = {
                "error_code" : response.status_code,
                "error_message" : response.text
            }
        else:
            data = response.json()
        return data

    def requestMaybe(self, test_failure=False):
        if test_failure:
            print("Simulating request failure for testing...")
            return
        weather_parmas = {
            "latitude": f'{float(self.gps_coords[0]):.3f}',
            "longitude": f'{float(self.gps_coords[1]):.3f}',
            "current": ",".join(current_doi),
            "hourly": ",".join(hourly_doi),
            "forecast_days": 2,
            "timezone": self.tz
        }
        air_quality_params = {
            "latitude": f'{float(self.gps_coords[0]):.3f}',
            "longitude": f'{float(self.gps_coords[1]):.3f}',
            "hourly": ",".join(air_quality_doi),
            "forecast_days": 2,
            "timezone": self.tz
        }
        if self.weather_update_time is None or (datetime.datetime.now(tz=self.pytz) - self.weather_update_time).total_seconds() > 10*60:
            ans = self.requestWrapper(weather_url, weather_parmas)
            if ans and "error_code" not in ans:
                self.dict_weather = ans
                self.weather_update_time = datetime.datetime.now(tz=self.pytz)
        if self.air_quality_update_time is None or (datetime.datetime.now(tz=self.pytz) - self.air_quality_update_time).total_seconds() > 10*60:
            ans = self.requestWrapper(air_quality_url, air_quality_params)
            if ans and "error_code" not in ans:
                self.dict_air_quality = ans
                self.air_quality_update_time = datetime.datetime.now(tz=self.pytz)

    def getLocation(self):
        self.location, self.gps_coords = geopy.geocoders.Nominatim(user_agent="myGeocoder_ascii_clock").geocode(self.location_human)
    
    def getCurrentCondition(self):
        self.requestMaybe(test_failure=False)
        dict_current = self.dict_weather
        if dict_current is None or "current" not in dict_current:
            return
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
            "temperature_2m": f"{float(dict_current['current']['temperature_2m']):.0f}{dict_current['current_units']['temperature_2m']}",
            "apparent_temperature": f"{float(dict_current['current']['apparent_temperature']):.0f}{dict_current['current_units']['apparent_temperature']}",
            "relative_humidity_2m": f"{float(dict_current['current']['relative_humidity_2m']):.0f}{dict_current['current_units']['relative_humidity_2m']}",
            "cloud_cover": f"{float(dict_current['current']['cloud_cover']):.0f}{dict_current['current_units']['cloud_cover']}",
            "surface_pressure" : f"{float(dict_current['current']['surface_pressure']):.0f}{dict_current['current_units']['surface_pressure']}",
            "wind_speed_10m" : f"{float(dict_current['current']['wind_speed_10m']):.0f}{dict_current['current_units']['wind_speed_10m']}",
            "wind_gusts_10m" : f"{float(dict_current['current']['wind_gusts_10m']):.0f}{dict_current['current_units']['wind_gusts_10m']}",
            "wmo_description": description,
            "wmo_image_path": image_path,
        }
        self.weather_now = condition_to_print

    def getDoI(self):
        now = datetime.datetime.now(tz=self.pytz)
        self.requestMaybe(test_failure=False)
        if  self.dict_weather:
            data_forcast = self.dict_weather
            df_forcast = pd.DataFrame(data_forcast["hourly"])
            df_forcast["time"] = [self.pytz.localize(datetime.datetime.fromisoformat(t)) for t in df_forcast["time"]]
            df_forcast = df_forcast[df_forcast["time"] >= now - datetime.timedelta(minutes=20)]
            df_forcast = df_forcast[df_forcast["time"] < now + datetime.timedelta(days=1, minutes=15)]
            self.df_forcast = df_forcast
            try:
                df_forcast_smoothed = df_forcast.set_index("time").drop_duplicates().resample(datetime.timedelta(minutes=1)).interpolate(method='cubic').reset_index()
                self.df_forcast_smoothed = df_forcast_smoothed
                self.df_forcast_smoothed['cloud_cover'] = self.df_forcast_smoothed['cloud_cover'].clip(upper=100).clip(lower=0.0)
            except Exception as e:
                print("Error processing weather data:")
                print(e)
                pass
        if self.dict_air_quality:
            data_air_quality = self.dict_air_quality
            df_air_quality = pd.DataFrame(data_air_quality["hourly"])
            df_air_quality["time"] = [self.pytz.localize(datetime.datetime.fromisoformat(t)) for t in df_air_quality["time"]]
            df_air_quality = df_air_quality[df_air_quality["time"] >= now - datetime.timedelta(minutes=60)]
            df_air_quality = df_air_quality[df_air_quality["time"] < now + datetime.timedelta(days=1, hours=1)]
            try:
                df_air_quality = df_air_quality.set_index("time").drop_duplicates().resample(datetime.timedelta(minutes=1)).interpolate(method='cubic').reset_index()
            except Exception as e:
                print("Error processing weather data:")
                print(e)
                pass
            self.df_air_quality = df_air_quality

    def plot(self):
        self.getDoI()
        if self.df_forcast is None or self.df_air_quality is None:
            fig, axs = plt.subplots(2, 2, figsize=(12, 3.5))
            for ax in axs.flat:
                ax.text(0.5, 0.5, "Weather data not available", horizontalalignment='center', verticalalignment='center', transform=ax.transAxes, fontsize=12)
        else:    
            legend_kwargs = {"loc": "upper right", "frameon" : False, "fontsize": 12}
            fig, axs = plt.subplots(2, 2, figsize=(12, 3.5))
            for ax in axs.flat:
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%Hh'))
                ax.set_xlim(self.df_forcast_smoothed["time"].min(), self.df_forcast_smoothed["time"].max())
            # ax00:
            for ax in [axs[0,0]]:
                ax.plot(self.df_forcast_smoothed["time"], self.df_forcast_smoothed["temperature_2m"], label="Temperature [°C]", color=colour_dict["aurora_orange"])
                ax.plot(self.df_forcast_smoothed["time"], self.df_forcast_smoothed["apparent_temperature"], label="Feels Like [°C]", color=colour_dict["frost_cyan"])
                min_temp = min(self.df_forcast_smoothed["temperature_2m"].min(), self.df_forcast_smoothed["apparent_temperature"].min())
                max_temp = max(self.df_forcast_smoothed["temperature_2m"].max(), self.df_forcast_smoothed["apparent_temperature"].max())
                temp_range = max_temp - min_temp
                ax.set_ylim(min_temp - temp_range * 0.1, max_temp + temp_range * 0.4)
                ax.legend(**legend_kwargs, ncol=2)
                ax.get_xaxis().set_visible(False)
            for ax in [axs[0,1]]:
                ax_perc = ax.twinx()
                pa = ax_perc.bar(self.df_forcast["time"], self.df_forcast["precipitation"], label="Prec. [mm/h]", color=colour_dict["frost_green"], width = 0.03)
                ax_perc.set_ylim(0, 0.8 if self.df_forcast["precipitation"].max() * 2 < 0.8 else self.df_forcast["precipitation"].max() * 2)
                pp = ax.plot(self.df_forcast_smoothed["time"], self.df_forcast_smoothed["precipitation_probability"]/100.0, label="Perc. Prob.", color=colour_dict["frost_cyan"])
                cc = ax.plot(self.df_forcast_smoothed["time"], self.df_forcast_smoothed["cloud_cover"]/100.0, label="Cloud Cover", color=colour_dict["snow_storm"])
                rh = ax.plot(self.df_forcast_smoothed["time"], self.df_forcast_smoothed["relative_humidity_2m"]/100.0, label="Humidity", color=colour_dict["aurora_green"])
                ax.legend(handles = [rh[0], cc[0]], loc="upper left", frameon=False, fontsize=12, ncol=1)
                ax_perc.legend(handles = [pa[0], pp[0]], labels=["Prec. [mm/h]", "Perc. Prob."], loc="upper right", frameon=False, fontsize=12)
                ax.get_xaxis().set_visible(False)
                ax.plot(self.df_forcast_smoothed["time"], np.ones_like(self.df_forcast_smoothed["time"]), color=colour_dict["snow_melt"], alpha=0.3, linestyle="--")
                ax.set_ylim(0, 2)
            for ax in [axs[1, 0]]:
                dominant_allergens = ["birch_pollen"]
                allergen_cols = ['alder_pollen', 'grass_pollen', 'mugwort_pollen', 'olive_pollen', 'ragweed_pollen']
                dominant_allergens += [self.df_air_quality[allergen_cols].max().idxmax()]
                maxmax = self.df_air_quality[dominant_allergens].max().max()
                minmin = self.df_air_quality[dominant_allergens].min().min()
                if maxmax == 0:
                    ax.text(0.5, 0.5, "No significant allergen forcasted", horizontalalignment='center', verticalalignment='center', transform=ax.transAxes, fontsize=12)
                for dominant_allergen in dominant_allergens:
                    if self.df_air_quality[dominant_allergen].max() == 0:
                        continue
                    if dominant_allergen == "birch_pollen":
                        label = 'Birch'
                    else:
                        label = f"{dominant_allergen.replace('_', ' ').title()} [grns/m³]"
                    ax.plot(self.df_air_quality["time"], self.df_air_quality[dominant_allergen], label=label)
                ax.legend(**legend_kwargs, ncol=2)
                allergen_range = maxmax - minmin
                ax.set_ylim(0, maxmax + allergen_range * 0.4)
                ax.fill_between(self.df_air_quality["time"], 0, 30, color=colour_dict["aurora_green"], alpha=0.25)
                ax.fill_between(self.df_air_quality["time"], 30, 60, color=colour_dict["aurora_yellow"], alpha=0.25)
                ax.fill_between(self.df_air_quality["time"], 60, 150, color=colour_dict["aurora_red"], alpha=0.25)
                ax.fill_between(self.df_air_quality["time"], 150, 1000, color=colour_dict["aurora_purple"], alpha=0.25)

            for ax in [axs[1, 1]]:
                ax.set_ylim(0, 100 if self.df_air_quality["european_aqi"].max() < 100 else self.df_air_quality["european_aqi"].max() * 1.4)
                ax.plot(self.df_air_quality["time"], self.df_air_quality["european_aqi"], label="European AQI", color = colour_dict["frost_cyan"])
                ax.legend(**legend_kwargs)
                ax.fill_between(self.df_air_quality["time"], 0, 50, color=colour_dict["frost_cyan"], alpha=0.25)
                ax.fill_between(self.df_air_quality["time"], 50, 100, color=colour_dict["aurora_green"], alpha=0.25)
                ax.fill_between(self.df_air_quality["time"], 100, 150, color=colour_dict["aurora_yellow"], alpha=0.25)
                ax.fill_between(self.df_air_quality["time"], 150, 250, color=colour_dict["aurora_red"], alpha=0.25)
                ax.fill_between(self.df_air_quality["time"], 250, 1000, color=colour_dict["aurora_purple"], alpha=0.25)

        fig.tight_layout()
        buf = StringIO()
        fig.savefig(buf, format="svg", bbox_inches="tight", transparent=True)
        plt.close(fig)
        return buf.getvalue()

    def getFutureCondition(self):
        now = datetime.datetime.now(tz=self.pytz)
        self.getDoI()
        if self.df_forcast is None:
            return []
        df_future_cond = self.df_forcast[["time", "weather_code"]]
        df_future_cond = df_future_cond[df_future_cond["time"] > now]
        df_future_cond = df_future_cond.head(12)
        df_future_cond['time'] = df_future_cond['time'].dt.strftime('%H')
        df_future_cond['is_day'] = df_future_cond['time'].astype(int).apply(lambda x: 1 if 7 <= x and x <= 18 else 0)
        df_future_cond["wmo_description"] = df_future_cond[["weather_code", "is_day"]].apply(lambda row: wmo_codes.get(str(row["weather_code"]), {}).get('day' if row["is_day"] else "night", {}).get("description", f"Unknown code {row['weather_code']}"), axis=1)
        df_future_cond["wmo_image_path"]  = df_future_cond[["weather_code", "is_day"]].apply(lambda row: f'static/google-weather-icons/sets/set-2/{wmo_codes.get(str(row["weather_code"]), {}).get(("day" if row["is_day"] else "night"), {}).get("image", "tornado")}.png', axis=1)
        df_future_cond = df_future_cond[["time", "weather_code", "wmo_description", "wmo_image_path"]]
        return df_future_cond.to_dict(orient="records")

    def getDateArt(self):
        now = datetime.datetime.now(tz=self.pytz)
        date_str = now .strftime(f"%a %d{determine_th_st_nd_rd(now.day)} %b") 
        return date_str
    
    def getTimeArt(self):
        now = datetime.datetime.now(tz=self.pytz)
        return now.strftime("%H:%M:%S")
    
    def getTitleArt(self):
        now = datetime.datetime.now(tz=self.pytz)
        lunar_date = LunarDate.fromSolarDate(now.year, now.month, now.day)
        lunar_date_str = getLunarChineseChars(lunar_date.month, lunar_date.day)
        return f'{self.location.strip()}, {lunar_date_str}'

    def getCurrentCondArt(self):
        self.getCurrentCondition()
        if self.weather_now is None:
            return "Weather data not available", 'static/google-weather-icons/sets/set-2/tornado.png'
        now = datetime.datetime.now(tz=self.pytz)
        
        if (now - self.weather_update_time).total_seconds() > 60:
            updated_text = f'Updated {(now - self.weather_update_time).total_seconds()/60:.0f} mins ago' 
        else: 
            updated_text = f'Updated just now'
        
        lines_latter_only = [
            updated_text,
            f"{self.weather_now['wmo_description']}",
            f"{self.weather_now['temperature_2m']}; feels {self.weather_now['apparent_temperature']}",
            f"{self.weather_now['relative_humidity_2m']}",
            f"{self.weather_now['cloud_cover']}",
            f"{self.weather_now['wind_speed_10m']}; gusts {self.weather_now['wind_gusts_10m']}",
        ]

        max_line_length = max(len(line) for line in lines_latter_only)
        lines_latter_only = [line.rjust(max_line_length) for line in lines_latter_only]

        lines_first_only = [
            "Outdoor:     ",
            "             ",
            "Temperature: ",
            "Humidity:    ", 
            "Cloud cover: ",
            "Wind:        ",
        ]

        lines_combined = [f"{first}{latter}" for first, latter in zip(lines_first_only, lines_latter_only)]
        return '\n'.join(lines_combined), self.weather_now["wmo_image_path"]
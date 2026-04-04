import datetime
import subprocess
from lunardate import LunarDate
import json
import pytz
import pandas as pd
import geopy
from timezonefinder import TimezoneFinder
from io import StringIO
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
plt.style.use('dark_background')
import matplotlib.dates as mdates
import numpy as np

from forcast_doi import hourly_doi, air_quality_doi, hourly_url, air_quality_url, current_url, current_doi
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
        self.cond_last_update_time = None
        self.forcast_last_update_time = None
        self.tz = TimezoneFinder().timezone_at(lng=self.gps_coords[1], lat=self.gps_coords[0])
        self.pytz = pytz.timezone(self.tz) if self.tz else None
        self.df_forcast = None
        self.df_forcast_smoothed = None
        self.df_air_quality = None
        self.getCurrentCondition()
        self.getDoI()

    def getLocation(self):
        self.location, self.gps_coords = geopy.geocoders.Nominatim(user_agent="myGeocoder_ascii_clock").geocode(self.location_human)
    
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
        self.cond_last_update_time = datetime.datetime.now(tz=self.pytz)

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
        self.df_forcast = df_forcast
        try:
            df_forcast_smoothed = df_forcast.set_index("time").drop_duplicates().resample(datetime.timedelta(minutes=1)).interpolate(method='cubic').reset_index()
            df_air_quality = df_air_quality.set_index("time").drop_duplicates().resample(datetime.timedelta(minutes=1)).interpolate(method='cubic').reset_index()
        except Exception as e:
            print("Error processing weather data:")
            print(e)
            pass
        self.forcast_last_update_time = datetime.datetime.now(tz=self.pytz)
        self.df_forcast_smoothed = df_forcast_smoothed
        self.df_air_quality = df_air_quality

    def plot(self):
        self.getDoI()
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
            ax.set_ylim(min_temp -5, max_temp + 5)
            ax.legend(**legend_kwargs, ncol=2)
            ax.get_xaxis().set_visible(False)
        for ax in [axs[0,1]]:
            ax.bar(self.df_forcast_smoothed["time"], self.df_forcast_smoothed["precipitation"], label="Prec. [mm/h]", color=colour_dict["frost_green"], width = 0.005)
            ax.plot(self.df_forcast_smoothed["time"], self.df_forcast_smoothed["precipitation_probability"]/100.0, label="Perc. Prob.", color=colour_dict["frost_cyan"])
            ax.plot(self.df_forcast_smoothed["time"], self.df_forcast_smoothed["cloud_cover"]/100.0, label="Cloud Cover", color=colour_dict["snow_storm"])
            ax.plot(self.df_forcast_smoothed["time"], self.df_forcast_smoothed["relative_humidity_2m"]/100.0, label="Humidity", color=colour_dict["aurora_green"])
            ax.legend(**legend_kwargs, ncol=2)
            ax.get_xaxis().set_visible(False)
            ax.plot(self.df_forcast_smoothed["time"], np.ones_like(self.df_forcast_smoothed["time"]), color=colour_dict["snow_melt"], alpha=0.3, linestyle="--")
            ax.set_ylim(0, 2 if self.df_forcast_smoothed["precipitation"].max() < 1 else self.df_forcast_smoothed["precipitation"].max() + 1)
        for ax in [axs[1, 0]]:
            if self.df_air_quality["birch_pollen"].max() > 5: 
                dominant_allergen = "birch_pollen"
            else: 
                allergen_cols = ['alder_pollen', 'grass_pollen', 'mugwort_pollen', 'olive_pollen', 'ragweed_pollen', 'birch_pollen']
                dominant_allergen = self.df_air_quality[allergen_cols].max().idxmax()
            if self.df_air_quality[dominant_allergen].max() == 0:
                ax.text(0.5, 0.5, "No significant allergen forcasted", horizontalalignment='center', verticalalignment='center', transform=ax.transAxes, fontsize=12)
            else:
                ax.plot(self.df_air_quality["time"], self.df_air_quality[dominant_allergen], label=f"{dominant_allergen.replace('_', ' ').title()} [grains/m³]", alpha=0.0)
                ax.legend(**legend_kwargs)
                ax.set_ylim(0, 50 if self.df_air_quality[dominant_allergen].max() < 50 else self.df_air_quality[dominant_allergen].max() + 20)
                df_allergen_0_10 = self.df_air_quality.query(f"{dominant_allergen} >= 0 and {dominant_allergen} < 10")
                df_allergen_10_20 = self.df_air_quality.query(f"{dominant_allergen} >= 10 and {dominant_allergen} < 20")
                df_allergen_20_100 = self.df_air_quality.query(f"{dominant_allergen} >= 20 and {dominant_allergen} < 100")
                df_allergen_100 = self.df_air_quality.query(f"{dominant_allergen} >= 100")
                ax.bar(df_allergen_0_10["time"],   df_allergen_0_10[dominant_allergen],   color=colour_dict["aurora_green"],  width = 0.002)
                ax.bar(df_allergen_10_20["time"], df_allergen_10_20[dominant_allergen], color=colour_dict["aurora_yellow"], width = 0.002)
                ax.bar(df_allergen_20_100["time"], df_allergen_20_100[dominant_allergen], color=colour_dict["aurora_red"], width = 0.002)
                ax.bar(df_allergen_100["time"],    df_allergen_100[dominant_allergen],    color=colour_dict["aurora_purple"],    width = 0.002)

        for ax in [axs[1, 1]]:
            ax.plot(self.df_air_quality["time"], self.df_air_quality["european_aqi"], label="European AQI", alpha=0.0)
            ax.legend(**legend_kwargs)
            ax.set_ylim(20 if self.df_air_quality["european_aqi"].min() > 20 else self.df_air_quality["european_aqi"].min() - 10, 50 if self.df_air_quality["european_aqi"].max() < 50 else self.df_air_quality["european_aqi"].max() + 10)
            df_aqi_0_50 = self.df_air_quality.query("european_aqi >= 0 and european_aqi < 50")
            df_aqi_50_100 = self.df_air_quality.query("european_aqi >= 50 and european_aqi < 100")
            df_aqi_100_150 = self.df_air_quality.query("european_aqi >= 100 and european_aqi < 150")
            df_aqi_150 = self.df_air_quality.query("european_aqi >= 150")
            ax.bar(df_aqi_0_50["time"],   df_aqi_0_50["european_aqi"],   color=colour_dict["frost_cyan"],  width = 0.002)
            ax.bar(df_aqi_50_100["time"], df_aqi_50_100["european_aqi"], color=colour_dict["aurora_green"], width = 0.002)
            ax.bar(df_aqi_100_150["time"], df_aqi_100_150["european_aqi"], color=colour_dict["aurora_yellow"], width = 0.002)
            ax.bar(df_aqi_150["time"],    df_aqi_150["european_aqi"],    color=colour_dict["aurora_red"],    width = 0.002)

        fig.tight_layout()
        buf = StringIO()
        fig.savefig(buf, format="svg", bbox_inches="tight", transparent=True)
        plt.close(fig)
        return buf.getvalue()

    def getFutureCondition(self):
        now = datetime.datetime.now(tz=self.pytz)
        self.getDoI()
        df_future_cond = self.df_forcast[["time", "weather_code"]]
        df_future_cond = df_future_cond[df_future_cond["time"] > now]
        df_future_cond = df_future_cond.head(24).iloc[::2]
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
        if self.weather_now is None or (now - self.cond_last_update_time).total_seconds() > 20*60:
            self.getCurrentCondition()
        if (now - self.cond_last_update_time).total_seconds() > 60:
            updated_text = f'Updated {(now - self.cond_last_update_time).total_seconds()/60:.0f} mins ago' 
        else: 
            updated_text = f'Updated just now'
        return  f'Outdoor:     \n' +\
                f'             \n' +\
                f'Temperature: \n' +\
                f'Humidity:    \n' +\
                f'Cloud cover: \n' +\
                f'Wind:        \n', \
                \
                f'{updated_text}\n' + \
                f'{self.weather_now["wmo_description"]}\n' + \
                f'{self.weather_now["temperature_2m"]}; feels like {self.weather_now["apparent_temperature"]}\n' + \
                f'{self.weather_now["relative_humidity_2m"]}\n' + \
                f'{self.weather_now["cloud_cover"]}\n' + \
                f'{self.weather_now["wind_speed_10m"]}; gusts {self.weather_now["wind_gusts_10m"]}', \
                \
                self.weather_now["wmo_image_path"]
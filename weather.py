from art import text2art
import datetime
import subprocess
from lunardate import LunarDate
import sys
import json
import pytz
import itertools
import pandas as pd

class bcolors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    BLINK = '\033[5m'
    WHITE = '\033[0m'
    NOCOLOR = ''

chinese_month_art = """
  8888888888888
  8           8
  8888888888888
  8           8
  8888888888888
 8            8
Y            YP
"""

chinese_day_art ="""
888888888888888
8             8
8             8
888888888888888
8             8
8             8
888888888888888
"""

# 农
chinese_lunar_art ="""
      d        
 d88888888888b 
8   d         8
   d 8b   PP   
  d  8 bb P    
 d   8   bb8888
     YP        
"""

chinese_lunar_art = " "* 15 + chinese_lunar_art
chinese_month_art = " "* 15 + chinese_month_art
chinese_day_art   = " "* 15 + chinese_day_art

map_chinese_arts = {
    "month" : chinese_month_art,
    "day" : chinese_day_art,
    "0" : text2art("0", font='colossal'),
    "1" : text2art("1", font='colossal'),
    "2" : text2art("2", font='colossal'),
    "3" : text2art("3", font='colossal'),
    "4" : text2art("4", font='colossal'), 
    "5" : text2art("5", font='colossal'), 
    "6" : text2art("6", font='colossal'), 
    "7" : text2art("7", font='colossal'), 
    "8" : text2art("8", font='colossal'), 
    "9" : text2art("9", font='colossal'),
    "space" : "  \n"* 8
}

def combine_arts(arts):
    art_lines = zip(*[art.splitlines() for art in arts])
    combined_art = "\n".join(" ".join(line) for line in art_lines) 
    return combined_art

def assemble_chinese_date(month, day):
    store = []
    store.append(chinese_lunar_art)
    store.append(map_chinese_arts["space"])
    for char in str(month): 
        store.append(map_chinese_arts[char])
    store.append(map_chinese_arts["month"]) 
    store.append(map_chinese_arts["space"])
    for char in str(day): 
        store.append(map_chinese_arts[char]) 
    store.append(map_chinese_arts["day"])
    return combine_arts(store) + "\n"*2

def determine_th_st_nd_rd(day):
    if 4 <= day <= 20 or 24 <= day <= 30:
        return "th" 
    else: 
        return ["st", "nd", "rd"][day % 10 - 1]

def remove_trailing_newlines(art, num_newlines=2):
    art = art.rstrip()
    art = art + " "* 5
    art = art + "\n"*num_newlines
    return art

def centre_art(art, width):
    art_lines = art.splitlines() 
    centred_lines = [line.center(width) for line in art_lines] 
    return "\n".join(centred_lines)

def colour_art(art, color):
    colored_art = ''
    for line in art.splitlines():
        colored_art += f"{color}{bcolors.BOLD}{line}{bcolors.ENDC}\n"
    return colored_art

def getWeather(postcode):
    # return None, '', 'Unknown Location'
    postcode = postcode.replace(" ", "+")
    weather = subprocess.getoutput(f'curl -fGsS --compressed "wttr.in/{postcode}?1F"')
    weather_split = weather.splitlines()
    if len(weather_split) < 18:
        return None, '', 'Unknown Location', None
    weather_now = weather_split[2:7]
    weather_now = '\n'.join(weather_now)
    weather_forcast = weather_split[7:17]
    weather_forcast = '\n'.join(weather_forcast)
    weather_forcast = weather_forcast[:183] + "   Today    " + weather_forcast[195:]
    location = weather_split[17].split("[")[0].split(":")[1].strip()
    gps_coords = weather_split[17].split("[")[1].split("]")[0].split(",")
    gps_coords = [float(coord) for coord in gps_coords]
    return weather_now, weather_forcast, location, gps_coords

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
        self.weather_now = None
        self.weather_forcast = None
        self.location = None
        self.gps_coords = None
        self.last_update_time = None
        self.tz = None

    def getDoI(self):
        gps_coords = self.gps_coords
        if gps_coords is None:
            _, _, _, gps_coords = getWeather(self.location_human)
            self.gps_coords = gps_coords
        while True:
            try:
                details_forcast     = subprocess.getoutput(f'curl -fGsS "https://api.open-meteo.com/v1/forecast?latitude={gps_coords[0]}&longitude={gps_coords[1]}&minutely_15=temperature_2m,apparent_temperature,precipitation,precipitation_probability&forecast_days=2&timezone=auto"')
                details_air_quality = subprocess.getoutput(f'curl -fGsS "https://air-quality-api.open-meteo.com/v1/air-quality?latitude={gps_coords[0]}&longitude={gps_coords[1]}&hourly=birch_pollen,european_aqi&forecast_days=2&timezone=auto"')
                data_forcast = json.loads(details_forcast)
                data_air_quality = json.loads(details_air_quality)
                break
            except Exception as e:
                print("Error fetching weather data, retry in 10 seconds...")
                print(e)
                print(self.gps_coords)
                import time
                time.sleep(10)

        self.tz = pytz.timezone(data_forcast["timezone"])
        now = datetime.datetime.now(tz=self.tz)
        df_forcast = pd.DataFrame({
            "time": [self.tz.localize(datetime.datetime.fromisoformat(t)) for t in data_forcast["minutely_15"]["time"]],
            "temperature_2m": data_forcast["minutely_15"]["temperature_2m"],
            "apparent_temperature": data_forcast["minutely_15"]["apparent_temperature"],
            "precipitation": data_forcast["minutely_15"]["precipitation"],
            "precipitation_probability": data_forcast["minutely_15"]["precipitation_probability"]
        })
        df_air_quality = pd.DataFrame({
            "time": [self.tz.localize(datetime.datetime.fromisoformat(t)) for t in data_air_quality["hourly"]["time"]],
            "birch_pollen": data_air_quality["hourly"]["birch_pollen"],
            "european_aqi": data_air_quality["hourly"]["european_aqi"]
        })
        # interpolate air quality data to 1min intervals, sometimes it can fail due to e.g. BST / GNT time change...
        df_forcast = df_forcast[df_forcast["time"] >= now - datetime.timedelta(minutes=20)]
        df_forcast = df_forcast[df_forcast["time"] < now + datetime.timedelta(days=1, minutes=15)]
        df_air_quality = df_air_quality[df_air_quality["time"] >= now - datetime.timedelta(minutes=60)]
        df_air_quality = df_air_quality[df_air_quality["time"] < now + datetime.timedelta(days=1, hours=1)]
        try:
            df_air_quality = df_air_quality.set_index("time").drop_duplicates().resample(datetime.timedelta(minutes=1)).interpolate().reset_index()
        except:
            pass
        return df_forcast, df_air_quality

    def getArt(self):
        width = 128
        date_str = None
        now = datetime.datetime.now(tz=self.tz if self.tz else datetime.timezone.utc)
        if self.weather_now is None or (now - self.last_update_time).total_seconds() > 600:
            self.weather_now, self.weather_forcast, self.location, self.gps_coords = getWeather(self.location_human)
            self.last_update_time = now
        date_str = now .strftime(f"%a  %d{determine_th_st_nd_rd(now.day)}  %b") 
        date_art       = text2art(date_str, font='colossal')
        lunar_date = LunarDate.today()
        lunar_date_str = getLunarChineseChars(lunar_date.month, lunar_date.day)
        hour_str = now.strftime("%H")
        minute_str = now.strftime("%M")
        dot_str = " : " if now.second % 2 == 0 else "   "
        time_art = colour_art(text2art(f'{hour_str}{dot_str}{minute_str}', font='colossal'), bcolors.NOCOLOR)

        weather_now_print = f'                Updated {(now - self.last_update_time).total_seconds()/60:.0f}min ago\n' + self.weather_now
        print_part_date = '\n' * (1 if self.location != "Unknown Location" else 10) + colour_art(centre_art(combine_arts([date_art, "\n"*8]), width-1), bcolors.CYAN) + '\n\n'
        print_part_time = combine_arts(['                  \n'* 8, time_art, '   │\n'*8, '\n'*2+weather_now_print]) + '\n\n'
        # print_part_weat = combine_arts([' \n'* 20, self.weather_forcast]) + '\n\n'
        print_part_loca = centre_art(f'{self.location.strip()}, {lunar_date_str}', width-1)
        print_part_all = print_part_loca + '\n\n' + print_part_date + print_part_time
        
        return print_part_all
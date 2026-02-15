from art import text2art
from time import sleep
import datetime
import os
from lunardate import LunarDate
import sys

class bcolors:
    RED = '\033[0;91m'
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
chinese_day_art = " "* 15 + chinese_day_art

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
        colored_art += f"{color}{bcolors.BOLD}{line.rstrip()}{bcolors.ENDC}\n"
    return colored_art

def remove_dots(art):
    return art.replace(" d8b ", "     ").replace(" Y8P ", "     ")

def getWeather():
    # return None, '', 'Unknown Location'
    weather = os.popen('curl -fGsS --compressed "wttr.in/BS1+1NR?2F"').read()
    weather_split = weather.splitlines()
    if len(weather_split) < 27:
        return None, '', 'Unknown Location'
    weather_now = weather.splitlines()[2:7]
    weather_now = '\n'.join(weather_now)
    weather_forcast = weather.splitlines()[7:27]
    weather_forcast = '\n'.join(weather_forcast)
    location = weather.splitlines()[27][10:][:-22]
    return weather_now, weather_forcast, location

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

def main():
    date_str = None
    dot_printed = False
    last_weather_update = now - datetime.timedelta(days=1)
    latest_weather = ('\n'*5 + '         Weather data unavailable\n', '', 'Unknown Location')
    while True:
        now = datetime.datetime.now()
        width, height = os.get_terminal_size()
        if width != 128 or height != 44:
            print('\n'*int(height / 2 - 1) + f"({width}x{height}) Please resize your terminal to exactly 128*44") 
            sleep(1)
            os.system('clear') 
            continue
        if now - last_weather_update > datetime.timedelta(minutes=30):
            weather_now, weather_forcast, location = getWeather()
            if location != "Unknown Location":
                last_weather_update = now
                latest_weather = (weather_now, weather_forcast, location)
        date_str = now .strftime(f"%a  %d{determine_th_st_nd_rd(now.day)}  %b") 
        date_art       = text2art(date_str, font='colossal')
        lunar_date = LunarDate.today()
        lunar_date_str = getLunarChineseChars(lunar_date.month, lunar_date.day)
        hour_str = now .strftime("%H")
        minute_str = now .strftime("%M")
        if not dot_printed:
            dot_printed = True
            dot_str = " : "
        else: 
            dot_printed = False
            dot_str = "   "
        time_art = text2art(f'{hour_str}{dot_str}{minute_str}', font='colossal')
        weather_now, weather_forcast, location = latest_weather
        weather_now_print = f'                Updated {(now - last_weather_update).total_seconds() / 60.0:.0f}min ago\n' + weather_now
        print_part_date = '\n' * (1 if location != "Unknown Location" else 10) + colour_art(centre_art(combine_arts([date_art, "\n"*8]), width-1), bcolors.CYAN) + '\n\n'
        print_part_time = combine_arts(['                  \n'* 8, time_art, '   │\n'*8, '\n'*2+weather_now_print]) + '\n\n'
        print_part_weat = combine_arts([' \n'* 20, weather_forcast]) + '\n\n'
        print_part_loca = centre_art(f'{location.strip()}, {lunar_date_str}', width-1)
        print_part_all = print_part_date + print_part_time + print_part_weat + print_part_loca
        
        os.system('clear')
        print(print_part_all)

        sleep(0.99)
        
if __name__ == "__main__":
    main()
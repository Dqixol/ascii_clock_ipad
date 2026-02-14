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
    colored_art = f"{color}{bcolors.BOLD}{art}{bcolors.ENDC}" 
    return colored_art

def remove_dots(art):
    return art.replace(" d8b ", "     ").replace(" Y8P ", "     ")

def getWeather():
    # weather = open('/Users/jvshang/Documents/ascii_clock_ipad/example_weather.txt').read()
    weather = os.popen('curl -fGsS --compressed "wttr.in/BS1+1NR?1F"').read()
    weather_now = weather.splitlines()[2:7]
    weather_now = '\n'.join(weather_now)
    weather_forcast = weather.splitlines()[7:17]
    weather_forcast = '\n'.join(weather_forcast)
    location = weather.splitlines()[17][10:][:-22]
    if weather_forcast.strip() == '':
        raise
    return weather_now, weather_forcast, location

def getLunarChineseChars(month, day):
    chinese_months = ["正月", "二月", "三月", "四月", "五月", "六月", "七月", "八月", "九月", "十月", "冬月", "腊月"]
    chinese_days = ["初一", "初二", "初三", "初四", "初五", "初六", "初七", "初八", "初九", "初十",
                    "十一", "十二", "十三", "十四", "十五", "十六", "十七", "十八", "十九", "二十",
                    "廿一", "廿二", "廿三", "廿四", "廿五", "廿六", "廿七", "廿八", "廿九", "三十"
                    ]
    return chinese_months[month-1] + chinese_days[day-1]

def main():
    os.system('clear')
    date_str = None
    dot_printed = False
    last_weather_update = datetime.datetime.now() - datetime.timedelta(days=1)
    while True:
        width, height = os.get_terminal_size()
        if width < 125 or height < 30:
            print(f"({width}x{height}) Please resize your terminal to at least 125x30 for optimal display.") 
            sleep(1)
            os.system('clear') 
            continue
        if datetime.datetime.now() - last_weather_update > datetime.timedelta(minutes=30):
            try:
                weather_now, weather_forcast, location = getWeather()
                last_weather_update = datetime.datetime.now()
            except:
                print('failed to get weather, will retry')
        os.system('clear')
        date_str = datetime.datetime.now() .strftime(f"%d{determine_th_st_nd_rd(datetime.datetime.now().day)}  %b") 
        date_art       = text2art(date_str, font='colossal')
        lunar_date = LunarDate.today()
        lunar_date_str = getLunarChineseChars(lunar_date.month, lunar_date.day)
        lunar_date_art = ' \n'*7 + (lunar_date_str + '\n')

        # lunar_date_art = colour_art(remove_trailing_newlines(centre_art(assemble_chinese_date(lunar_date.month, lunar_date.day), width-1), 3), bcolors.YELLOW)
        print('\n' + colour_art(combine_arts(['                  \n'* 8, date_art, '   │    \n'*8, lunar_date_art]), bcolors.CYAN) + '\n')
        try:
            print(centre_art(location, width-1))
            print(combine_arts([' \n'* 10, weather_forcast])+'\n\n')
        except:
            print('\n' + centre_art("Failed to get weather data, will retry", width-1))
        time_str = datetime.datetime.now() .strftime("%H : %M")
        time_art = text2art(time_str,        font='colossal')
        # if not dot_printed:
        #     dot_printed = True
        # else: 
        #     time_art = remove_dots(time_art)
        #     dot_printed = False
        try: 
            weather_now_print = f'                Updated {(datetime.datetime.now() - last_weather_update).total_seconds():.0f}s ago\n' + weather_now
            print(combine_arts(['                  \n'* 8, time_art, '   │\n'*8, '\n'*2+weather_now_print]))
        except:
            print(combine_arts(['                  \n'* 8, time_art]))
        sleep(60)
        
if __name__ == "__main__":
    main()
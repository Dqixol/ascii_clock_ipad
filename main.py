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

def main():
    os.system('clear')
    date_str = None
    width_saved, height_saved = os.get_terminal_size()
    dot_printed = False
    flag_resize = False
    while True:
        width, height = os.get_terminal_size()
        if (width, height) != (width_saved, height_saved):
            flag_resize = True
        if width < 100 or height < 30:
            print(f"({width}x{height}) Please resize your terminal to at least 100x30 for optimal display.") 
            sleep(1)
            os.system('clear') 
            continue
        if flag_resize or ((not date_str) or (date_str != datetime.datetime.now().strftime(f"%d{determine_th_st_nd_rd(datetime.datetime.now().day)}  %b"))):
            os.system('clear')
            date_str = datetime.datetime.now() .strftime(f"%d{determine_th_st_nd_rd(datetime.datetime.now().day)}  %b") 
            lunar_date = LunarDate.today()
            date_art       = colour_art(remove_trailing_newlines(centre_art(             text2art(date_str,        font='colossal'), width-1), 4), bcolors.WHITE)
            lunar_date_art = colour_art(remove_trailing_newlines(centre_art(assemble_chinese_date(lunar_date.month, lunar_date.day), width-1), 4), bcolors.YELLOW)
            print(date_art + lunar_date_art)
        time_str = datetime.datetime.now() .strftime("%H : %M : %S")
        time_art = colour_art(remove_trailing_newlines(centre_art(             text2art(time_str,        font='colossal'), width-1), 2), bcolors.GREEN)
        if not dot_printed:
            dot_printed = True
        else: 
            time_art = remove_dots(time_art)
            dot_printed = False
        print(time_art)
        sleep(1)
        sys.stdout.write('\033[10A')
        sys.stdout.flush()


if __name__ == "__main__":
    main()


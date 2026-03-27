from flask import Flask, render_template, Response
from ansi2html import Ansi2HTMLConverter
import weather
import datetime

from io import StringIO
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
plt.style.use('dark_background')
import matplotlib.dates as mdates

app = Flask(__name__)
conv = Ansi2HTMLConverter(inline=True, scheme="dracula")

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

weather_info = weather.weatherInfo("BS1 1NR")

def make_svg():
    legend_kwargs = {"loc": "upper right", "frameon" : False, "fontsize": 12}
    df_forcast, df_air_quality = weather_info.getDoI()
    fig, axs = plt.subplots(2, 2, figsize=(12, 3.5))
    for ax in axs.flat:
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Hh'))
        ax.set_xlim(df_forcast["time"].min(), df_forcast["time"].max())
    # ax00:
    for ax in [axs[0,0]]:
        ax.plot(df_forcast["time"], df_forcast["temperature_2m"], label="Temperature [°C]", color=colour_dict["aurora_orange"])
        ax.plot(df_forcast["time"], df_forcast["apparent_temperature"], label="Feels like [°C]", color=colour_dict["frost_cyan"])
        min_temp = min(df_forcast["temperature_2m"].min(), df_forcast["apparent_temperature"].min())
        max_temp = max(df_forcast["temperature_2m"].max(), df_forcast["apparent_temperature"].max())
        ax.set_ylim(0 if min_temp > 0 else min_temp - 1, 20 if max_temp < 20 else max_temp + 1)
        ax.legend(**legend_kwargs, ncol=2)
        ax.get_xaxis().set_visible(False)
    for ax in [axs[0,1]]:
        ax.bar(df_forcast["time"], df_forcast["precipitation"]*4.0, width = 0.005, label="Precipitation [mm/h]", color=colour_dict["frost_green"])
        ax.plot(df_forcast["time"], df_forcast["precipitation_probability"]/100.0, label="Probability", color=colour_dict["frost_cyan"])
        ax.legend(**legend_kwargs, ncol=2)
        ax.get_xaxis().set_visible(False)
        ax.set_ylim(0, 1.3 if df_forcast["precipitation"].max() < 1.3 else df_forcast["precipitation"].max() + 0.5)
    for ax in [axs[1, 0]]:
        ax.plot(df_air_quality["time"], df_air_quality["birch_pollen"], label="Birch Pollen [grains/m³]", alpha=0.0)
        ax.legend(**legend_kwargs)
        ax.set_ylim(0, 50 if df_air_quality["birch_pollen"].max() < 50 else df_air_quality["birch_pollen"].max() + 20)
        df_birch_0_10 = df_air_quality.query("birch_pollen >= 0 and birch_pollen < 10")
        df_birch_10_20 = df_air_quality.query("birch_pollen >= 10 and birch_pollen < 20")
        df_birch_20_100 = df_air_quality.query("birch_pollen >= 20 and birch_pollen < 100")
        df_birch_100 = df_air_quality.query("birch_pollen >= 100")
        ax.bar(df_birch_0_10["time"],   df_birch_0_10["birch_pollen"],   color=colour_dict["aurora_green"],  width = 0.005)
        ax.bar(df_birch_10_20["time"], df_birch_10_20["birch_pollen"], color=colour_dict["aurora_yellow"], width = 0.005)
        ax.bar(df_birch_20_100["time"], df_birch_20_100["birch_pollen"], color=colour_dict["aurora_red"], width = 0.005)
        ax.bar(df_birch_100["time"],    df_birch_100["birch_pollen"],    color=colour_dict["aurora_purple"],    width = 0.005)
    for ax in [axs[1, 1]]:
        ax.plot(df_air_quality["time"], df_air_quality["european_aqi"], label="European AQI", alpha=0.0)
        ax.legend(**legend_kwargs)
        ax.set_ylim(20 if df_air_quality["european_aqi"].min() > 20 else df_air_quality["european_aqi"].min() - 10, 50 if df_air_quality["european_aqi"].max() < 50 else df_air_quality["european_aqi"].max() + 10)
        df_aqi_0_50 = df_air_quality.query("european_aqi >= 0 and european_aqi < 50")
        df_aqi_50_100 = df_air_quality.query("european_aqi >= 50 and european_aqi < 100")
        df_aqi_100_150 = df_air_quality.query("european_aqi >= 100 and european_aqi < 150")
        df_aqi_150 = df_air_quality.query("european_aqi >= 150")
        ax.bar(df_aqi_0_50["time"],   df_aqi_0_50["european_aqi"],   color=colour_dict["frost_cyan"],  width = 0.005)
        ax.bar(df_aqi_50_100["time"], df_aqi_50_100["european_aqi"], color=colour_dict["aurora_green"], width = 0.005)
        ax.bar(df_aqi_100_150["time"], df_aqi_100_150["european_aqi"], color=colour_dict["aurora_yellow"], width = 0.005)
        ax.bar(df_aqi_150["time"],    df_aqi_150["european_aqi"],    color=colour_dict["aurora_red"],    width = 0.005)

    fig.tight_layout()
    buf = StringIO()
    fig.savefig(buf, format="svg", bbox_inches="tight", transparent=True)
    plt.close(fig)

    return buf.getvalue()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/art")
def art():
    ascii_art = weather_info.getArt()
    html_art = conv.convert(ascii_art, full=False)
    return html_art

@app.route("/plot.svg")
def plot_svg():
    svg = make_svg()
    return Response(svg, mimetype="image/svg+xml")

if __name__ == "__main__":
    app.run(debug=False, port=3000)
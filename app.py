from time import time, sleep
from flask import Flask, render_template, Response, send_file, jsonify

import weather
import hass

app = Flask(__name__)

while True:
    try:
        weather_info = weather.weatherInfo("BS1 1NR")
        break
    except Exception as e:
        print("Error fetching weather data:", e)
        print("Retrying in 5 seconds...")
        sleep(5)


@app.route("/")
def index():
    return render_template("index.html")

@app.route("/titleText")
def titleText():
    title = weather_info.getTitleArt()
    return title

@app.route("/dateText")
def dateText():
    date = weather_info.getDateArt()
    return date

@app.route("/timeText")
def timeText():
    time = weather_info.getTimeArt()
    return time

@app.route("/currentCondText")
def currentCondText():
    current_cond = weather_info.getCurrentCondArt()
    return current_cond[0]


@app.route("/currentCondImage")
def currentCondImage():
    current_cond = weather_info.getCurrentCondArt()
    return send_file(current_cond[1], mimetype="image/png")

@app.route("/plot.svg")
def plot_svg():
    svg = weather_info.plot()
    return Response(svg, mimetype="image/svg+xml")

@app.route("/forecastCond24h")
def forecastCond24h():
    json_from_df = weather_info.getFutureCondition()  # list of dicts
    return jsonify(json_from_df)

@app.route("/indoorAirQualityPlot.svg")
def indoor_air_quality_plot_svg():
    svg = hass.getPlot(tz=weather_info.tz)
    return Response(svg, mimetype="image/svg+xml")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
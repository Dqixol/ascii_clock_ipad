from flask import Flask, render_template, Response, send_file, jsonify
import weather

app = Flask(__name__)

weather_info = weather.weatherInfo("BS1 1NR")

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

@app.route("/currentCondText1")
def currentCondText1():
    current_cond = weather_info.getCurrentCondArt()
    return current_cond[0]

@app.route("/currentCondText2")
def currentCondText2():
    current_cond = weather_info.getCurrentCondArt()
    return current_cond[1]


@app.route("/currentCondImage")
def currentCondImage():
    current_cond = weather_info.getCurrentCondArt()
    return send_file(current_cond[2], mimetype="image/png")

@app.route("/plot.svg")
def plot_svg():
    svg = weather_info.plot()
    return Response(svg, mimetype="image/svg+xml")

@app.route("/forecastCond24h")
def forecastCond24h():
    json_from_df = weather_info.getFutureCondition()  # list of dicts
    return jsonify(json_from_df)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000, debug=False)
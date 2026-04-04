import requests
import datetime
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
plt.style.use('dark_background')
import matplotlib.dates as mdates
from io import StringIO

API_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJmMmYyOTZlNWI5Yjk0YjJkYWNiM2M4MmU1YzFkMjJmNiIsImlhdCI6MTc3NTI0OTIzMCwiZXhwIjoyMDkwNjA5MjMwfQ.RlItH-wiOKkYw0XWSovBiTGrxin_yS-Oc1xXrzmN-wo'

endpoints = [
    "sensor.first_air_quality_monitor_temperature",
    "sensor.first_air_quality_monitor_humidity",
    "sensor.first_air_quality_monitor_air_quality_index",
    "sensor.first_air_quality_monitor_volatile_organic_compounds_index",
    "sensor.first_air_quality_monitor_pm10",
    "sensor.first_air_quality_monitor_carbon_monoxide",
]

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "content-type": "application/json",
}

base_url = "http://pi5-alarm.local:8123/api/history/period?filter_entity_id="

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

def getPlot(tz, hours=12):
    now = pd.Timestamp.now(tz=tz)
    dfs = {}
    for endpoint in endpoints:
        url = f"{base_url}{endpoint}"
        response = requests.get(url, headers=headers)
        response_json = response.json()
        unit = response_json[0][0]['attributes'].get('unit_of_measurement')
        unit = f'[{unit}]' if unit else ''
        friendly_name = response_json[0][0]['attributes'].get('friendly_name', '')
        df = pd.DataFrame(response_json[0])
        df['state'] = df['state'].replace('unavailable', 'nan')
        df['state'] = df['state'].astype(float)
        df['state'] = df['state'].ffill()
        df['time'] = pd.to_datetime(df['last_changed'], utc=True).dt.tz_convert(tz)
        df = df[['state', 'time']]
        df.loc[len(df)] = {'state': float('nan'), 'time': now}
        df = df.set_index("time").resample(datetime.timedelta(minutes=1)).ffill().reset_index()
        dfs[endpoint] = df, unit, friendly_name, response_json

    fig, axs = plt.subplots(len(endpoints), 1, figsize=(6, 1.75 * len(endpoints)))
    for ax, endpoint in zip(axs,endpoints):
        legend_kwargs = {"loc": "upper right", "frameon" : False, "fontsize": 12}
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Hh'))
        ax.set_xlim(now - pd.Timedelta(hours=hours), now)
        df, unit, friendly_name, response_json = dfs[endpoint]
        friendly_name = friendly_name.split('Monitor ')[-1].title()
        friendly_name = f'Indoor {friendly_name}'
        if endpoint == 'sensor.first_air_quality_monitor_air_quality_index':
            ax.set_ylim(df['state'].min() - 10 if df['state'].min() > 10 else 0, 100)
            ax.plot(df['time'], df['state'], label=f'{friendly_name} {unit}', color = colour_dict['snow_storm'])
            ax.fill_between(df['time'], 90,  100, color=colour_dict['frost_cyan'], alpha=0.25)
            ax.fill_between(df['time'], 80, 90, color=colour_dict['aurora_green'], alpha=0.25)
            ax.fill_between(df['time'], 60, 80, color=colour_dict['aurora_yellow'], alpha=0.25)
            ax.fill_between(df['time'], 40, 60, color=colour_dict['aurora_orange'], alpha=0.25)
            ax.fill_between(df['time'], 20, 40, color=colour_dict['aurora_red'], alpha=0.25)
            ax.fill_between(df['time'], 0, 20, color=colour_dict['aurora_purple'], alpha=0.25)
            legend_kwargs["loc"] = "lower right"
        if endpoint == 'sensor.first_air_quality_monitor_pm10':
            friendly_name = "Indoor Particulate Matter"
            ax.set_ylim(df['state'].min() - 10 if df['state'].min() > 10 else 0, df['state'].max() *1.2)
            ax.plot(df['time'], df['state'], label=f'{friendly_name} {unit}', color = colour_dict['aurora_yellow'])
            ax.fill_between(df['time'], 0, 20, color=colour_dict['aurora_green'], alpha=0.25)
            ax.fill_between(df['time'], 20, 50, color=colour_dict['aurora_yellow'], alpha=0.25)
            ax.fill_between(df['time'], 50, 150, color=colour_dict['aurora_orange'], alpha=0.25)
            ax.fill_between(df['time'], 150, 200, color=colour_dict['aurora_red'], alpha=0.25)
            if df['state'].max() > 200:
                ax.fill_between(df['time'], 150, df['state'].max() * 1.2, color=colour_dict['aurora_purple'], alpha=0.25)
        if endpoint == 'sensor.first_air_quality_monitor_volatile_organic_compounds_index':
            friendly_name = "Indoor VOC Index"
            ax.set_ylim(df['state'].min() - 10 if df['state'].min() > 10 else 0, df['state'].max() + 10 if df['state'].max() < 90 else 100)
            ax.plot(df['time'], df['state'], label=f'{friendly_name} {unit}', color = colour_dict['frost_green'])
            ax.fill_between(df['time'], 0, 10, color=colour_dict['aurora_green'], alpha=0.25)
            ax.fill_between(df['time'], 10, 20, color=colour_dict['aurora_yellow'], alpha=0.25)
            ax.fill_between(df['time'], 20, 30, color=colour_dict['aurora_orange'], alpha=0.25)
            ax.fill_between(df['time'], 30, 60, color=colour_dict['aurora_red'], alpha=0.25)
            ax.fill_between(df['time'], 60, 100, color=colour_dict['aurora_purple'], alpha=0.25)
        if endpoint == 'sensor.first_air_quality_monitor_carbon_monoxide':
            friendly_name = "Indoor Carbon Monoxide"
            ax.set_ylim(0, df['state'].max() * 1.2 if df['state'].max() > 0 else 1)
            ax.bar(df['time'], df['state'], label=f'{friendly_name} {unit}', color=colour_dict['aurora_orange'], width=0.002)
            ax.fill_between(df['time'], 0, 5, color=colour_dict['aurora_green'], alpha=0.25)
            if df['state'].max() > 5:
                ax.fill_between(df['time'], 5, df['state'].max() * 1.2, color=colour_dict['aurora_purple'], alpha=0.25)
            if df['state'].iloc[-1] > 5:
                ax.text(0.5, 0.5, "High CO Levels, EVACUATE!!!", horizontalalignment='center', verticalalignment='center', transform=ax.transAxes, fontsize=15)
        if endpoint == 'sensor.first_air_quality_monitor_temperature':
            ax.set_ylim(df['state'].min() - 5, df['state'].max() + 5)
            ax.fill_between(df['time'], 0, 15, color=colour_dict['frost_dblue'], alpha=0.25)
            ax.fill_between(df['time'], 15, 20, color=colour_dict['frost_cyan'], alpha=0.25)
            ax.fill_between(df['time'], 20, 24, color=colour_dict['aurora_green'], alpha=0.25)
            ax.fill_between(df['time'], 24, 28, color=colour_dict['aurora_yellow'], alpha=0.25)
            ax.fill_between(df['time'], 28, 32, color=colour_dict['aurora_orange'], alpha=0.25)
            ax.fill_between(df['time'], 32, 36, color=colour_dict['aurora_red'], alpha=0.25)
            ax.fill_between(df['time'], 36, 50, color=colour_dict['aurora_purple'], alpha=0.25)
            ax.plot(df['time'], df['state'], label=f'{friendly_name} {unit}', color=colour_dict['aurora_orange'])
        if endpoint == 'sensor.first_air_quality_monitor_humidity':
            ax.set_ylim(df['state'].min() - 10, df['state'].max() + 10)
            ax.plot(df['time'], df['state'], label=f'{friendly_name} {unit}', color=colour_dict['aurora_green'])
            ax.fill_between(df['time'], 0, 20, color=colour_dict['aurora_red'],alpha=0.25)
            ax.fill_between(df['time'], 20, 30, color=colour_dict['aurora_yellow'],alpha=0.25)
            ax.fill_between(df['time'], 30, 40, color=colour_dict['aurora_green'],alpha=0.25)
            ax.fill_between(df['time'], 40, 50, color=colour_dict['frost_cyan'],alpha=0.25)
            ax.fill_between(df['time'], 50, 60, color=colour_dict['aurora_green'],alpha=0.25)
            ax.fill_between(df['time'], 60, 70, color=colour_dict['aurora_yellow'],alpha=0.25)
            ax.fill_between(df['time'], 70, 80, color=colour_dict['aurora_orange'],alpha=0.25)
            ax.fill_between(df['time'], 80, 90, color=colour_dict['aurora_red'],alpha=0.25)
            ax.fill_between(df['time'], 90, 200, color=colour_dict['aurora_purple'],alpha=0.25)
        ax.legend(**legend_kwargs)

    plt.tight_layout()
    buf = StringIO()
    fig.savefig(buf, format="svg", bbox_inches="tight", transparent=True)
    plt.close(fig)
    return buf.getvalue()

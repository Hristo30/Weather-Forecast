import requests
import pandas as pd
import random
from dash import Dash, html, dcc, Input, Output, State, no_update, callback_context
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import math

app = Dash(__name__)
server = app.server

# Weather Mapping
WEATHER_MAPPING = {
    # Clear
    0: ("Klarer Himmel", "KlarerHimmel.png", "clear", "light-text"),
    1: ("Überwiegend klar", "ÜberwiegendKlar.png", "clear", "light-text"),

    # Partly Cloudy
    2: ("Teilweise bewölkt", "TeilweiseBewölkt.png", "partly-cloudy", "light-text"),

    # Cloudy
    3: ("Bewölkt", "Bewölkt.png", "cloudy", "light-text"),

    # Foggy
    45: ("Nebel", "Nebel.png", "foggy", "dark-text"),
    48: ("Nebel mit Reif", "NebelMitReif.png", "foggy", "dark-text"),

    # Rain
    51: ("Leichter Nieselregen", "LeichterNieselregen.png", "rain", "light-text"),
    53: ("Mäßiger Nieselregen", "MäßigerNieselregen.png", "rain", "light-text"),
    55: ("Starker Nieselregen", "StarkerNieselregen.png", "rain", "light-text"),
    56: ("Leichter gefrierender Nieselregen", "LeichterNieselregen.png", "rain", "light-text"),
    57: ("Starker gefrierender Nieselregen", "StarkerNieselregen.png", "rain", "light-text"),
    61: ("Leichter Regen", "LeichterRegen.png", "rain", "light-text"),
    63: ("Mäßiger Regen", "MäßigerRegen.png", "rain", "light-text"),
    65: ("Starker Regen", "StarkerRegen.png", "rain", "light-text"),
    66: ("Leichter gefrierender Regen", "LeichterRegen.png", "rain", "light-text"),
    67: ("Starker gefrierender Regen", "StarkerRegen.png", "rain", "light-text"),
    80: ("Leichter Regenschauer", "LeichterRegenschauer.png", "rain", "light-text"),
    81: ("Mäßiger Regenschauer", "MäßigerRegenschauer.png", "rain", "light-text"),
    82: ("Heftiger Regenschauer", "HeftigerRegenschauer.png", "rain", "light-text"),

    # Snow
    71: ("Leichter Schneefall", "LeichterSchneefall.png", "snow", "dark-text"),
    73: ("Mäßiger Schneefall", "MäßigerSchneefall.png", "snow", "dark-text"),
    75: ("Starker Schneefall", "StarkerSchneefall.png", "snow", "dark-text"),
    77: ("Schneegriesel", "StarkerSchneefall.png", "snow", "dark-text"),
    85: ("Leichte Schneeschauer", "LeichterSchneefall.png", "snow", "dark-text"),
    86: ("Starke Schneeschauer", "StarkerSchneefall.png", "snow", "dark-text"),

    # Thunder
    95: ("Gewitter", "Gewitter.png", "thunder", "light-text"),
    96: ("Gewitter mit leichtem Hagel", "GewitterMitLeichtemHagel.png", "thunder", "light-text"),
    99: ("Gewitter mit starkem Hagel", "GewitterMitStarkemHagel.png", "thunder", "light-text"),
}

# Get Icons
def get_weather_info(code):
    return WEATHER_MAPPING.get(code, ("Unbekannt", "Unbekannt.png", "default", "light-text"))

def temperature_icon(temp):
    if temp < 5: return "cold_temp.png"
    if temp < 20: return "mild_temp.png"
    return "hot_temp.png"

def wind_speed_icon(speed):
    if speed < 10: return "low_wind.png"
    if speed < 20: return "mild_wind.png"
    if speed < 35: return "strong_wind.png"
    return "very_strong_wind.png"

# Wind Direction
def wind_direction_cardinal(degree):
    directions = ["N", "NO", "O", "SO", "S", "SW", "W", "NW"]
    direction_size = 360 / len(directions)

    index = round(degree / direction_size) % len(directions)
    return directions[index]


def create_wind_compass(wind_speed, wind_direction):
    display_direction = (wind_direction + 180) % 360
    angle = math.radians(display_direction)
    arrow_length = 26
    end_x = 50 + arrow_length * math.sin(angle)
    end_y = 50 - arrow_length * math.cos(angle)
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=[50], y=[50],
        mode='markers',
        marker=dict(
            size=95, 
            color='rgba(255, 71, 87, 0.08)', 
            line=dict(width=0)
        ),
        hoverinfo='skip',
        showlegend=False
    ))
    
    fig.add_trace(go.Scatter(
        x=[50], y=[50],
        mode='markers',
        marker=dict(
            size=85, 
            color='rgba(255,255,255,0.08)', 
            line=dict(width=2, color='rgba(255,255,255,0.25)')
        ),
        hoverinfo='skip',
        showlegend=False
    ))
    
    directions = ["S", "SO", "O", "NO", "N", "NW", "W", "SW"]
    angles = [0, 45, 90, 135, 180, 225, 270, 315]
    
    for dir_text, dir_angle in zip(directions, angles):
        rad = math.radians(dir_angle)
        radius = 58.5
        x = 50 + radius * math.sin(rad)
        y = 50 - radius * math.cos(rad)
        
        is_cardinal = dir_text in ["N", "O", "S", "W"]
        font_size = 15 if is_cardinal else 11
        
        fig.add_trace(go.Scatter(
            x=[x], y=[y],
            mode='text',
            text=dir_text,
            textfont=dict(
                size=font_size, 
                color='rgba(255,255,255,0.9)' if is_cardinal else 'rgba(255,255,255,0.6)',
                family='Arial, sans-serif',
                weight='bold' if is_cardinal else 'normal'
            ),
            hoverinfo='skip',
            showlegend=False
        ))
    
    head_length = 9
    head_angle = math.radians(30)
    
    line_end_factor = 0.96
    line_end_x = 50 + (arrow_length * line_end_factor) * math.sin(angle)
    line_end_y = 50 - (arrow_length * line_end_factor) * math.cos(angle)
    
    shadow_offset = 1.2
    fig.add_trace(go.Scatter(
        x=[50 + shadow_offset, line_end_x + shadow_offset], 
        y=[50 - shadow_offset, line_end_y - shadow_offset],
        mode='lines',
        line=dict(color='rgba(0,0,0,0.25)', width=3),
        hoverinfo='skip',
        showlegend=False
    ))
    
    fig.add_trace(go.Scatter(
        x=[50, line_end_x], y=[50, line_end_y],
        mode='lines',
        line=dict(color='#ff4757', width=3),
        hoverinfo='skip',
        showlegend=False
    ))
    
    fig.add_trace(go.Scatter(
        x=[50, line_end_x], y=[50, line_end_y],
        mode='lines',
        line=dict(color='rgba(255,255,255,0.3)', width=0.5),
        hoverinfo='skip',
        showlegend=False
    ))
    
    head_x1 = end_x - head_length * math.sin(angle - head_angle)
    head_y1 = end_y + head_length * math.cos(angle - head_angle)
    head_x2 = end_x - head_length * math.sin(angle + head_angle)
    head_y2 = end_y + head_length * math.cos(angle + head_angle)
    
    fig.add_trace(go.Scatter(
        x=[end_x + shadow_offset, head_x1 + shadow_offset, head_x2 + shadow_offset],
        y=[end_y - shadow_offset, head_y1 - shadow_offset, head_y2 - shadow_offset],
        mode='lines',
        fill='toself',
        fillcolor='rgba(0,0,0,0.25)',
        line=dict(color='rgba(0,0,0,0.25)', width=0),
        hoverinfo='skip',
        showlegend=False
    ))
    
    fig.add_trace(go.Scatter(
        x=[end_x, head_x1, head_x2],
        y=[end_y, head_y1, head_y2],
        mode='lines',
        fill='toself',
        fillcolor='#ff4757',
        line=dict(color='#ff4757', width=0),
        hoverinfo='skip',
        showlegend=False
    ))
    
    fig.add_trace(go.Scatter(
        x=[end_x, head_x1, head_x2, end_x],
        y=[end_y, head_y1, head_y2, end_y],
        mode='lines',
        line=dict(color='rgba(255,255,255,0.3)', width=1),
        hoverinfo='skip',
        showlegend=False
    ))
    
    fig.add_trace(go.Scatter(
        x=[50], y=[50],
        mode='markers',
        marker=dict(size=12, color='rgba(255,255,255,0.3)'),
        hoverinfo='skip',
        showlegend=False
    ))
    
    fig.add_trace(go.Scatter(
        x=[50], y=[50],
        mode='markers',
        marker=dict(size=8, color='white'),
        hoverinfo='skip',
        showlegend=False
    ))
    
    fig.update_layout(
        xaxis=dict(range=[-15, 115], visible=False, showgrid=False),
        yaxis=dict(range=[-15, 115], visible=False, showgrid=False, scaleanchor="x", scaleratio=1),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        width=120,
        height=120,
        margin=dict(l=0, r=0, t=0, b=0),
        hovermode=False,
        showlegend=False
    )
    
    return fig

# Data Fetching
def geocode_city(city_name):
    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": city_name, "countrycodes": "de", "format": "json", "limit": 1}
    headers = {"User-Agent": "WeatherDashboardStudentProject/1.0"}
    try:
        response = requests.get(url, params=params, headers=headers, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data:
                return (float(data[0]["lat"]), float(data[0]["lon"])), None
        return None, "Stadt nicht gefunden"
    except Exception as e:
        return None, "Verbindungsfehler"

def fetch_weather(lat, lon):
    try:
        url = (
            f"https://api.open-meteo.com/v1/forecast?"
            f"latitude={lat}&longitude={lon}"
            f"&current=temperature_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m,wind_direction_10m"
            f"&hourly=temperature_2m,precipitation"
            f"&daily=temperature_2m_max,temperature_2m_min,precipitation_sum,weather_code,sunrise,sunset"
            f"&timezone=Europe%2FBerlin"
        )
        response = requests.get(url, timeout=10)
        return response.json() if response.status_code == 200 else {}
    except:
        return {}

# UI Components
def build_forecast_cards(daily_df, city_name):
    if daily_df.empty or len(daily_df) < 7:
        return html.Div([], className="cards-container forecast-container")
    
    cards = []
    for i, row in daily_df.iloc[1:7].iterrows():
        time_obj = pd.to_datetime(row["time"]) if isinstance(row["time"], str) else row["time"]
        date_label = time_obj.strftime("%a %d.%m")
        weather_desc, icon_file, _, _ = get_weather_info(row.get("weather_code", 0))
        
        cards.append(html.Div([
            html.H4(date_label, className="card-title"),
            html.Img(src=f"/assets/{icon_file}", className="card-icon"),
            html.P(f"{round(row['temperature_2m_min'])}° / {round(row['temperature_2m_max'])}°", className="card-value")
        ], className="card card-animate forecast-card", style={"animationDelay": f"{0.4 + len(cards)*0.1}s"}))
    
    return html.Div(cards, className="cards-container forecast-container")

def build_sun_card(daily_df):
    if daily_df.empty or "sunrise" not in daily_df.columns or "sunset" not in daily_df.columns:
        return html.Div()

    sunrise = pd.to_datetime(daily_df.iloc[0]["sunrise"])
    sunset = pd.to_datetime(daily_df.iloc[0]["sunset"])

    if sunrise.tz is None:
        sunrise = sunrise.tz_localize("Europe/Berlin")
    else:
        sunrise = sunrise.tz_convert("Europe/Berlin")

    if sunset.tz is None:
        sunset = sunset.tz_localize("Europe/Berlin")
    else:
        sunset = sunset.tz_convert("Europe/Berlin")

    now = datetime.now(tz=sunrise.tz)
    is_night = now < sunrise or now > sunset

    day_length = sunset - sunrise
    night_length = pd.Timedelta(hours=24) - day_length

    if is_night:
        if now > sunset:
            progress = (now - sunset).total_seconds() / night_length.total_seconds()
        else:
            progress = (now - (sunset - pd.Timedelta(hours=24))).total_seconds() / night_length.total_seconds()
        title_text = "Mond"
        duration_display = f"{night_length.seconds // 3600} Std. {(night_length.seconds % 3600) // 60} Min."
        duration_label = "Nachtdauer"
        time1_value = sunset.strftime("%H:%M")
        time1_label = "Sonnenuntergang"
        time2_value = sunrise.strftime("%H:%M")
        time2_label = "Sonnenaufgang"
        arc_color = "#64748B"
        celestial_color = "#CBD5E0"
        glow_color = "#94A3B8"
    else:
        progress = (now - sunrise).total_seconds() / day_length.total_seconds()
        title_text = "Sonne"
        duration_display = f"{day_length.seconds // 3600} Std. {(day_length.seconds % 3600) // 60} Min."
        duration_label = "Tageslänge"
        time1_value = sunrise.strftime("%H:%M")
        time1_label = "Sonnenaufgang"
        time2_value = sunset.strftime("%H:%M")
        time2_label = "Sonnenuntergang"
        
        if progress < 0.25:
            arc_color = "#FF8E53"
        elif progress < 0.5:
            arc_color = "#FFB84D"
        elif progress < 0.75:
            arc_color = "#FFA726"
        else:
            arc_color = "#C084FC"
        
        celestial_color = "#FFD700"
        glow_color = "#FFA500"

    progress = max(0, min(1, progress))

    cx, cy, r = 70, 0, 52
    width, height = 140, 100

    angles = [math.pi * i / 100 for i in range(101)]
    x_full = [cx + r * math.cos(a) for a in angles]
    y_full = [cy + r * math.sin(a) for a in angles]

    steps = int(progress * 100)
    prog_angles = [math.pi * i / 100 for i in range(steps + 1)]
    x_prog = [cx + r * math.cos(a) for a in prog_angles]
    y_prog = [cy + r * math.sin(a) for a in prog_angles]

    a = math.pi * progress
    celestial_x = cx + r * math.cos(a)
    celestial_y = cy + r * math.sin(a)

    fig = go.Figure()

    fig.add_trace(go.Scatter(x=x_full, y=y_full, mode="lines",
                             line=dict(color="rgba(255,255,255,0.18)", width=9),
                             hoverinfo="skip", showlegend=False))

    fig.add_trace(go.Scatter(x=x_prog, y=y_prog, mode="lines",
                             line=dict(color=arc_color, width=9),
                             hoverinfo="skip", showlegend=False))

    fig.add_trace(go.Scatter(x=[celestial_x], y=[celestial_y], mode="markers",
                             marker=dict(size=42, color=glow_color, opacity=0.4),
                             hoverinfo="skip", showlegend=False))

    fig.add_trace(go.Scatter(x=[celestial_x], y=[celestial_y], mode="markers",
                             marker=dict(size=32, color=celestial_color),
                             hoverinfo="skip", showlegend=False))

    fig.update_layout(
        xaxis=dict(range=[0, width], visible=False),
        yaxis=dict(range=[0, height], visible=False, scaleanchor="x", scaleratio=1),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        width=width,
        height=height,
        margin=dict(l=0, r=0, t=10, b=0),
        hovermode=False,
        showlegend=False
    )

    return html.Div([

        html.H3(title_text, className="card-title"),
        
        dcc.Graph(
            figure=fig,
            config={"displayModeBar": False},
            className="sun-moon-graph"
        ),
   
        html.P(duration_display, className="card-value", style={"margin": "10px 0 4px 0"}),
        html.P(duration_label, className="card-subtitle", style={"margin": "0 0 20px 0"}),
        
        html.Div(style={"flexGrow": "1"}),
        
        html.Div([
            html.Div([
                html.Div(time1_value, className="sun-time-value"),
                html.Div(time1_label, className="sun-time-label")
            ], className="sun-time-item"),
            
            html.Div([
                html.Div(time2_value, className="sun-time-value"),
                html.Div(time2_label, className="sun-time-label")
            ], className="sun-time-item")
        ], className="sun-times-container")
        
    ], className="card card-animate", 
       style={
           "animationDelay": "0.4s",
           "display": "flex",
           "flexDirection": "column",
           "height": "380px",
           "justifyContent": "flex-start",
        
       })


# Animation Components
def create_rain_drops():
    drops = []
    for i in range(120):
        style = {
            'left': f'{random.uniform(-5, 105)}%',
            'top': f'{random.uniform(-100, 0)}px',
            'height': f'{random.uniform(20, 50)}px',
            'width': f'{random.uniform(1, 2)}px',
            'opacity': 0.6 * random.uniform(0.8, 1.2),
            'animationDelay': f'{random.uniform(0, 2)}s',
            'animationDuration': f'{random.uniform(1.5, 3)}s'
        }
        drops.append(html.Div(className="rain-drop", style=style))
    return drops, {'display': 'block', 'transition': 'opacity 1s ease'}

def create_snow_flakes():
    layers = []
    for layer in range(3):
        speed_factor = 1 + layer * 0.6
        size_factor = 0.6 + layer * 0.4
        duration = 60 / speed_factor
        
        flakes = []
        for i in range(50):
            style = {
                "left": f"{random.uniform(-10, 110)}%",
                "top": f"{random.uniform(0, 100)}vh",
                "fontSize": f"{random.uniform(12, 24) * size_factor}px",
                "opacity": random.uniform(0.7, 1.0),
                "--sway-distance": f"{random.uniform(30, 80)}px",
                "--sway-duration": f"{random.uniform(3,7)}s",
                "--rotation-speed": f"{random.uniform(8,20)}s"
            }
            flakes.append(html.Div(className="snowflake", style=style))
            flakes.append(html.Div(className="snowflake", style={**style, "top": f"{float(style['top'][:-2]) + 100}vh"}))
        
        layers.append(html.Div(className="snow-layer", style={"--fall-duration": f"{duration}s"}, children=flakes))
    return layers, {"display": "block"}

def create_clouds(is_partly_cloudy):
    layers = []
    count = 10 if is_partly_cloudy else 20
    base_opacity = 0.85 if is_partly_cloudy else 0.95
    base_width = 200 if is_partly_cloudy else 250
    base_height = 80 if is_partly_cloudy else 100
    
    for layer in range(3):
        scale = 1 - layer * 0.2
        duration = 60 + layer * 30
        
        clouds = []
        for _ in range(count):
            style = {
                'left': f'{random.uniform(0, 100)}vw',
                'top': f'{random.uniform(10, 80 + layer * 10)}vh',
                'width': f'{random.uniform(base_width * scale * 0.7, base_width * scale * 1.3)}px',
                'height': f'{random.uniform(base_height * scale * 0.8, base_height * scale * 1.2)}px',
                'opacity': random.uniform(base_opacity * 0.8, base_opacity * 1.2),
                'filter': f'blur({1 + layer * 0.5}px)'
            }
            clouds.append(html.Div(className="cloud", style=style))
            clouds.append(html.Div(className="cloud", style={**style, 'left': f'{float(style["left"][:-2]) + 100}vw'}))
        
        layers.append(html.Div(className="cloud-layer", style={'--scroll-duration': f'{duration}s'}, children=clouds))
    return layers, {'display': 'block', 'transition': 'opacity 1s ease'}

def create_thunder():
    layers = []
    for layer in range(4):
        scale = 1 - layer * 0.2
        containers = []
        
        for _ in range(12):
            style = {
                'left': f'{random.uniform(0, 100)}vw',
                'top': f'{random.uniform(10, 50 + layer * 15)}vh',
                'width': f'{random.uniform(280 * scale * 0.7, 280 * scale * 1.3)}px',
                'height': f'{random.uniform(110 * scale * 0.8, 110 * scale * 1.2)}px'
            }
            
            content = [html.Div(className="thunder-cloud", style={'width': '100%', 'height': '100%', 'opacity': random.uniform(0.85, 1.0), 'filter': f'blur({2 + layer}px)'})]
            
            if random.random() < 0.15:
                lightning_style = {
                    '--bolt-height': f'{random.uniform(20, 35)}vh',
                    '--skew': f'{random.choice([-8, -5, 0, 5, 8])}deg',
                    '--flash-duration': f'{random.uniform(3, 5)}s',
                    '--flash-delay': f'{random.uniform(0, 20)}s'
                }
                content.append(html.Div(className="cloud-lightning", children=[
                    html.Div(className="lightning-bolt", style=lightning_style),
                    html.Div(className="cloud-glow", style={'--flash-duration': lightning_style['--flash-duration'], '--flash-delay': lightning_style['--flash-delay']})
                ]))
            
            containers.append(html.Div(className="thunder-cloud-container", style=style, children=content))
            containers.append(html.Div(className="thunder-cloud-container", style={**style, 'left': f'{float(style["left"][:-2]) + 100}vw'}, children=content))
        
        layers.append(html.Div(className="thunder-layer", style={'--scroll-duration': '120s'}, children=containers))
    return layers, {"display": "block"}

# Layout
app.layout = html.Div([
    html.Div(id="rain-container", className="rain-container"),
    html.Div(id="snow-container", className="snow-container"),
    html.Div(id="clouds-container", className="clouds-container"),
    html.Div(id="thunder-container", className="thunder-container"),
    
    html.Div([
        html.Div([
            html.H1("Wetterdashboard Deutschland", className="main-title"),
            html.Div([
                html.P([
                    html.Span(f"{datetime.now().strftime('%A, %d. %B %Y')}", className="current-date"),
                    html.Span(" | ", id="city-separator", className="date-separator", style={"display": "none"}),
                    html.Span(id="selected-city-display", className="city-name")
                ], className="date-city-combined")
            ], className="date-city-container"),
        ], className="title-card fade-in"),
        html.Div([
            html.Label("Stadt eingeben", className="input-label"),
            dcc.Input(id="city-input", type="text", placeholder="z. B. Berlin, Hamburg, München …", debounce=True, className="city-input", value="Berlin"),
        ], className="input-container fade-in"),
        html.Div(id="status-message", className="status-message"),
        html.Div(id="current-weather", className="cards-container"),
        html.Div([
            html.Button("Heute", id="btn-today", n_clicks=0, className="view-btn"),
            html.Button("7 Tage", id="btn-7days", n_clicks=0, className="view-btn active")
        ], className="buttons-container"),
        html.Div([
            html.Div(dcc.Graph(id="temp-hourly", config={'displayModeBar': False}), className="graph-card slide-up"),
            html.Div(dcc.Graph(id="precip-hourly", config={'displayModeBar': False}), className="graph-card slide-up")
        ], id="hourly-graphs-container", className="hourly-graphs", style={'display': 'none'}),

    ], className="content-wrapper"),

   html.Div([
        html.Button("Test Default", id="btn-test-0", n_clicks=0, style={"fontSize": "12px"}),
        html.Button("Test Clear", id="btn-test-1", n_clicks=0, style={"fontSize": "12px"}),
        html.Button("Test Partly Cloudy", id="btn-test-2", n_clicks=0, style={"fontSize": "12px"}),
        html.Button("Test Cloudy", id="btn-test-3", n_clicks=0, style={"fontSize": "12px"}),
        html.Button("Test Foggy", id="btn-test-4", n_clicks=0, style={"fontSize": "12px"}),
        html.Button("Test Rain", id="btn-test-5", n_clicks=0, style={"fontSize": "12px"}),
        html.Button("Test Snow", id="btn-test-6", n_clicks=0, style={"fontSize": "12px"}),
        html.Button("Test Thunder", id="btn-test-7", n_clicks=0, style={"fontSize": "12px"}),
        html.Button("Stop Test", id="btn-stop-test", n_clicks=0, style={"fontSize": "12px"}),
    ], style={"position": "fixed", "bottom": "10px", "left": "0", "width": "100%", "display": "flex", "justifyContent": "center", "gap": "10px", "opacity": "0.5", "zIndex": "1000"}),

    dcc.Store(id="temp-view-store", data="7days"),
    dcc.Store(id="test-weather-store", data={"active": False, "index": 0}),
], id="main-container", className="weather-bg default light-text")

@app.callback(
    Output("rain-container", "children"), Output("rain-container", "style"),
    Output("snow-container", "children"), Output("snow-container", "style"),
    Output("clouds-container", "children"), Output("clouds-container", "style"),
    Output("thunder-container", "children"), Output("thunder-container", "style"),
    Input("main-container", "className")
)

def update_weather_animation(container_class):
    rain_drops, rain_style = ([], {"display": "none"})
    snow_flakes, snow_style = ([], {"display": "none"})
    clouds_children, clouds_style = ([], {"display": "none"})
    thunder_children, thunder_style = ([], {"display": "none"})

    if "rain" in container_class:
        rain_drops, rain_style = create_rain_drops()
    if "snow" in container_class:
        snow_flakes, snow_style = create_snow_flakes()
    if "partly-cloudy" in container_class:
        clouds_children, clouds_style = create_clouds(True)
    elif "cloudy" in container_class:
        clouds_children, clouds_style = create_clouds(False)
    if "thunder" in container_class:
        thunder_children, thunder_style = create_thunder()

    return (rain_drops, rain_style, snow_flakes, snow_style, clouds_children, clouds_style, thunder_children, thunder_style)

@app.callback(
    Output("test-weather-store", "data"),
    [Input(f"btn-test-{i}", "n_clicks") for i in range(8)] + [Input("btn-stop-test", "n_clicks")],
    prevent_initial_call=True
)
def update_test_mode(*n_clicks):
    ctx = callback_context
    if not ctx.triggered:
        return no_update
    triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]
    if triggered_id == "btn-stop-test":
        return {"active": False, "index": 0}
    try:
        index = int(triggered_id.split("-")[-1])
        return {"active": True, "index": index}
    except:
        return no_update

@app.callback(
    Output("status-message", "children"),
    Output("selected-city-display", "children"),
    Output("city-separator", "style"),
    Output("current-weather", "children"),
    Output("temp-hourly", "figure"),
    Output("precip-hourly", "figure"),
    Output("btn-today", "className"),
    Output("btn-7days", "className"),
    Output("temp-view-store", "data"),
    Output("main-container", "className"),
    Output("hourly-graphs-container", "style"),
    Input("city-input", "value"),
    Input("btn-today", "n_clicks"),
    Input("btn-7days", "n_clicks"),
    Input("test-weather-store", "data"),
    State("temp-view-store", "data")
)
def update_dashboard(city_name, n_today, n_7days, test_store, current_view):
    ctx = callback_context
    triggered_id = ctx.triggered[0]["prop_id"].split(".")[0] if ctx.triggered else None

    if triggered_id == "btn-today":
        view = "today"
    elif triggered_id == "btn-7days":
        view = "7days"
    else:
        view = current_view or "7days"

    empty_fig = go.Figure().update_layout(
        paper_bgcolor="rgba(0,0,0,0)", 
        plot_bgcolor="rgba(0,0,0,0)", 
        xaxis_visible=False, 
        yaxis_visible=False
    )

    if test_store.get("active", False):
        idx = test_store.get("index", 0)
        conditions = [
            ("default", "light-text"), ("clear", "light-text"), ("partly-cloudy", "light-text"),
            ("cloudy", "light-text"), ("foggy", "dark-text"), ("rain", "light-text"),
            ("snow", "dark-text"), ("thunder", "light-text")
        ]
        bg_class, text_class = conditions[idx]

        temp = 12
        apparent = 10
        wind = 15
        wind_dir = 225  # SW
        wind_cardinal = wind_direction_cardinal(wind_dir)
        wind_compass = create_wind_compass(wind, wind_dir)
        desc = "Test Wetter"
        icon = "ÜberwiegendKlar.png"
        sun_card = html.Div()

        cards = html.Div([
            html.Div([
                html.H3("Temperatur", className="card-title"),
                html.Img(src=f"/assets/{temperature_icon(temp)}", className="card-icon"),
                html.P(f"{temp} °C", className="card-value"),
                html.P(f"Gefühlt: {apparent} °C", className="feels-like")
            ], className="card card-animate", style={"animationDelay": "0.1s"}),

            html.Div([
                html.H3("Windgeschwindigkeit", className="card-title"),
                html.Div([
                    html.Div([html.Img(src=f"/assets/{wind_speed_icon(wind)}", className="card-icon wind-speed-icon")], className="wind-icon-wrapper"),
                    html.Div([dcc.Graph(figure=wind_compass, config={'displayModeBar': False})], className="wind-compass-wrapper")
                ], className="wind-icons-container"),
                html.P(f"{wind} km/h", className="card-value")
            ], className="card card-animate wind-card-content", style={"animationDelay": "0.2s"}),

            html.Div([
                html.H3("Wetterlage", className="card-title"),
                html.Img(src=f"/assets/{icon}", className="card-icon"),
                html.P(desc, className="card-value")
            ], className="card card-animate", style={"animationDelay": "0.3s"}),

            sun_card
        ], className="cards-container")

        return (
            "Test Modus aktiv", 
            "Test Stadt", 
            {"display": "inline"}, 
            html.Div([cards, html.Div()]), 
            empty_fig, empty_fig,
            "view-btn", "view-btn active", 
            view, 
            f"weather-bg {bg_class} {text_class}",
            {"display": "none"}
        )

    if not city_name or not city_name.strip():
        return (
            "", "", {"display": "none"}, html.Div(), 
            empty_fig, empty_fig, 
            "view-btn", "view-btn active", 
            view, 
            "weather-bg default light-text",
            {"display": "none"}
        )

    city_name = city_name.strip()
    coords, error = geocode_city(city_name)
    if error:
        return (
            error, "", {"display": "none"}, html.Div(), 
            no_update, no_update, 
            "view-btn", "view-btn active", 
            view, 
            "weather-bg default light-text",
            {"display": "none"}
        )

    lat, lon = coords
    data = fetch_weather(lat, lon)
    if not data or "current" not in data:
        return (
            "Wetterdaten nicht verfügbar", 
            "", 
            {"display": "none"}, 
            html.Div(), 
            no_update, 
            no_update, 
            "view-btn", 
            "view-btn active", 
            view, 
            "weather-bg default light-text",
            {"display": "none"}
        )

    current = data["current"]
    temp = round(current.get("temperature_2m", 0))
    apparent = round(current.get("apparent_temperature", temp), 1)
    wind = round(current.get("wind_speed_10m", 0))
    wind_dir = current.get("wind_direction_10m", 0)
    code = current.get("weather_code", 0)

    wind_cardinal = wind_direction_cardinal(wind_dir)
    wind_compass = create_wind_compass(wind, wind_dir)

    desc, icon, bg_class, text_class = get_weather_info(code)
    city_label = f"Wetterdaten für: {city_name.capitalize()}"

    daily_df = pd.DataFrame(data.get("daily", {}))
    if not daily_df.empty and "time" in daily_df.columns:
        daily_df["time"] = pd.to_datetime(daily_df["time"])

    sun_card = build_sun_card(daily_df)
    forecast_cards = build_forecast_cards(daily_df, city_name)

    cards = html.Div([
        html.Div([
            html.H3("Temperatur", className="card-title"),
            html.Img(src=f"/assets/{temperature_icon(temp)}", className="card-icon"),
            html.P(f"{temp} °C", className="card-value"),
            html.P(f"Gefühlt: {apparent} °C", className="feels-like")
        ], className="card card-animate", style={"animationDelay": "0.1s"}),

        html.Div([
            html.H3("Windgeschwindigkeit", className="card-title"),
            html.Div([
                html.Div([html.Img(src=f"/assets/{wind_speed_icon(wind)}", className="card-icon wind-speed-icon")], className="wind-icon-wrapper"),
                html.Div([dcc.Graph(figure=wind_compass, config={'displayModeBar': False}, style={'width': '100px', 'height': '100px'})], className="wind-compass-wrapper")
            ], className="wind-icons-container"),
            html.P(f"{wind} km/h", className="card-value")
        ], className="card card-animate", style={"animationDelay": "0.2s"}),

        html.Div([
            html.H3("Wetterlage", className="card-title"),
            html.Img(src=f"/assets/{icon}", className="card-icon"),
            html.P(desc, className="card-value")
        ], className="card card-animate", style={"animationDelay": "0.3s"}),

        sun_card
    ], className="cards-container")

    # Hourly graphs
    hourly_df = pd.DataFrame(data.get("hourly", {}))
    if not hourly_df.empty and "time" in hourly_df.columns:
        hourly_df["time"] = pd.to_datetime(hourly_df["time"])
        today_date = pd.Timestamp.now().date()
        today_hourly = hourly_df[hourly_df["time"].dt.date == today_date]

        temp_data = today_hourly if view == "today" else hourly_df
        precip_data = today_hourly if view == "today" else hourly_df
        view_label = "Heute" if view == "today" else "7 Tage"
    else:
        temp_data = pd.DataFrame()
        precip_data = pd.DataFrame()
        view_label = "Keine Daten"

    is_dark = text_class == "dark-text"
    template = "plotly_white" if is_dark else "plotly_dark"
    font_color = "#1a1a1a" if is_dark else "#ffffff"
    grid_color = "rgba(0,0,0,0.25)" if is_dark else "rgba(255,255,255,0.3)"

    if not temp_data.empty and "temperature_2m" in temp_data.columns:
        temp_fig = px.line(temp_data, x="time", y="temperature_2m")
        temp_fig.update_traces(line=dict(color="#ff6b6b", width=5), fill='tozeroy', fillcolor="rgba(255,107,107,0.15)")
        temp_fig.update_layout(
            title=f"<b>Temperaturverlauf - {view_label}</b>",
            yaxis_title="<b>Temperatur (°C)</b>",
            template=template,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(255,255,255,0.1)" if is_dark else "rgba(0,0,0,0.2)",
            font=dict(color=font_color, size=16),
            margin=dict(t=100, l=80, r=80, b=90),
            hovermode="x unified",
            xaxis=dict(showgrid=True, gridcolor=grid_color, gridwidth=2),
            yaxis=dict(showgrid=True, gridcolor=grid_color, gridwidth=2),
            title_font=dict(size=22, color=font_color)
        )
    else:
        temp_fig = empty_fig

    if not precip_data.empty and "precipitation" in precip_data.columns:
        precip_fig = px.bar(precip_data, x="time", y="precipitation")
        precip_fig.update_traces(marker_color="#45b7d1", opacity=0.85)
        precip_fig.update_layout(
            title=f"<b>Niederschlag - {view_label}</b>",
            yaxis_title="<b>Niederschlag (mm)</b>",
            template=template,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(255,255,255,0.1)" if is_dark else "rgba(0,0,0,0.2)",
            font=dict(color=font_color, size=16),
            margin=dict(t=100, l=80, r=80, b=90),
            hovermode="x unified",
            xaxis=dict(showgrid=True, gridcolor=grid_color, gridwidth=2),
            yaxis=dict(showgrid=True, gridcolor=grid_color, gridwidth=2),
            title_font=dict(size=22, color=font_color)
        )
    else:
        precip_fig = empty_fig

    today_class = "view-btn active" if view == "today" else "view-btn"
    seven_class = "view-btn active" if view == "7days" else "view-btn"

    return (
        "", 
        city_label, 
        {"display": "inline"}, 
        html.Div([cards, forecast_cards]), 
        temp_fig, precip_fig,
        today_class, seven_class, 
        view, 
        f"weather-bg {bg_class} {text_class}",
        {"display": "flex"}
    )

if __name__ == "__main__":
    import os
    app.run_server(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8050)),
        debug=False
    )

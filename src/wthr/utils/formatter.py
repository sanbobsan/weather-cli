from datetime import datetime
from typing import Literal

from rich import box
from rich.console import Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from wthr.models import CurrentForecast, DailyForecast, HourlyForecast, Weather

WEATHER_CODES: dict[int, tuple[str, str]] = {
    0: ("☀️", "Ясно"),
    1: ("🌤️", "Преимущественно ясно"),
    2: ("⛅", "Переменная облачность"),
    3: ("☁️", "Пасмурно"),
    45: ("🌫️", "Туман"),
    48: ("🌫️", "Иней"),
    51: ("🌦️", "Слабая морось"),
    53: ("🌦️", "Морось"),
    55: ("🌦️", "Плотная морось"),
    61: ("🌧️", "Слабый дождь"),
    63: ("🌧️", "Дождь"),
    65: ("🌧️", "Сильный дождь"),
    71: ("🌨️", "Слабый снег"),
    73: ("🌨️", "Снег"),
    75: ("🌨️", "Сильный снег"),
    77: ("❄️", "Снежные зерна"),
    80: ("🌦️", "Ливень"),
    81: ("🌧️", "Сильный ливень"),
    82: ("⛈️", "Очень сильный ливень"),
    95: ("⛈️", "Гроза"),
    96: ("⛈️", "Гроза с градом"),
    99: ("⛈️", "Сильная гроза с градом"),
}


# region utils


def get_weather_info(code: int) -> str:
    """Возвращает (эмодзи, описание) по коду погоды WMO"""
    return WEATHER_CODES.get(code, ("❓", "Неизвестно"))[1]


def format_datetime(dt: datetime | str, format_str: str = "%H:%M") -> str:
    """Форматирует datetime или ISO-строку"""
    if isinstance(dt, str):
        dt = datetime.fromisoformat(dt)
    return dt.strftime(format_str)


def get_temp_style(temp: float) -> str:
    """Возвращает стиль цвета для температуры"""
    if temp >= 30:
        return "bold red"
    elif temp >= 20:
        return "orange1"
    elif temp >= 10:
        return "yellow"
    elif temp >= 0:
        return "light_green"
    elif temp >= -10:
        return "cyan"
    else:
        return "bold cyan"


def colorize_temp(temp: float, temp_unit: Literal["C", "F"] = "C") -> str:
    """Возвращает температуру с цветовым стилем Rich markup"""
    style = get_temp_style(temp)
    return f"[{style}]{temp:.0f}°{temp_unit}[/]"


def get_weather_style(code: int) -> str:
    """Возвращает цвет описания погоды в зависимости от условий"""
    if code in (0, 1):  # Ясно
        return "yellow"
    elif code in (2, 3):  # Облачно
        return "grey69"
    elif code in (45, 48):  # Туман
        return "grey50"
    elif 50 <= code <= 67:  # Дождь
        return "bright_blue "
    elif 70 <= code <= 77:  # Снег
        return "cyan"
    elif code >= 95:  # Гроза
        return "magenta"
    else:
        return "white"


# endregion utils


def format_current(forecast: CurrentForecast) -> Panel:
    """Форматирует текущую погоду в панель"""
    desc = get_weather_info(forecast.weather_code)
    weather_style = get_weather_style(forecast.weather_code)

    time_str = format_datetime(forecast.time, "%H:%M")
    day_night = "День" if forecast.is_day == 1 else "Ночь"

    table = Table(show_header=False, box=None, padding=(0, 1))
    table.add_column("text", justify="right", style="grey62")
    table.add_column("value")
    # Время и период суток
    table.add_row(
        Text("Время", style="grey60"),
        Text(f"{time_str} ({day_night})", style="bold white"),
    )
    table.add_row()
    # Температура
    table.add_row(
        Text("Температура", style="grey60"), colorize_temp(forecast.temperature)
    )
    # Ощущаемая температура
    if forecast.apparent_temperature is not None:
        table.add_row(
            Text("Ощущается", style="grey60"),
            colorize_temp(forecast.apparent_temperature),
        )
    # Ветер
    wind_value = f"{forecast.wind_speed} м/с"
    if forecast.wind_direction is not None:
        wind_value += f" ({forecast.wind_direction}°)"
    table.add_row(Text("Ветер", style="grey60"), Text(wind_value, style="white"))
    # Влажность
    table.add_row(
        Text("Влажность", style="grey60"),
        Text(f"{forecast.relative_humidity}%", style="white"),
    )
    title_content = Group(Text(desc, style=weather_style), table)
    return Panel(
        title_content,
        title="📍 Текущая погода",
        title_align="left",
        border_style="grey50",
        padding=(1, 2),
        box=box.ROUNDED,
        expand=True,
    )


def format_daily(forecast: DailyForecast) -> Panel:
    """Форматирует прогноз на один день в панель"""
    desc = get_weather_info(forecast.weather_code)
    weather_style = get_weather_style(forecast.weather_code)

    day_name = format_datetime(forecast.time, "%A")
    date_str = format_datetime(forecast.time, "%d.%m.%Y")

    table = Table(show_header=False, box=None, padding=(0, 1))
    table.add_column("text", justify="right", style="grey62")
    table.add_column("value")
    # Дата
    table.add_row(
        Text("Дата", style="grey60"),
        Text(f"{day_name}, {date_str}", style="bold white"),
    )
    table.add_row()
    # Температуры
    table.add_row(
        Text("Минимальная", style="grey60"),
        colorize_temp(forecast.temperature_min),
    )
    table.add_row(
        Text("Максимальная", style="grey60"),
        colorize_temp(forecast.temperature_max),
    )
    # Ощущаемые температуры
    if forecast.apparent_temperature_min is not None:
        table.add_row(
            Text("Ощущается (мин)", style="grey60"),
            colorize_temp(forecast.apparent_temperature_min),
        )
    if forecast.apparent_temperature_max is not None:
        table.add_row(
            Text("Ощущается (макс)", style="grey60"),
            colorize_temp(forecast.apparent_temperature_max),
        )
    # Осадки
    precip_value = f"{forecast.precipitation_probability_max}%"
    if forecast.precipitation_sum is not None and forecast.precipitation_sum > 0:
        precip_value += f" ({forecast.precipitation_sum:.1f} мм)"
    table.add_row(
        Text("Осадки", style="grey60"),
        Text(
            precip_value,
            style="bright_blue " if forecast.precipitation_sum else "white",
        ),
    )
    # Ветер
    if forecast.wind_speed_max is not None:
        table.add_row(
            Text("Ветер (макс)", style="grey60"),
            Text(f"{forecast.wind_speed_max} м/с", style="white"),
        )
    # Солнце
    if forecast.sunrise and forecast.sunset:
        sunrise_str = format_datetime(forecast.sunrise, "%H:%M")
        sunset_str = format_datetime(forecast.sunset, "%H:%M")
        table.add_row(
            Text("Солнце", style="grey60"),
            Text(f"{sunrise_str} — {sunset_str}", style="yellow"),
        )
    title_content = Group(Text(desc, style=weather_style), table)
    return Panel(
        title_content,
        title=f"📅 {date_str}",
        title_align="left",
        border_style="grey50",
        padding=(1, 2),
        box=box.ROUNDED,
        expand=True,
    )


def format_hourly(forecasts: list[HourlyForecast], limit: int = 12) -> Panel:
    """Форматирует почасовой прогноз"""
    table = Table(show_header=True, header_style="bold cyan", box=None, padding=(0, 1))
    table.add_column("Время", justify="center", style="grey62", width=8)
    table.add_column("Погода", justify="center", width=20)
    table.add_column("Темп", justify="right", width=10)
    table.add_column("Ветер", justify="right", width=10)
    table.add_column("Влажность", justify="right", width=10)
    table.add_column("Осадки", justify="right", width=10)

    items = forecasts[:limit]
    for hour in items:
        desc = get_weather_info(hour.weather_code)
        weather_style = get_weather_style(hour.weather_code)
        time_str = format_datetime(hour.time, "%H:%M")
        # Ветер
        wind_value = f"{hour.wind_speed} м/с" if hour.wind_speed is not None else "—"
        # Влажность
        humidity_value = (
            f"{hour.relative_humidity}%" if hour.relative_humidity is not None else "—"
        )
        # Осадки
        precip_value = (
            f"{hour.precipitation_probability}%"
            if hour.precipitation_probability is not None
            else "—"
        )
        table.add_row(
            Text(time_str, style="bold white"),
            Text(desc, style=weather_style),
            colorize_temp(hour.temperature),
            Text(wind_value, style="white"),
            Text(humidity_value, style="white"),
            Text(precip_value, style="white"),
        )

    return Panel(
        table,
        title="⏰ Почасовой прогноз",
        title_align="left",
        border_style="grey50",
        padding=(1, 2),
        box=box.ROUNDED,
        expand=True,
    )


def format_weather(
    weather: Weather,
    show_daily: int | None = None,
    show_hourly: int | None = None,
) -> list[Panel]:
    """Собирает полный отчет о погоде"""
    output: list[Panel] = []
    # Заголовок с названием города
    output.append(
        Panel(
            Text(weather.location_display_name, style="bold white"),
            title="🌐",
            title_align="left",
            border_style="grey50",
            box=box.ROUNDED,
            expand=True,
        )
    )
    # Текущая погода
    if weather.current:
        output.append(format_current(weather.current))
    # Прогноз по дням
    if weather.daily and show_daily and show_daily > 0:
        for day in weather.daily[:show_daily]:
            output.append(format_daily(day))
    # Почасовой прогноз
    if weather.hourly and show_hourly and show_hourly > 0:
        output.append(format_hourly(weather.hourly, limit=show_hourly))
    return output

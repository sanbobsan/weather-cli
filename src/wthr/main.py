from typing import Annotated, Optional

import typer
from rich import box, print
from rich.panel import Panel

from wthr.api import LocationNotFoundError, WeatherAPIClient
from wthr.models import ForecastType
from wthr.utils import format_weather, config_storage

app = typer.Typer()


@app.callback(invoke_without_command=True)
def default(ctx: typer.Context):
    if not ctx.invoked_subcommand:
        weather()


@app.command("weather")
def weather(
    location: Annotated[
        str, typer.Argument(help="Место, где нужно узнать погоду")
    ] = "",
    d: Annotated[
        bool,
        typer.Option(
            "-d",
            help="Показать прогноз по дням",
        ),
    ] = False,
    days: Annotated[
        Optional[int],
        typer.Option(
            "--days",
            metavar="[days]",
            help="Указать количество дней, обычно 4",
        ),
    ] = None,
    h: Annotated[
        bool,
        typer.Option(
            "-h",
            help="Показать почасовой прогноз",
        ),
    ] = False,
    hours: Annotated[
        Optional[int],
        typer.Option(
            "--hours",
            metavar="[hours]",
            help="Указать количество часов, обычно 12",
        ),
    ] = None,
    mixed: Annotated[
        bool,
        typer.Option(
            "--mixed",
            "-m",
            help="Показать все 3 типа прогноза",
        ),
    ] = False,
) -> None:
    """
    Показать прогноз погоды для указанного места.

    Есть 3 типа прогноза:
      1. Текущая погода (по умолчанию) — температура, ветер, влажность сейчас.
      2. Прогноз по дням (-d, --days) — мин/макс температура, осадки, солнце.
      3. Почасовой прогноз (-h, --hours) — температура и условия на ближайшие часы.

    Если не указать тип прогноза, будет показана только текущая погода.
    Если указать флаг -h, но не указывать --hours, то будет показан почасовой прогноз на 12 часов.
    Если указать флаг -d, но не указывать --days, то будет показан почасовой прогноз на 4 дня.
    Если указать --hours или --days, то можно не указывать -h или -d соответственно.
    Если указать и --days (-d) и --hours (-h) или флаг --mixed, то будут показаны все 3 типа одновременно.

    Примеры:

      # Текущая погода в Москве
      $ weather-cli weather Москва

      # Прогноз на 4 дня
      $ weather-cli weather Москва --days 12

      # Почасовой прогноз на 12 часов (по умолчанию)
      $ weather-cli weather Москва -h

      # Все типы прогноза сразу
      $ weather-cli weather Москва --mixed

      # Интерактивный запрос места (если не указано)
      $ weather-cli weather
    """
    if not location:
        if loc := config_storage.get_default_location():
            location = loc
        else:
            while not location:
                location = str(typer.prompt("Укажите место")).strip()
            print()

    if not any([mixed, d, days, h, hours]):
        type: ForecastType = ForecastType.CURRENT
    elif mixed or ((d or days) and (h or hours)):
        type = ForecastType.MIXED
        if not days:
            days = 4
        if not hours:
            hours = 12
    elif d or days:
        type = ForecastType.DAILY
        if not days:
            days = 4
    elif h or hours:
        type = ForecastType.HOURLY
        if not hours:
            hours = 12

    with WeatherAPIClient() as client:
        try:
            location_ = client.get_location(location)
        except LocationNotFoundError:
            panel = Panel(
                f"Локация '{location}' не найдена",
                border_style="grey50",
                padding=(0, 2),
                box=box.ROUNDED,
                expand=False,
            )
            print(panel)
            return

        weather = client.get_weather(
            location=location_,
            forecast_type=type,
            days=days,
            hours=hours,
        )

    print(
        *format_weather(
            weather=weather,
            show_daily=days,
            show_hourly=hours,
        )
    )


@app.command("set")
def set(
    location: Annotated[
        str, typer.Argument(help="Место, где нужно узнать погоду")
    ] = "",
) -> None:
    """Сохранить место в конфиг, чтобы в дальнейшем автоматически использовать его для получения погоды"""
    if not location:
        while not location:
            location = str(typer.prompt("Укажите место")).strip()
        print()

    config_storage.set_default_location(location)
    typer.echo(f'Ваше место: "{location}" сохранена в конфиг')


@app.command("get")
def get() -> None:
    """Проверить текущее место в конфиге"""
    location = config_storage.get_default_location()
    if location:
        text = f"Ваше место: {location}"
    else:
        text = "Ваше место не указано"
    panel = Panel(
        text,
        border_style="grey50",
        padding=(0, 2),
        box=box.ROUNDED,
        expand=False,
    )
    print(panel)


@app.command("clear")
def clear() -> None:
    """Удалить конфиг"""
    config_storage.clear()
    text = "Конфиг удален"
    panel = Panel(
        text,
        border_style="grey50",
        padding=(0, 2),
        box=box.ROUNDED,
        expand=False,
    )
    print(panel)


if __name__ == "__main__":
    app()

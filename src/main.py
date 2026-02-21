from typing import Annotated

import typer

app = typer.Typer()


@app.command("weather")
def weather(
    location: Annotated[
        str, typer.Argument(help="Место, где нужно узнать погоду")
    ] = "",
) -> None:
    """Показать погоду"""
    if not location:
        location = typer.prompt("Укажите место")
    typer.echo(f"Это погода для {location}!")


@app.command("set")
def set(
    location: Annotated[
        str, typer.Argument(help="Место, где нужно узнать погоду")
    ] = "",
) -> None:
    """Запомнить место"""
    if not location:
        location = typer.prompt("Укажите место для сохранения")
    typer.echo(f"Локация {location} сохранена!")


if __name__ == "__main__":
    app()

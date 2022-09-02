import click

from onx import settings


def validate_winning_length(ctx, _, value):
    if ("grid_size" in ctx.params and value > ctx.params["grid_size"]) or (
        "grid_size" not in ctx.params and value > settings.DEFAULT_GRID_SIZE
    ):
        raise click.BadParameter(
            "winning-length have to be less or equal to --grid-size"
        )


@click.command(context_settings=dict(help_option_names=["-h", "--help"]))
@click.option("-d", "--daemon", is_flag=True, help="Run server.")
@click.option(
    "-g",
    "--grid-size",
    help=f"Grid size = {settings.DEFAULT_GRID_SIZE} by default.",
    default=settings.DEFAULT_GRID_SIZE,
    type=click.IntRange(min=settings.DEFAULT_GRID_SIZE, max=14),
)
@click.option(
    "-w",
    "--winning-length",
    help=f"Winning sequence length = {settings.DEFAULT_WINNING_LENGTH} by default.",
    default=settings.DEFAULT_WINNING_LENGTH,
    type=click.IntRange(min=settings.DEFAULT_WINNING_LENGTH, max=5),
    callback=validate_winning_length,
)
def main(daemon: bool, grid_size: int, winning_length: int) -> None:
    """
    Noughts & Crosses game. Client and server command.
    """
    if daemon:
        from onx.server.event_loop import run_event_loop

        run_event_loop()
    else:
        from onx.tui.app import GameApp
        from onx import __version__

        GameApp.run(
            title=f"Noughts & Crosses v{__version__}",
            grid_size=grid_size,
            winning_length=winning_length,
        )


if __name__ == "__main__":
    main()

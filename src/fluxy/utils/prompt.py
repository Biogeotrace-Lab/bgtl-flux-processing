import click


_CONFIRMATION_FORMAT = " [y/N]: "


def confirm_or_abort(msg: str) -> bool:
    """Return True if possitive user input, Abort otherwise.
    """
    if input(click.style(msg + _CONFIRMATION_FORMAT,
                         bold=True)).lower() == "y":
        return True

    raise click.Abort()


def confirm(msg: str) -> bool:
    """Return True if possitive user input, False otherwise.
    """
    if input(click.style(msg + _CONFIRMATION_FORMAT,
                         bold=True)).lower() == "y":
        return True

    return False

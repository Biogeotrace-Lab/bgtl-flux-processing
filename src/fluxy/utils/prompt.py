import click


def prompt_yes_or_abort(msg: str) -> bool:
    """Return True if possitive user input, Abort otherwise.
    """
    if input(click.style(msg + " y/n: ", bold=True)) == "y":
        return True

    raise click.Abort()


def prompt_yes_or_false(msg: str) -> bool:
    """Return True if possitive user input, False otherwise.
    """
    if input(click.style(msg + " y/n: ", bold=True)) == "y":
        return True

    return False

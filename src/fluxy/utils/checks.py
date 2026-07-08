import click

tick = chr(0x2714)
ballot = chr(0x2718)

def passes_check_report(msg: str, passing_condition: bool) -> bool:
    """Construct a check report line according to a condition of
    pass or fail.
    """
    color = "bright_green"
    report_msg = f"{msg} {tick}"

    if not passing_condition:
        color = "bright_red"
        report_msg = f"{msg} {ballot}"

    click.secho(report_msg, fg=color)
    return passing_condition

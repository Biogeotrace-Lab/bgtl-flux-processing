import click
import sys

tick = chr(0x2714)
ballot = chr(0x2718)


STATUS = {
    True: ('bright_green', 'Pass', tick),
    False: ('bright_red', 'Fail', ballot)
}


# This should be designed to be an autonomous binary gate. Like the confirmation
# or abort prompts. If it passes, cool. If not, report and exit.
def passes_quality_check(msg: str, passing_condition: bool,
                         error_message: str = ''):
    """Construct a check report line according to a condition of
    pass or fail.
    """
    color, result, mark = STATUS[passing_condition]
    report_msg = f"Check - {msg}; {result} {mark}"

    click.secho(report_msg, fg=color)
    
    if not passing_condition:
        click.echo(error_message)
        raise click.Abort()


class QualityControl:
    status = STATUS.copy()

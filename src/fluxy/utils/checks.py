import click
import sys


from rich.table import Table
from rich.console import Console
from rich.text import Text


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
    """QualityControl class

    It collects quality control checks and reports back with the corresponding
    error code. Can be used as a context manager.
    """
    STATUS = {True: f"Pass {tick}", False: f"Fail {ballot}"}
    CONSOLE = Console()

    def __init__(self) -> None:
        self.error_code = 0
        self._checks_count = 0
        self.table = Table(title="Quality Control Report", title_style="bold")
        self.table.add_column("Checks", justify="right")
        self.table.add_column("Description")
        self.table.add_column("Status")
        self.table.add_column("Comments")
        self._id_generator = (str(i) for i in range(1, 10000))

    def _format_status(self, passes: bool):
        return self.STATUS[passes]

    def generate_new_id(self):
        return next(self._id_generator)

    def add_check(self, check_title: str,
                  pass_condition: bool,
                  failure_msg: str) -> None:
        self.table.add_row(self.generate_new_id(),
                           check_title,
                           self._format_status(pass_condition),
                           failure_msg if not pass_condition else '',
                           style="bright_green" if pass_condition
                           else "bright_red")
        # Flip errors code if failure.
        self.error_code |= not pass_condition

    def report(self) -> int:
        """Construct the report to stdout and return `error_code`.
        
        :returns error_code: 0 if control passes; 1 if control fails.
        :rtype: int
        """
        self.CONSOLE.print(self.table)
        return self.error_code

    def report_and_exit(self):
        self.report()
        sys.exit(self.error_code)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        if exc_type is not None:
            click.echo(
                "\n" +
                click.style("Attention: ", bold=True) +
                "Quality control was interrupted due to error "
                f"'{exc}' at line {tb.tb_lineno}" +
                "\n")
    
            if self.table.title is not None:
                self.table.title += " (Partial)"

        self.report_and_exit()

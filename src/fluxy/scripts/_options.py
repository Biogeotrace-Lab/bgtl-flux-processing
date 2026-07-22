import click


class CommandWithMutuallyExclusiveOptions(click.Command):
    def __init__(self, *args, **kwargs) -> None:
        self.mutex = set(kwargs.pop("mutex", []))
        super().__init__(*args, **kwargs)

    def parse_args(self, ctx: click.Context, args: list[str]) -> list[str]:
        intersection = self.mutex.intersection(set(args))
        if len(intersection) > 1:
            ctx.fail(f"Options {intersection} cannot be used together.")
        
        if not args:
            ctx.fail(ctx.get_help())

        return super().parse_args(ctx, args)

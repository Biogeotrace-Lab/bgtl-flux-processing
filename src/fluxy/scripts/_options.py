import click


class CommaSeparatedList(click.ParamType):
    name = "comma_list"
    def __init__(self, type: type = str) -> None:
        super().__init__()
        self.type = type
    
    def convert(self, value, param, ctx):
        # Handle default or already-parsed list values
        if isinstance(value, (list, tuple)):
            return value

        if value is None:
            return tuple()

        try:
            # Split by comma and strip extra whitespace
            return list(self.type(item.strip()) for item in value.split(",") if item.strip())
        except AttributeError:
            self.fail(f"'{value}' could not be parsed as a comma-separated list.", param, ctx)


class CommandWithMutuallyExclusiveOptions(click.Command):
    def __init__(self, *args, **kwargs) -> None:
        self.mutex = set(kwargs.pop("mutex", []))
        super().__init__(*args, **kwargs)

    def parse_args(self, ctx: click.Context, args: list[str]) -> list[str]:
        if ctx.resilient_parsing:
            return super().parse_args(ctx, args)

        intersection = self.mutex.intersection(set(args))
        if len(intersection) > 1:
            ctx.fail(f"Options {intersection} cannot be used together.")
        
        if not args:
            ctx.fail(ctx.get_help())

        return super().parse_args(ctx, args)

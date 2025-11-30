"""Discord cog for team management commands."""

# pyright: reportUnknownLambdaType=false

import logging

from discord.ext import commands

from app.mediator import Mediator
from app.usecases.result import UseCaseError
from app.usecases.teams.create_team import CreateTeamCommand
from app.usecases.teams.get_team import GetTeamQuery

logger = logging.getLogger(__name__)


class TeamsCog(commands.Cog, name="Teams"):
    """Discord commands for team management."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.group(name="teams")
    async def teams(self, ctx: commands.Context[commands.Bot]) -> None:
        """Team management commands."""
        if ctx.invoked_subcommand is None:
            await ctx.send(
                "Error: missing option. Use !teams get <id> or !teams create <name>"
            )

    @teams.command(name="get")
    async def teams_get(
        self,
        ctx: commands.Context[commands.Bot],
        team_id: str,
    ) -> None:
        """Get team by ID. Usage: !teams get <team_id>"""
        query = GetTeamQuery(team_id=team_id)

        message = await (
            Mediator.send_async(query)
            .map(  # type: ignore[arg-type, return-value]  # pyright: ignore[reportUnknownLambdaType]
                lambda value: (
                    f"Team Information:\nID: {value.team.id}\nName: {value.team.name}"
                )
            )
            .unwrap()
        )

        await ctx.send(content=message)

    @teams.command(name="create")
    async def teams_create(
        self,
        ctx: commands.Context[commands.Bot],
        name: str,
    ) -> None:
        """Create new team. Usage: !teams create <name>"""
        message = await (
            Mediator.send_async(CreateTeamCommand(name=name))
            .and_then(  # type: ignore[arg-type, return-value]
                lambda result: Mediator.send_async(GetTeamQuery(result.team_id))
            )
            .map(  # type: ignore[arg-type, return-value]
                lambda value: (
                    f"Team Created:\nID: {value.team.id}\nName: {value.team.name}"
                )
            )
            .unwrap()
        )

        await ctx.send(content=message)

    @teams_get.error
    async def teams_get_error(
        self, ctx: commands.Context[commands.Bot], error: commands.CommandError
    ) -> None:
        """Handle errors for teams get command."""
        # Unwrap CommandInvokeError to get the actual exception
        if isinstance(error, commands.CommandInvokeError) and error.original:
            original_error = error.original
        else:
            original_error = error

        # Handle application errors (UseCaseError)
        if isinstance(original_error, UseCaseError):
            logger.error(
                "Use case error in teams get: %s",
                original_error.message,
                exc_info=True,
            )
            await ctx.send(f"Error: {original_error.message}")
        # Handle Discord framework errors
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(
                "Error: Missing required argument. Usage: !teams get <team_id>"
            )
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Error: Invalid argument provided.")
        else:
            # Catch-all for unexpected errors
            logger.error(
                "Unexpected error in teams get command: %s", error, exc_info=True
            )
            await ctx.send(f"Error: {error}")

    @teams_create.error
    async def teams_create_error(
        self, ctx: commands.Context[commands.Bot], error: commands.CommandError
    ) -> None:
        """Handle errors for teams create command."""
        # Unwrap CommandInvokeError to get the actual exception
        if isinstance(error, commands.CommandInvokeError) and error.original:
            original_error = error.original
        else:
            original_error = error

        # Handle application errors (UseCaseError)
        if isinstance(original_error, UseCaseError):
            logger.error(
                "Use case error in teams create: %s",
                original_error.message,
                exc_info=True,
            )
            await ctx.send(f"Error: {original_error.message}")
        # Handle Discord framework errors
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(
                "Error: Missing required argument. Usage: !teams create <name>"
            )
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Error: Invalid argument provided.")
        else:
            # Catch-all for unexpected errors
            logger.error(
                "Unexpected error in teams create command: %s", error, exc_info=True
            )
            await ctx.send(f"Error: {error}")


async def setup(bot: commands.Bot) -> None:
    """Setup function for cog loading."""
    await bot.add_cog(TeamsCog(bot))

"""Discord cog for team management commands."""

import logging

from discord.ext import commands

from app.core.result import Err, Ok
from app.mediator import Mediator
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
        result = await Mediator.send_async(query)

        match result:
            case Ok(ok_value):
                message = (
                    f"Team Information:\n"
                    f"ID: {ok_value.team.id}\n"
                    f"Name: {ok_value.team.name}"
                )
                await ctx.send(content=message)
            case Err(err_value):
                logger.error("Failed to get team: %s", err_value.message)
                await ctx.send(f"Error: {err_value.message}")

    @teams.command(name="create")
    async def teams_create(
        self,
        ctx: commands.Context[commands.Bot],
        name: str,
    ) -> None:
        """Create new team. Usage: !teams create <name>"""
        command = CreateTeamCommand(name=name)
        result = await Mediator.send_async(command)

        match result:
            case Ok(ok_value):
                message = (
                    f"Team Created:\nID: {ok_value.team.id}\nName: {ok_value.team.name}"
                )
                await ctx.send(content=message)
            case Err(err_value):
                logger.error("Failed to create team: %s", err_value.message)
                await ctx.send(f"Error: {err_value.message}")


async def setup(bot: commands.Bot) -> None:
    """Setup function for cog loading."""
    await bot.add_cog(TeamsCog(bot))

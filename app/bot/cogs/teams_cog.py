"""Discord cog for team management commands."""

# pyright: reportUnknownLambdaType=false

from discord.ext import commands

from app.bot.cogs.base_cog import BaseCog
from app.mediator import Mediator
from app.usecases.teams.create_team import CreateTeamCommand
from app.usecases.teams.get_team import GetTeamQuery
from app.usecases.teams.update_team import UpdateTeamCommand


class TeamsCog(BaseCog, name="Teams"):
    """Discord commands for team management."""

    @commands.group(name="teams")
    async def teams(self, ctx: commands.Context[commands.Bot]) -> None:
        """Team management commands."""
        if ctx.invoked_subcommand is None:
            if ctx.command:
                await ctx.send_help(ctx.command)

    @teams.command(name="get")
    async def teams_get(
        self,
        ctx: commands.Context[commands.Bot],
        id: str,
    ) -> None:
        """Get team by ID. Usage: !teams get <team_id>"""
        query = GetTeamQuery(id=id)

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
                lambda result: Mediator.send_async(GetTeamQuery(id=result.id))
            )
            .map(  # type: ignore[arg-type, return-value]
                lambda value: (
                    f"Team Created:\nID: {value.team.id}\nName: {value.team.name}"
                )
            )
            .unwrap()
        )

        await ctx.send(content=message)

    @teams.command(name="update")
    async def teams_update(
        self,
        ctx: commands.Context[commands.Bot],
        team_id: str,
        *,
        new_name: str,
    ) -> None:
        """Update team name. Usage: !teams update <team_id> <new_name>"""
        message = await (
            Mediator.send_async(UpdateTeamCommand(team_id=team_id, new_name=new_name))
            .and_then(  # type: ignore[arg-type, return-value]
                lambda result: Mediator.send_async(GetTeamQuery(id=result.id))
            )
            .map(  # type: ignore[arg-type, return-value]
                lambda value: (
                    f"Team Updated Successfully:\n"
                    f"ID: {value.team.id}\n"
                    f"Name: {value.team.name}\n"
                    f"Version: {value.team.version}"
                )
            )
            .unwrap()
        )

        await ctx.send(content=message)


async def setup(bot: commands.Bot) -> None:
    """Setup function for cog loading."""
    await bot.add_cog(TeamsCog(bot))

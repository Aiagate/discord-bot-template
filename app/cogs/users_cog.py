"""Discord cog for user management commands."""

import logging

from discord.ext import commands

from app.core.result import Err, Ok
from app.mediator import Mediator
from app.usecases.users.create_user import CreateUserCommand
from app.usecases.users.get_user import GetUserQuery

logger = logging.getLogger(__name__)


class UsersCog(commands.Cog, name="Users"):
    """Discord commands for user management."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.group(name="users")
    async def users(self, ctx: commands.Context[commands.Bot]) -> None:
        """User management commands."""
        if ctx.invoked_subcommand is None:
            await ctx.send(
                "Error: missing option. Use !users get <id> or !users create <name> <email>"
            )

    @users.command(name="get")
    async def users_get(
        self,
        ctx: commands.Context[commands.Bot],
        user_id: str,
    ) -> None:
        """Get user by ID. Usage: !users get <user_id>"""
        query = GetUserQuery(user_id=user_id)
        result = await Mediator.send_async(query)

        match result:
            case Ok(ok_value):
                message = (
                    f"User Information:\n"
                    f"ID: {ok_value.user.id}\n"
                    f"Name: {ok_value.user.name}\n"
                    f"Email: {ok_value.user.email}"
                )
                await ctx.send(content=message)
            case Err(err_value):
                logger.error("Failed to get user: %s", err_value.message)
                await ctx.send(f"Error: {err_value.message}")

    @users.command(name="create")
    async def users_create(
        self,
        ctx: commands.Context[commands.Bot],
        name: str,
        email: str,
    ) -> None:
        """Create new user. Usage: !users create <name> <email>"""
        command = CreateUserCommand(name=name, email=email)
        result = await Mediator.send_async(command)

        match result:
            case Ok(ok_value):
                user_id = ok_value.user_id
                query = GetUserQuery(user_id=user_id)
                get_result = await Mediator.send_async(query)

                match get_result:
                    case Ok(get_ok_value):
                        message = (
                            f"User Created:\n"
                            f"ID: {get_ok_value.user.id}\n"
                            f"Name: {get_ok_value.user.name}\n"
                            f"Email: {get_ok_value.user.email}"
                        )
                        await ctx.send(content=message)
                    case Err(get_err_value):
                        logger.error(
                            "Failed to get created user: %s", get_err_value.message
                        )
                        await ctx.send(f"Error: {get_err_value.message}")
            case Err(err_value):
                logger.error("Failed to create user: %s", err_value.message)
                await ctx.send(f"Error: {err_value.message}")


async def setup(bot: commands.Bot) -> None:
    """Setup function for cog loading."""
    await bot.add_cog(UsersCog(bot))

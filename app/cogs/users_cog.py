# pyright: reportUnknownLambdaType=false

"""Discord cog for user management commands."""

import logging

from discord.ext import commands

from app.mediator import Mediator
from app.usecases.result import UseCaseError
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

        message = await (
            Mediator.send_async(query)
            .map(
                lambda value: (
                    f"User Information:\n"
                    f"ID: {value.user.id}\n"
                    f"Name: {value.user.name}\n"
                    f"Email: {value.user.email}"
                )
            )
            .unwrap()
        )

        await ctx.send(content=message)

    @users.command(name="create")
    async def users_create(
        self,
        ctx: commands.Context[commands.Bot],
        name: str,
        email: str,
    ) -> None:
        """Create new user. Usage: !users create <name> <email>"""
        message = await (
            Mediator.send_async(CreateUserCommand(name=name, email=email))
            .and_then(lambda result: Mediator.send_async(GetUserQuery(result.user_id)))
            .map(
                lambda value: (
                    f"User Created:\n"
                    f"ID: {value.user.id}\n"
                    f"Name: {value.user.name}\n"
                    f"Email: {value.user.email}"
                )
            )
            .unwrap()
        )

        await ctx.send(content=message)

    @users_get.error
    async def users_get_error(
        self, ctx: commands.Context[commands.Bot], error: commands.CommandError
    ) -> None:
        """Handle errors for users get command."""
        # Unwrap CommandInvokeError to get the actual exception
        if isinstance(error, commands.CommandInvokeError) and error.original:
            original_error = error.original
        else:
            original_error = error

        # Handle application errors (UseCaseError)
        if isinstance(original_error, UseCaseError):
            logger.error(
                "Use case error in users get: %s",
                original_error.message,
                exc_info=True,
            )
            await ctx.send(f"Error: {original_error.message}")
        # Handle Discord framework errors
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(
                "Error: Missing required argument. Usage: !users get <user_id>"
            )
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Error: Invalid argument provided.")
        else:
            # Catch-all for unexpected errors
            logger.error(
                "Unexpected error in users get command: %s", error, exc_info=True
            )
            await ctx.send(f"Error: {error}")

    @users_create.error
    async def users_create_error(
        self, ctx: commands.Context[commands.Bot], error: commands.CommandError
    ) -> None:
        """Handle errors for users create command."""
        # Unwrap CommandInvokeError to get the actual exception
        if isinstance(error, commands.CommandInvokeError) and error.original:
            original_error = error.original
        else:
            original_error = error

        # Handle application errors (UseCaseError)
        if isinstance(original_error, UseCaseError):
            logger.error(
                "Use case error in users create: %s",
                original_error.message,
                exc_info=True,
            )
            await ctx.send(f"Error: {original_error.message}")
        # Handle Discord framework errors
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(
                "Error: Missing required argument. Usage: !users create <name> <email>"
            )
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Error: Invalid argument provided.")
        else:
            # Catch-all for unexpected errors
            logger.error(
                "Unexpected error in users create command: %s", error, exc_info=True
            )
            await ctx.send(f"Error: {error}")


async def setup(bot: commands.Bot) -> None:
    """Setup function for cog loading."""
    await bot.add_cog(UsersCog(bot))

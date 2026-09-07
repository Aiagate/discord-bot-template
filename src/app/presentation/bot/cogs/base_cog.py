# pyright: reportUnknownLambdaType=false
"""Base cog with common error handling."""

import logging
from typing import Any

from discord.ext import commands

from app.application.mediator import ApplicationMediator
from app.usecases.result import UseCaseError

logger = logging.getLogger(__name__)


class BaseCog(commands.Cog):
    """Base cog with common error handling."""

    def __init__(self, bot: commands.Bot, mediator: ApplicationMediator) -> None:
        self.bot = bot
        self.mediator = mediator

    async def cog_command_error(
        self, ctx: commands.Context[Any], error: Exception
    ) -> None:
        """Global error handler for all commands in this cog."""
        original_error = getattr(error, "original", error)
        command_name = ctx.command.qualified_name if ctx.command else "unknown command"

        if isinstance(original_error, UseCaseError):
            logger.warning(
                "Use case error in %s: %s",
                command_name,
                original_error.message,
            )
            await ctx.send(f"Error: {original_error.display_message}")
        elif isinstance(
            error, (commands.MissingRequiredArgument, commands.BadArgument)
        ):
            if ctx.command:
                await ctx.send_help(ctx.command)
        else:
            logger.error(
                "Unexpected error in %s.", command_name, exc_info=original_error
            )
            await ctx.send("An unexpected error occurred. Please try again later.")

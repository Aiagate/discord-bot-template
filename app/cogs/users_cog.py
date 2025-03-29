from di_test import GetUserQuery
from discord.ext import commands
from mediator import Mediator


class UsersCog(commands.Cog, name="Users"):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.group(name="users")
    async def users(self, ctx: commands.Context) -> None:
        if ctx.invoked_subcommand is None:
            await ctx.send("Error: missing option")

    @users.command(name="get")
    async def users_get(self, ctx: commands.Context) -> None:
        query = GetUserQuery(user_id=1, order_id=100)
        result = await Mediator.send_async(query)
        message = (
            f"Get user information {result.user} and order information {result.order}"
        )
        await ctx.send(content=message)


def setup(bot: commands.Bot) -> None:
    return bot.add_cog(UsersCog(bot))

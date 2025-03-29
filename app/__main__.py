#! .venv/bin/python


import discord
from cogs import users_cog
from discord.ext import commands


class MyBot(commands.Bot):
    def __init__(self) -> None:
        super().__init__(intents=discord.Intents.all(), command_prefix="!")

    async def setup_hook(self) -> None:
        """起動時に Cog をロードする"""
        await self.load_cogs()

    async def load_cogs(self) -> None:
        await self.load_extension(users_cog.__name__)
        # cogs = ["cogs.users_cog"]
        # for cog in cogs:
        #     await self.load_extension(cog)


bot = MyBot()
bot.run("YOUR_BOT_TOKEN")

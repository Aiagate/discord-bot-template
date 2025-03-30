#! .venv/bin/python


import logging

import discord
from cogs import users_cog
from discord.ext import commands


class MyBot(commands.Bot):
    def __init__(self, command_prefix: str = "!") -> None:
        super().__init__(intents=discord.Intents.all(), command_prefix=command_prefix)

    async def setup_hook(self) -> None:
        await self.load_cogs()

    async def load_cogs(self) -> None:
        await self.load_extension(users_cog.__name__)


logging.basicConfig(
    level=logging.DEBUG,
    format="[ %(levelname)-8s] %(asctime)s | %(name)-16s %(funcName)-16s| %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
bot = MyBot()
bot.run("YOUR_TOKEN")

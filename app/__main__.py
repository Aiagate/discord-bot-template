#! .venv/bin/python


import discord
from discord.ext import commands


class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(intents=discord.Intents.all(), command_prefix="!")

    async def setup_hook(self):
        """起動時に Cog をロードする"""
        await self.load_cogs()

    async def load_cogs(self):
        cogs = -["app.cogs.test_cog"]
        for cog in cogs:
            await self.load_extension(cog)

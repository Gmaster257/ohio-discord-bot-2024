import sys
import os

sys.path.append('/home/zhchen/ohio-discord-bot-2024')

print(f"Current directory: {os.getcwd()}")
print(f"Python executable: {sys.executable}")
print(f"Python version: {sys.version}")
print(f"Python path: {sys.path}")

import config
import discord
from discord.ext import commands
import random

#Init Bot Settings
intents = discord.Intents.all()

class OHIOBot(commands.Bot):
    async def setup_hook(self):
        #Log cogs
        await self.load_extension('cogs.verify')
        await self.load_extension('cogs.teams')

    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')

    async def on_command_error(self, interaction: discord.Interaction, error: commands.CommandError) -> None:
        if isinstance(error, commands.CheckFailure):
            await interaction.response.send_message(
                content=(
                    "You do not have permission to run this command."
                    "If you think this is a mistake, please contact server admins."
                ), 
                ephemeral=True)
        else:
            await interaction.response.send_message("An error occurred. Please try again later or contact server admins.")

bot = OHIOBot(command_prefix='!', intents=intents)





def start():
    bot.run(config.discord_token, reconnect=True)

if __name__ == "__main__":
    start()
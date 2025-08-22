import config
import discord
from discord.ext import commands
import logging
from utils.logger import setup_logging

#Init Bot Settings
intents = discord.Intents.all()

setup_logging()
logger = logging.getLogger('bot')

class OHIOBot(commands.Bot):
    async def setup_hook(self):
        self.logger = logger
        #Log cogs
        await self.load_extension('cogs.verify')
        await self.load_extension('cogs.teams')
        await self.load_extension('cogs.admin')
        await self.load_extension('cogs.fun')

    async def on_error(self, interaction: discord.Interaction, error: discord.app_commands.AppCommandError) -> None:
        if isinstance(error, commands.CheckFailure):
            await interaction.response.send_message(
                content=(
                    "You do not have permission to run this command."
                    "If you think this is a mistake, please contact server admins."
                ), 
                ephemeral=True)
        else:
            await interaction.response.send_message(
                content="An error occurred. Please try again later or contact server admins.",
                ephemeral=True)
            print(error)

    async def on_ready(self):
        self.logger.info(f'Logged in as {self.user} (ID: {self.user.id})')

bot = OHIOBot(command_prefix='!', intents=intents)

def start():
    bot.run(config.discord_token, reconnect=True)

if __name__ == "__main__":
    start()
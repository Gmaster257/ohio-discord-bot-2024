import core.records as records
import config
import discord
from discord import app_commands
from discord.ext import commands, tasks
import asyncio
import random

class FunCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = bot.logger
        self.logger.info(f'FunCog initialized with {bot.user}')

    @app_commands.command(name='affirm', description="Recieve a random affirmation for encouragement")
    async def affirm(self, interaction: discord.Interaction):
        affirmations = {
            "You're doing amazing—every line of code is one step closer to something great!",
            "Remember, the best solutions often come from the toughest challenges. Keep going!",
            "You belong here. Your ideas matter and are worth sharing.",
            "It's not about having all the answers; it's about asking the right questions. You're doing great!",
            "Every bug you squash is a step closer to innovation. Keep debugging!",
            "Your creativity is your superpower. Let it shine!",
            "It's okay to take breaks. Rest fuels brilliance.",
            "You’re capable of more than you realize—trust the process.",
            "Collaboration is key, and you're an invaluable part of your team!",
            "Progress, not perfection, is the goal. You're moving forward, and that's what counts.",
            "Hackathons are marathons, not sprints. Pace yourself and enjoy the journey!",
            "Remember, even the greatest projects started with a single idea. Keep building!",
            "You’re not alone; your teammates and community are here to support you.",
            "Every keystroke is an act of creativity. You're a digital artist!",
            "Challenges are opportunities in disguise. Embrace them and thrive!",
            "Your dedication inspires others. Keep up the amazing work!",
            "Celebrate small victories—they lead to big successes!",
            "Think outside the box. Your unique perspective is your advantage!",
            "You're making something out of nothing—that's incredible!",
            "No matter the outcome, you're learning, growing, and creating. That's a win!"
        }
        random_affirm = random.choice(list(affirmations))
        await interaction.response.send_message(ephemeral=True, content=f'{random_affirm}')

async def setup(bot) -> None:
    await bot.add_cog(FunCog(bot))
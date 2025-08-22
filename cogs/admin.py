import discord
from discord import app_commands
from discord.ext import commands, tasks

class AdminCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = bot.logger
        self.logger.info(f'AdminCog initialized with {bot.user}')

    @commands.command()
    @commands.guild_only()
    async def sync(self, ctx: commands.Context, guilds: commands.Greedy[discord.Object], spec = None) -> None:
        """
        `!sync` takes all global commands within the CommandTree and sends them to Discord. (see CommandTree for more info.)
        `!sync ~` will sync all guild commands for the current context’s guild.
        `!sync *` copies all global commands to the current guild (within the CommandTree) and syncs.
        `!sync ^` will remove all guild commands from the CommandTree and syncs, which effectively removes all commands from the guild.
        `!sync 123 456 789` will sync the 3 guild ids we passed: 123, 456 and 789. Only their guilds and guild-bound commands.
        """
        if not guilds:
            if spec == "~":
                synced = await ctx.bot.tree.sync(guild=ctx.guild)
            elif spec == "*":
                ctx.bot.tree.copy_global_to(guild=ctx.guild)
                synced = await ctx.bot.tree.sync(guild=ctx.guild)
            elif spec == "^":
                ctx.bot.tree.clear_commands(guild=ctx.guild)
                await ctx.bot.tree.sync(guild=ctx.guild)
                synced = []
            else:
                synced = await ctx.bot.tree.sync()

            await ctx.send(
                f"Synced {len(synced)} commands {'globally' if spec is None else 'to the current guild.'}"
            )
            self.logger.info(f"Synced {len(synced)} commands {'globally' if spec is None else 'to the current guild.'}")
            return

        ret = 0
        for guild in guilds:
            try:
                await ctx.bot.tree.sync(guild=guild)
            except discord.HTTPException:
                pass
            else:
                ret += 1

        await ctx.send(f"Synced the tree to {ret}/{len(guilds)}.")
        self.logger.info(f"Synced the tree to {ret}/{len(guilds)}.")

async def setup(bot) -> None:
    await bot.add_cog(AdminCog(bot))
    
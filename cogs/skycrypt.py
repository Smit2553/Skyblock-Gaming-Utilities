import discord
from discord.ext import commands


class SkyCrypt(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @discord.slash_command(description="Get SkyCrypt stats for a player.")
    async def skycrypt(self, ctx
                       , username: discord.Option(discord.SlashCommandOptionType.string, "Minecraft Username", required=True)):
        await ctx.respond(f"https://sky.shiiyu.moe/stats/{username}")


def setup(bot):
    bot.add_cog(SkyCrypt(bot))

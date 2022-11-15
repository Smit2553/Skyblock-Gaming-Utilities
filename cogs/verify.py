import os
import requests
from discord.ext import commands
from discord import option
from cogs.minecraftfunctions import *


class Verify(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.slash_command(description="Adds a user to our verification system.")
    @option(
        name="minecraft_ign",
        description="Your Minecraft IGN"
    )
    async def verify(self, ctx, minecraft_ign=None):
        if minecraft_ign is None:
            embed = discord.Embed(
                title=":x: Error",
                description="Please provide a Minecraft IGN. \n Example: `-verify ObbyTrusty`",
                color=0xFF0000
            )
            await ctx.respond(embed=embed)
            return
        if minecraft_ign is None:
            embed = discord.Embed(title=f'Error', description='Please enter a user \n `-verify ObbyTrusty`',
                                  colour=0xFF0000)
            await ctx.respond(embed=embed)
            return
        tempvar = "Attempt to verify: " + str(ctx.author)
        print(tempvar)
        uuid = await ign_to_uuid(minecraft_ign)
        if type(uuid) is discord.Embed:
            await ctx.respond(embed=uuid)
            return
        else:
            uuid = uuid['id']
        async with aiosqlite.connect('database/SGdatabase.sqlite') as db:
            async with db.execute(f"SELECT * FROM sgutilsdb WHERE discord_id = ?", (ctx.author.id,)) as cursor:
                async for row in cursor:
                    if row is not None:
                        embed = discord.Embed(title=f'Error',
                                              description='You are already verified. Please use `/unverify` '
                                                          'before trying to reverify', colour=0xFF0000)
                        await ctx.respond(embed=embed)
                        return
                response = requests.get(f'https://api.hypixel.net/player?key={os.getenv("APIKEY")}&uuid={uuid}')
                if response.status_code != 200:
                    embed = discord.Embed(title=f'Error',
                                          description='Error fetching information from the API. Try again later',
                                          colour=0xFF0000)
                    await ctx.respond(embed=embed)
                    return
                player = response.json()
                try:
                    if player['player']['socialMedia']['links']['DISCORD'] == str(ctx.author):
                        pass
                    else:
                        embed = discord.Embed(title=f'Error',
                                              description='The discord linked with your hypixel account is not the same as '
                                                          'the one you are trying to verify with. \n You can connect your '
                                                          'discord following https://youtu.be/6ZXaZ-chzWI',
                                              colour=0xFF0000)
                        await ctx.respond(embed=embed)
                        return
                except KeyError:
                    embed = discord.Embed(title=f'Error',
                                          description='The discord linked with your hypixel account is not the same as '
                                                      'the one you are trying to verify with. \n You can connect your '
                                                      'discord following https://youtu.be/6ZXaZ-chzWI',
                                          colour=0xFF0000)
                    await ctx.respond(embed=embed)
                    return
                embed = discord.Embed(title=f'You are now verified!',
                                      description=f'Standard Verification Completed.',
                                      colour=0xee6940)
                embed.set_thumbnail(url=f'https://crafatar.com/renders/head/{uuid}')
                await ctx.respond(embed=embed)
                await db.execute(f"""INSERT INTO sgutilsdb VALUES ({ctx.author.id}, "{uuid}")""")
                await db.commit()

    @discord.slash_command(description='Removes user from our verification database')
    async def unverify(self, ctx):
        async with aiosqlite.connect('database/SGdatabase.sqlite') as db:
            await db.execute("DELETE FROM sgutilsdb WHERE discord_id = ?", (ctx.author.id,))
            await db.commit()
            embed = discord.Embed(title=f'Verification',
                                  description=f'You have been unverified.',
                                  colour=0x008000)
            await ctx.respond(embed=embed)
            return


def setup(bot):
    bot.add_cog(Verify(bot))

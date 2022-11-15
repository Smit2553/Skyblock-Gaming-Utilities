import discord
from discord.ext import commands
import requests
import requests_cache
from aiohttp_client_cache import CachedSession, SQLiteBackend
from discord.commands import SlashCommandGroup
from discord import option
import os
import aiosqlite


class GuildFeatures(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        requests_cache.install_cache('guild_cache', backend='sqlite', expire_after=300)

    guild = SlashCommandGroup("guild", "Hypixel Skyblock Guild Utilities")

    @guild.command(description="Link a guild to the server")
    @option(
        name="guild",
        description="Guild Name",
        required=True
    )
    @commands.has_permissions(administrator=True)
    async def link(self, ctx, guild):
        response = requests.get(f'https://api.hypixel.net/guild?key={os.getenv("APIKEY")}&name={guild}')
        if response.status_code != 200:
            embed = discord.Embed(title=f'Error',
                                  description='Error fetching information from the API. Try again later',
                                  colour=0xFF0000)
            await ctx.respond(embed=embed)
            return
        data = response.json()
        if data['success'] == False:
            embed = discord.Embed(title=f'Error',
                                  description='Error fetching information from the API. Try again later',
                                  colour=0xFF0000)
            await ctx.respond(embed=embed)
            return
        if data['guild'] is None:
            embed = discord.Embed(title=f'Error',
                                  description='Guild does not exist.',
                                  colour=0xFF0000)
            await ctx.respond(embed=embed)
            return
        guilduuid = data['guild']['_id']
        guild = data['guild']['name']
        async with aiosqlite.connect('SGGuildDB.sqlite') as db:
            async with db.execute("SELECT * FROM sgguildutilsdb WHERE discord_guild_id = ?", (ctx.guild.id,)) as cursor:
                async for row in cursor:
                    if row is not None:
                        embed = discord.Embed(title=f'Error',
                                              description='A guild already linked to this server. \nUse `/guild unlink` to unlink '
                                                          'the '
                                                          'guild. If you are trying to link multiple guilds, please join the '
                                                          'support server in my About Me and wait for the '
                                                          'announcement stating '
                                                          'that this feature has been introduced.',
                                              colour=0xFF0000)
                        await ctx.respond(embed=embed)
                        return
                await db.execute(f'''INSERT INTO sgguildutilsdb VALUES (?, ?, ?)''', (ctx.guild.id, guilduuid, None))
                await db.commit()
                embed = discord.Embed(title=f'Guild Linked!',
                                      description=f'**{guild}** has been linked to this server.',
                                      colour=0xee6940)
                await ctx.respond(embed=embed)

    @guild.command(description="Unlink a guild from the server")
    @commands.has_permissions(administrator=True)
    async def unlink(self, ctx):
        async with aiosqlite.connect('SGGuildDB.sqlite') as db:
            async with db.execute("SELECT * FROM sgguildutilsdb WHERE discord_guild_id = ?", (ctx.guild.id,)) as cursor:
                async for row in cursor:
                    if row is not None:
                        await db.execute(f'''DELETE FROM sgguildutilsdb WHERE discord_guild_id = {ctx.guild.id}''')
                        await db.commit()
                        embed = discord.Embed(title=f'Guild Unlinked!',
                                              description=f'Guild has been unlinked from this server.',
                                              colour=0xee6940)
                        await ctx.respond(embed=embed)
                        return
                embed = discord.Embed(title=f'Error',
                                      description='No guild linked to this server. \nTo link a guild use `/guild link`',
                                      colour=0xFF0000)
                await ctx.respond(embed=embed)
                return

    @guild.command(description="Set or change a vc that displays the guild's member count")
    @option(
        name="channel",
        description="Channel to set",
        required=True,
        type=discord.VoiceChannel)
    @commands.has_permissions(administrator=True)
    async def setcountvc(self, ctx, channel):
        async with aiosqlite.connect('SGGuildDB.sqlite') as db:
            async with db.execute("SELECT * FROM sgguildutilsdb WHERE discord_guild_id = ?", (ctx.guild.id,)) as cursor:
                async for row in cursor:
                    if row is not None:
                        await db.execute(f'''UPDATE sgguildutilsdb SET member_count_channel = ? WHERE 
                        discord_guild_id = ?''', (channel.id, ctx.guild.id))
                        await db.commit()
                        embed = discord.Embed(title=f'Channel Set!',
                                              description=f'Channel has been set to {channel.mention}',
                                              colour=0xee6940)
                        await ctx.respond(embed=embed)
                        response = requests.get(f'https://api.hypixel.net/guild?key={os.getenv("APIKEY")}&id={row[1]}')
                        if response.status_code != 200:
                            return
                        data = response.json()

                        if data['success'] is False:
                            return
                        if data['guild'] is None:
                            return

                        await channel.edit(name=f'{data["guild"]["name"]} Members: {len(data["guild"]["members"])}')
                        print(f'Updated Voice for {ctx.guild}')
                        return
                embed = discord.Embed(title=f'Error',
                                      description='No guild linked to this server. \nTo link a guild use `/guild link`',
                                      colour=0xFF0000)
                await ctx.respond(embed=embed)
                return


def setup(bot):
    bot.add_cog(GuildFeatures(bot))

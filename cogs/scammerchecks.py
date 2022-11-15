import discord
from discord.ext import commands
import requests
from discord import option
import os
from dotenv import load_dotenv
from discord.commands import SlashCommandGroup
import requests_cache
import sqlite3
from functions import *
import aiosqlite
from aiohttp_client_cache import CachedSession, SQLiteBackend


class ScammerCheck(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        load_dotenv()
        requests_cache.install_cache('scammer_cache', backend='sqlite', expire_after=600)

    scammer = SlashCommandGroup("scammer", "Scammer checks for Hypixel Skyblock")

    @scammer.command(description="Check if a player is a scammer.")
    @option(
        name="player",
        description="Minecraft IGN",
        required=True
    )
    async def lookup(self, ctx, player):
        mojangresponse = await ign_to_uuid(player)
        if type(mojangresponse) is discord.Embed:
            await ctx.respond(embed=mojangresponse)
            return
        uuid = mojangresponse["id"]
        async with aiosqlite.connect('SGScammer.sqlite') as db:
            async with db.execute("SELECT * FROM sgscammerdb WHERE minecraftuuid = ? AND discord_guild_id = ?",
                                  (uuid, ctx.guild.id)) as cursor:
                async for row in cursor:
                    if row is not None:
                        embed = discord.Embed(title=f'Scammer Check',
                                              description=f'**{mojangresponse["name"]}** is a in the server specific '
                                                          f'blacklist. \n To remove them use /scammer '
                                                          f'whitelist', colour=0xFF0000)
                        embed.set_thumbnail(url=f'https://crafatar.com/renders/head/{uuid}')
                        await ctx.respond(embed=embed)
                        return
        async with CachedSession(cache=SQLiteBackend('ign_cache', expires_after=600)) as session:
            response = await session.get(f'https://skykings.net/api/lookup/?key={os.getenv("SKYKINGSKEY")}&uuid={uuid}')
            if response.status != 200:
                embed = discord.Embed(title=f'Error',
                                      description='Error fetching information from the API. Try again later',
                                      colour=0xFF0000)
                await ctx.respond(embed=embed)
                return
            data = await response.json()
            if not data['success']:
                embed = discord.Embed(title=f'Error',
                                      description='Error fetching information from the API. Try again later',
                                      colour=0xFF0000)
                await ctx.respond(embed=embed)
                return

            if not data['entries']:
                embed = discord.Embed(title=f'Not a Scammer!',
                                      description=f'**{mojangresponse["name"]}** is not a scammer! \n This does not '
                                                  f'mean this person is safe '
                                                  f'to trade with. Proceed with your own risk.',
                                      colour=0xee6940)
                embed.set_thumbnail(url=f'https://crafatar.com/renders/head/{uuid}')
                await ctx.respond(embed=embed)
                return
            for entry in data['entries']:
                embed = discord.Embed(title=f'Scammer!',
                                      description=f'**{mojangresponse["name"]}** is a scammer! \n This '
                                                  f'means this person is unsafe '
                                                  f'to trade with. Proceed with your own risk.',
                                      colour=0xFF0000)
                embed.set_thumbnail(url=f'https://crafatar.com/renders/head/{uuid}')
                embed.add_field(name="Reason", value=entry['reason'])
                await ctx.respond(embed=embed)
                return

    @scammer.command(description="Check if a guild has any scammers.")
    @option(
        name="guild",
        description="Guild Name",
        required=True
    )
    async def guild(self, ctx, guild):
        await ctx.defer()
        async with CachedSession(cache=SQLiteBackend('guild_cache', expires_after=600)) as session:
            response = await session.get(f'https://api.hypixel.net/guild?key={os.getenv("APIKEY")}&name={guild}')
            if response.status != 200:
                embed = discord.Embed(title=f'Error',
                                      description='Error fetching information from the API. Try again later',
                                      colour=0xFF0000)
                await ctx.respond(embed=embed)
                return
            data = await response.json()
            if not data['success']:
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
            guild = data['guild']['name']
            guildmembers = []
            scammercheck = False
            scammers = []
            reasons = []
            async with aiosqlite.connect('SGScammer.sqlite') as db:
                for member in data['guild']['members']:
                    async with db.execute("SELECT * FROM sgscammerdb WHERE minecraftuuid = ? AND discord_guild_id = ?",
                                          (member['uuid'], ctx.guild.id)) as cursor:
                        async for row in cursor:
                            if row is not None:
                                scammercheck = True
                                ign = await uuid_to_ign(member['uuid'])
                                if type(ign) is not discord.Embed:
                                    scammers.append(ign)
                                    reasons.append('Server Specific Blacklist')
                                else:
                                    scammers.append(f"{member['uuid']} (IGN not found)")
                                    reasons.append('Server Specific Blacklist')
                    if member['uuid'] in guildmembers:
                        continue
                    else:
                        guildmembers.append(member['uuid'])

            def divide_chunks(length, n):
                for i in range(0, len(length), n):
                    yield length[i:i + n]

            x = list(divide_chunks(guildmembers, 10))
            skykingsapi = os.getenv("SKYKINGSKEY")
            for chunks in x:
                lookupstring = ",".join(chunks)
                async with CachedSession(cache=SQLiteBackend('scammer_cache', expires_after=600)) as session:
                    response = await session.get(
                        f'https://skykings.net/api/lookup/bulk?key={skykingsapi}&uuids={lookupstring}')
                    if response.status != 200:
                        embed = discord.Embed(title=f'Error',
                                              description='Error fetching information from the API. Try again later',
                                              colour=0xFF0000)
                        await ctx.respond(embed=embed)
                        return
                    data = await response.json()
                    if not data['success']:
                        embed = discord.Embed(title=f'Error',
                                              description='Error fetching information from the API. Try again later',
                                              colour=0xFF0000)
                        await ctx.respond(embed=embed)
                        return
                    print(data)
                    if not data['entries']:
                        pass

                    else:
                        for scammer in data['entries']:
                            for player in scammer['players']:
                                if len(scammer) > 10:
                                    break
                                ign = await uuid_to_ign(player)
                                if type(ign) is not discord.Embed:
                                    scammers.append(ign)
                                    reasons.append(scammer['reason'])
                                scammercheck = True
            if not scammercheck:
                embed = discord.Embed(title=f'No Scammers!',
                                      description=f'**{guild}** has no scammers!',
                                      colour=0xee6940)
                await ctx.respond(embed=embed)
                return
            if scammercheck:
                embed = discord.Embed(title=f'Scammer(s)!',
                                      description=f'**{guild}** has scammers!',
                                      colour=0xFF0000)
                for i in range(len(scammers)):
                    if i <= 9:
                        embed.add_field(name=scammers[i], value=reasons[i], inline=False)
                    else:
                        embed.add_field(name='More Scammers!',
                                        value='This guild has more scammers! Unable to display all of them.',
                                        inline=False)
                await ctx.respond(embed=embed)
                return

    @scammer.command(description="Check if a discord user is a scammer.")
    @option(
        name="user",
        description="Discord User",
        required=True
    )
    async def user(self, ctx, user: discord.User):
        pass


def setup(bot):
    bot.add_cog(ScammerCheck(bot))

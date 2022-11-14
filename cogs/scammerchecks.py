import discord
from discord.ext import commands
import requests
from discord import option
import os
from dotenv import load_dotenv
from discord.commands import SlashCommandGroup
import requests_cache
import sqlite3


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
        mojangresponse = requests.get(f'https://api.mojang.com/users/profiles/minecraft/{player}')
        try:
            uuid = mojangresponse.json()['id']
            print(uuid)
        except Exception as err:
            print(err)
            embed = discord.Embed(title=f'Error',
                                  description='Error fetching information from the API. Recheck the spelling of your '
                                              'IGN',
                                  colour=0xFF0000)
            await ctx.respond(embed=embed)
            return
        conn = sqlite3.connect('SGScammer.sqlite')
        c = conn.cursor()
        c.execute(f"SELECT * FROM sgscammerdb WHERE minecraftuuid = '{uuid}' AND discord_guild_id = '{ctx.guild.id}'")
        if c.fetchone() is not None:
            embed = discord.Embed(title=f'Scammer Check',
                                  description=f'**{mojangresponse.json()["name"]}** is a in the server specific '
                                              f'blacklist. \n To remove them use /scammer '
                                              f'whitelist', colour=0xFF0000)
            embed.set_thumbnail(url=f'https://crafatar.com/renders/head/{uuid}')
            await ctx.respond(embed=embed)
            return
        conn.close()
        response = requests.get(f'https://skykings.net/api/lookup/?key={os.getenv("SKYKINGSKEY")}&uuid={uuid}')
        if response.status_code != 200:
            embed = discord.Embed(title=f'Error',
                                  description='Error fetching information from the API. Try again later',
                                  colour=0xFF0000)
            await ctx.respond(embed=embed)
            return
        data = response.json()
        if not data['success']:
            embed = discord.Embed(title=f'Error',
                                  description='Error fetching information from the API. Try again later',
                                  colour=0xFF0000)
            await ctx.respond(embed=embed)
            return

        if not data['entries']:
            embed = discord.Embed(title=f'Not a Scammer!',
                                  description=f'**{mojangresponse.json()["name"]}** is not a scammer! \n This does not '
                                              f'mean this person is safe '
                                              f'to trade with. Proceed with your own risk.',
                                  colour=0xee6940)
            embed.set_thumbnail(url=f'https://crafatar.com/renders/head/{uuid}')
            await ctx.respond(embed=embed)
            return
        for entry in data['entries']:
            embed = discord.Embed(title=f'Scammer!',
                                  description=f'**{mojangresponse.json()["name"]}** is a scammer! \n This '
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
        guild = data['guild']['name']
        guildmembers = []
        conn = sqlite3.connect('SGScammer.sqlite')
        c = conn.cursor()
        scammer = False
        scammers = []
        reasons = []
        for member in data['guild']['members']:
            c.execute(
                f"SELECT * FROM sgscammerdb WHERE minecraftuuid = '{member['uuid']}' AND discord_guild_id = '{ctx.guild.id}'")
            if c.fetchone() is not None:
                scammer = True
                print(member['uuid'])
                response = requests.get(f'https://api.mojang.com/user/profile/{member["uuid"]}')
                scammers.append(response.json()['name'])
                reasons.append('Server Specific Blacklist')
            else:
                guildmembers.append(member['uuid'])

        def divide_chunks(l, n):
            for i in range(0, len(l), n):
                yield l[i:i + n]

        x = list(divide_chunks(guildmembers, 10))
        for chunks in x:
            lookupstring = ",".join(chunks)
            response = requests.get(
                f'https://skykings.net/api/lookup/bulk?key={os.getenv("SKYKINGSKEY")}&uuids={lookupstring}')
            if response.status_code != 200:
                embed = discord.Embed(title=f'Error',
                                      description='Error fetching information from the API. Try again later',
                                      colour=0xFF0000)
                await ctx.respond(embed=embed)
                return
            data = response.json()
            if not data['success']:
                embed = discord.Embed(title=f'Error',
                                      description='Error fetching information from the API. Try again later',
                                      colour=0xFF0000)
                await ctx.respond(embed=embed)
                return
            if not data['entries']:
                pass
            else:
                for scammer in data['entries']:
                    for player in scammer['players']:
                        if len(scammer) > 10:
                            break
                        ign = requests.get(f'https://api.mojang.com/user/profile/{player}')
                        scammers.append(ign.json()['name'])
                    reasons.append(scammer['reason'])
                    scammer = True
        if not scammer:
            embed = discord.Embed(title=f'No Scammers!',
                                  description=f'**{guild}** has no scammers!',
                                  colour=0xee6940)
            await ctx.respond(embed=embed)
            return
        if scammer:
            embed = discord.Embed(title=f'Scammer(s)!',
                                  description=f'**{guild}** has scammers!',
                                  colour=0xFF0000)
            for i in range(len(scammers)):
                if i <= 9:
                    embed.add_field(name=scammers[i], value=reasons[i], inline=False)
                else:
                    embed.add_field(name='More Scammers!',
                                    value='This guild has more scammers! Unable to display all of them.', inline=False)
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

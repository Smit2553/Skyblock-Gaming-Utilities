import discord
from discord.ext import commands
from discord.commands import SlashCommandGroup
import os
import requests
from discord import option
import aiosqlite


class Server(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    server = SlashCommandGroup("server", "Discord server specific tools")

    @server.command(description="Add a user to the Server specific blacklist. ")
    @option(
        name="player",
        description="Minecraft IGN",
        required=True
    )
    @commands.has_permissions(ban_members=True)
    async def blacklist(self, ctx, player):
        response = requests.get(f'https://api.mojang.com/users/profiles/minecraft/{player}')
        if response.status_code != 200:
            embed = discord.Embed(title=f'Error',
                                  description='Error fetching information from the API. Try again later or check spelling of IGN.',
                                  colour=0xFF0000)
            await ctx.respond(embed=embed)
            return
        data = response.json()
        if data is None:
            embed = discord.Embed(title=f'Error',
                                  description='Error fetching information from the API. Try again later or check spelling of IGN.',
                                  colour=0xFF0000)
            await ctx.respond(embed=embed)
            return
        uuid = data['id']
        async with aiosqlite.connect('database/SGScammer.sqlite') as db:
            async with db.execute(
                    "SELECT * FROM sgscammerdb WHERE minecraftuuid = ? AND discord_guild_id = ?", (uuid, ctx.guild.id)) as cursor:
                async for row in cursor:
                    if row is not None:
                        embed = discord.Embed(title=f'Error',
                                              description='Player is already in the server specific blacklist',
                                              colour=0xFF0000)
                        await ctx.respond(embed=embed)
                        return
                await db.execute("INSERT INTO sgscammerdb VALUES (?, ?)", (ctx.guild.id, uuid))
                await db.commit()
        embed = discord.Embed(title=f'Added to blacklist!',
                              description=f'**{data["name"]}** has been added to the server blacklist!',
                              colour=0xee6940)
        embed.set_thumbnail(url=f'https://crafatar.com/renders/head/{uuid}')
        await ctx.respond(embed=embed)

    @server.command(description="Remove a user from the Server specific blacklist. ")
    @option(
        name="player",
        description="Minecraft IGN",
        required=True
    )
    @commands.has_permissions(ban_members=True)
    async def whitelist(self, ctx, player):
        response = requests.get(f'https://api.mojang.com/users/profiles/minecraft/{player}')
        if response.status_code != 200:
            embed = discord.Embed(title=f'Error',
                                  description='Error fetching information from the API. Try again later or check spelling of IGN.',
                                  colour=0xFF0000)
            await ctx.respond(embed=embed)
            return
        data = response.json()
        if data is None:
            embed = discord.Embed(title=f'Error',
                                  description='Error fetching information from the API. Try again later or check spelling of IGN.',
                                  colour=0xFF0000)
            await ctx.respond(embed=embed)
            return
        uuid = data['id']
        async with aiosqlite.connect('database/SGScammer.sqlite') as db:
            await db.execute("DELETE FROM sgscammerdb WHERE minecraftuuid = ? AND discord_guild_id = ?",
                             (uuid, ctx.guild.id))
            await db.commit()
        embed = discord.Embed(title=f'Removed from blacklist!',
                              description=f'**{data["name"]}** has been removed from the server blacklist!',
                              colour=0xee6940)
        embed.set_thumbnail(url=f'https://crafatar.com/renders/head/{uuid}')
        await ctx.respond(embed=embed)

    @server.command(description="List all the users on the Server specific blacklist.")
    async def scammerlist(self, ctx):
        check = False
        count = 0
        embed = discord.Embed(title=f'Server Blacklist',
                              description=f'**{ctx.guild.name}** has server specific scammers!',
                              colour=0xFF0000)
        async with aiosqlite.connect('database/SGScammer.sqlite') as db:
            async with db.execute(f"SELECT * FROM sgscammerdb WHERE discord_guild_id = '{ctx.guild.id}'") as cursor:
                async for row in cursor:
                    if row is not None:
                        check = True
                        count += 1
                        if count <= 9:
                            ign = requests.get(f'https://api.mojang.com/user/profile/{row[1]}')
                            embed.add_field(name=ign.json()['name'], value='Server Blacklisted!', inline=False)
                        if count > 9:
                            for i in range(9):
                                ign = requests.get(f'https://api.mojang.com/user/profile/{row[1]}')
                                embed.add_field(name=ign.json()['name'], value='Server Blacklisted!', inline=False)
                            embed.add_field(name='More Scammers!',
                                            value='This guild has more scammers! Unable to display all of them.',
                                            inline=False)
        if check is False:
            embed = discord.Embed(title=f'No Scammers!',
                                  description=f'**{ctx.guild.name}** has no server specific scammers!',
                                  colour=0xee6940)
            await ctx.respond(embed=embed)
            return
        await ctx.respond(embed=embed)
        return

    @server.command(description="View the server's configuration")
    async def config(self, ctx):
        async with aiosqlite.connect('database/SGGuildDB.sqlite') as db:
            async with db.execute("SELECT * FROM sgguildutilsdb WHERE discord_guild_id = ?", (ctx.guild.id,)) as cursor:
                async for row in cursor:
                    if row is not None:
                        embed = discord.Embed(title=f'Guild Config',
                                              description=f'**{ctx.guild.name}** has the following config setup!',
                                              colour=0xee6940)
                        response = requests.get(
                            f'https://api.hypixel.net/guild?key={os.getenv("APIKEY")}&&id={row[1]}')
                        if response.status_code != 200 or response.json()['guild'] is None or response.json()[
                            'success'] is False:
                            embed.add_field(name='Linked Guild', value=f'Error Getting Name from API', inline=False)
                        else:
                            embed.add_field(name='Linked Guild', value=f'{response.json()["guild"]["name"]}',
                                            inline=False)
                        vc = self.bot.get_channel(row[2])
                        if vc is None:
                            embed.add_field(name='Member Count Channel',
                                            value=f'Member Count Channel not set or has been deleted.',
                                            inline=False)
                        else:
                            embed.add_field(name='Member Count Channel', value=f'{vc.mention}', inline=False)
                        await ctx.respond(embed=embed)
                        return
                embed = discord.Embed(title=f'Error',
                                      description='This server has no config setup. Please use `/guild link` to create a '
                                                  'config.',
                                      colour=0xFF0000)
                await ctx.respond(embed=embed)
                return


def setup(bot):
    bot.add_cog(Server(bot))

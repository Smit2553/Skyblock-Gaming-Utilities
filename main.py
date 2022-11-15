import discord
import os
from dotenv import load_dotenv
from discord.ext import commands
from discord import option
import sqlite3
load_dotenv()

bot = discord.Bot(debug_guilds=[int(os.getenv("DEBUG_GUILD"))])


@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="/bugreport | Double "
                                                                                                "the features square"
                                                                                                " the bugs!"))
    conn = sqlite3.connect('database/SGdatabase.sqlite')
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS sgutilsdb (
        discord_id integer PRIMARY KEY,
        minecraft_uuid text NOT NULL
    )""")
    conn.commit()
    conn.close()
    conn = sqlite3.connect('database/SGGuildDB.sqlite')
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS sgguildutilsdb (
        discord_guild_id integer PRIMARY KEY,
        skyblock_guild_id text NOT NULL,
        member_count_channel integer
    )""")
    conn.commit()
    conn.close()
    conn = sqlite3.connect('database/SGScammer.sqlite')
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS sgscammerdb (
            discord_guild_id integer,
            minecraftuuid integer NOT NULL
        )""")
    conn.commit()
    conn.close()
    print('SQLite database created')
    print(f"Logged in as {bot.user}")


for filename in os.listdir('./cogs'):
    if filename.endswith('.py'):
        try:
            bot.load_extension(f'cogs.{filename[:-3]}')
            print(f"Loaded {filename}")
        except Exception as err:
            print(err)


@bot.command(description="Ping Pong! Check the bot latency.")
async def ping(ctx):
    await ctx.respond(f"Pong! {bot.latency * 1000:.2f}ms")

@bot.event
async def on_application_command_error(ctx: discord.ApplicationContext, error: discord.DiscordException):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.respond(f"{error}")
    elif isinstance(error, commands.NotOwner):
        await ctx.respond("This command is for owners only!")
    elif isinstance(error, commands.MissingPermissions):
        await ctx.respond(error)
    else:
        raise error

owner = bot.create_group("owner", "Owner Commands", guild_ids=[int(os.getenv('DEBUG_GUILD'))])


@owner.command(description="Reload all cogs.")
@commands.is_owner()
async def reload(ctx):
    for filename1 in os.listdir('./cogs'):
        if filename1.endswith('.py'):
            bot.unload_extension(f'cogs.{filename1[:-3]}')

    for filename1 in os.listdir('./cogs'):
        if filename1.endswith('.py'):
            bot.load_extension(f'cogs.{filename1[:-3]}')
    await ctx.respond("All cogs reloaded")


@owner.command(description="Unload a cog.")
@commands.is_owner()
@option("extension", description="Choose a Cog", choices=[i[:-3] for i in os.listdir('./cogs')
                                                          if i.endswith('.py')])
async def unload(ctx, extension):
    bot.unload_extension(f'cogs.{extension}')
    await ctx.respond("Unloaded")


@owner.command(description="Load a cog.")
@commands.is_owner()
@option("extension", description="Choose a Cog", choices=[i[:-3] for i in os.listdir('./cogs')
                                                          if i.endswith('.py')])
async def load(ctx, extension):
    bot.load_extension(f'cogs.{extension}')
    await ctx.respond("Loaded")

@bot.event
async def on_guild_join(guild):
    print(f"Joined {guild.name} ({guild.id})")
bot.run(os.getenv("TOKEN"))

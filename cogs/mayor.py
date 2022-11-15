import discord
from discord.ext import commands
from discord.ext.pages import Paginator, Page
from aiohttp_client_cache import CachedSession, SQLiteBackend

class Mayor(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @discord.slash_command(description="Check the current mayor.")
    async def mayor(self, ctx):
        file = None
        async with CachedSession(cache=SQLiteBackend('database/election_cache', expires_after=600)) as session:
            response = await session.get("https://api.hypixel.net/resources/skyblock/election")
        if response.status != 200:
            await ctx.respond("Error fetching information from the API. Try again later", ephemeral=True)
            return
        data = await response.json()
        if not data["success"]:
            await ctx.respond("Error fetching information from the API. Try again later", ephemeral=True)
            return
        try:
            currentmayor = data['mayor']['name']
            perks = discord.Embed(title=f"{currentmayor}", color=0xee6940)
            try:
                file = discord.File(f"./resources/mayor/{currentmayor}.png", filename="image.png")
                perks.set_thumbnail(url=f'attachment://image.png')
            except:
                pass
            for perk in data['mayor']['perks']:
                perks.add_field(name=perk['name'], value=perk['description'], inline=True)
        except KeyError:
            await ctx.respond("Either there is no current mayor or an unknown error has occurred.", ephemeral=True)
            return
        if file is not None:
            await ctx.respond(embed=perks, file=file)
        else:
            await ctx.respond(embed=perks)

    @discord.slash_command(description="Check the results of the current mayoral elections.")
    async def election(self, ctx):
        async with CachedSession(cache=SQLiteBackend('database/election_cache', expires_after=600)) as session:
            response = await session.get("https://api.hypixel.net/resources/skyblock/election")
        if response.status != 200:
            await ctx.respond("Error fetching information from the API. Try again later", ephemeral=True)
            return
        data = await response.json()
        if not data["success"]:
            await ctx.respond("Error fetching information from the API. Try again later", ephemeral=True)
            return
        embeds = []
        files = []
        for candidate in data['mayor']['election']['candidates']:
            try:
                name = candidate['name']
                embed = discord.Embed(title=f"{name}", color=0xee6940)
                for perks in candidate['perks']:
                    description = perks['description']
                    l = list(description)
                    for i in range(len(l)):
                        if l[i] == "§":
                            l[i] = ""
                            l[i + 1] = ""
                    s = "".join(l)
                    embed.add_field(name=perks['name'], value=s, inline=True)
                try:
                    file = discord.File(f"./resources/mayor/{name}.png", filename="image.png")
                    embed.set_thumbnail(url=f'attachment://image.png')
                    files.append(file)
                except FileNotFoundError:
                    files.append(None)
                embeds.append(embed)
            except KeyError:
                await ctx.respond("An unknown error has occurred.", ephemeral=True)
                return
        my_pages = []
        for i in range(len(embeds)):
            if files[i] is not None:
                my_pages.append(Page(embeds=[embeds[i]], file=files[i]))
            else:
                my_pages.append(Page(embeds=[embeds[i]]))
        paginator = Paginator(pages=my_pages)
        await paginator.respond(ctx.interaction)


def setup(bot):
    bot.add_cog(Mayor(bot))

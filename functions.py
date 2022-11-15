import aiohttp
import discord
import aiosqlite
from aiohttp_client_cache import CachedSession, SQLiteBackend


async def ign_to_uuid(ign: str):
    async with CachedSession(cache=SQLiteBackend('ign_cache', expires_after=86400)) as session:
        response = await session.get(f'https://api.mojang.com/users/profiles/minecraft/{ign}')
        if response.status != 200:
            embed = discord.Embed(title=f'Error',
                                  description='Error fetching information from the API. Recheck the spelling of your '
                                              'IGN',
                                  colour=0xFF0000)
            return embed
        data = await response.json()
        try:
            return data
        except Exception as err:
            print(err)
            embed = discord.Embed(title=f'Error',
                                  description='Error fetching information from the API. Recheck the spelling of your '
                                              'IGN',
                                  colour=0xFF0000)
            return embed


async def uuid_to_ign(uuid):
    async with CachedSession(cache=SQLiteBackend('ign_cache', expires_after=86400)) as session:
        response = await session.get(f'https://api.mojang.com/user/profile/{uuid}')
        if response.status != 200:
            embed = discord.Embed(title=f'Error',
                                  description='Error fetching information from the API. Try again later',
                                  colour=0xFF0000)
            return embed
        data = await response.json()
        try:
            return data['name']
        except Exception as err:
            print(err)
            embed = discord.Embed(title=f'Error',
                                  description='Error fetching information from the API. Try again later',
                                  colour=0xFF0000)
            return embed

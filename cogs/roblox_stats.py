import aiohttp

async def get_group_info(group_id: int):
    url = f"https://groups.roblox.com/v1/groups/{group_id}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status != 200:
                return None, None
            data = await resp.json()
            return data["name"], data["memberCount"]


async def get_game_stats(universe_id: int):
    url = f"https://games.roblox.com/v1/games?universeIds={universe_id}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status != 200:
                return None, None, None
            data = (await resp.json())["data"][0]
            return data["name"], data["visits"], data["likes"]

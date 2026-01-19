import aiohttp

async def get_group_info(group_id: int):
    url = f"https://groups.roblox.com/v1/groups/{group_id}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status != 200:
                return None, None
            data = await resp.json()
            name = data.get("name")
            members = data.get("memberCount", 0)
            return name, members

async def get_game_stats(universe_id: int):
    url = f"https://games.roblox.com/v1/games?universeIds={universe_id}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status != 200:
                return None, None, None
            json_data = await resp.json()
            game_data_list = json_data.get("data", [])
            if not game_data_list:
                return None, None, None
            data = game_data_list[0]
            name = data.get("name")
            visits = data.get("visits", 0)
            likes = data.get("likes") or data.get("favoritedCount") or 0
            return name, visits, likes

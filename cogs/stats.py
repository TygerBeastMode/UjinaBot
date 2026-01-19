import requests

def get_group_info(group_id):
    url = f"https://groups.roblox.com/v1/groups/{group_id}"
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        name = data["name"]
        member_count = data["memberCount"]
        return name, member_count
    else:
        return None, None

def get_game_stats(universe_id):
    url = f"https://games.roblox.com/v1/games?universeIds={universe_id}"
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()["data"][0]
        name = data["name"]
        visits = data["visits"]
        likes = data["likes"]
        return name, visits, likes
    else:
        return None, None, None

group_name, members = get_group_info(756148344)  # replace with your group ID
game_name, visits, likes = get_game_stats(8605005806)  # replace with your universe ID

print(f"Group {group_name} has {members} members.")
print(f"Game {game_name} has {visits} visits and {likes} likes.")

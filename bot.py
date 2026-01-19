import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv
import os
import datetime
from roblox_stats import get_group_info, get_game_stats

GROUP_ID = 756148344
UNIVERSE_ID = 8605005806
VOICE_CHANNEL_ID = 1462891428844798022

intents = discord.Intents.all()

PERMISSIONS = {
    1457579511297216626: {  # Presidental Server
        "purge": [1457579620936192010],
    },
    1446923448822665380: {  # Departments Server
        "purge": [
            1455280261737611406,
            1448504233627357285,
            1448504299301765230,
        ],
    },
    1450322192989687861: {  # Main Server
        "purge": [
            1454291298088390728,
            1454291656915419310,
            1454328822072606750,
            1454291086452199526,
            1455013941368455231,
        ],
    },
}


bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

@bot.event
async def setup_hook():
    await bot.load_extension("cogs.logging")


# ---------------- Permissions helpers ----------------
def has_command_permission(interaction: discord.Interaction, command_name: str) -> bool:
    if not interaction.guild:
        return False
    guild_perms = PERMISSIONS.get(interaction.guild.id)
    if not guild_perms:
        return False
    allowed_roles = guild_perms.get(command_name)
    if not allowed_roles:
        return False
    user_role_ids = {role.id for role in interaction.user.roles}
    return any(role_id in user_role_ids for role_id in allowed_roles)

def command_check(command_name: str):
    async def predicate(interaction: discord.Interaction):
        return has_command_permission(interaction, command_name)
    return discord.app_commands.check(predicate)


# ---------------- Roblox Stats Updater ----------------
@tasks.loop(minutes=5)  # update every 5 minutes
async def update_stats_channel():
    channel = bot.get_channel(VOICE_CHANNEL_ID)
    if not channel or not isinstance(channel, discord.VoiceChannel):
        return

    # Fetch group and game info
    group_name, members = await get_group_info(GROUP_ID)
    game_name, visits, likes = await get_game_stats(UNIVERSE_ID)

    if members is None or visits is None:
        print("Failed to fetch Roblox data.")
        return

    # Format numbers (compact)
    def format_number(n):
        if n >= 1_000_000:
            return f"{n//1_000_000}M"
        elif n >= 1_000:
            return f"{n//1_000}K"
        return str(n)

    members_display = format_number(members)
    visits_display = format_number(visits)
    likes_display = format_number(likes or 0)

    # Build channel name (max 100 chars)
    new_name = f"👥 {members_display} | 🎮 {visits_display} | ❤️ {likes_display}"

    try:
        await channel.edit(name=new_name)
        print(f"Updated Roblox stats channel: {new_name}")
    except discord.Forbidden:
        print("Missing permissions to edit channel")
    except discord.HTTPException as e:
        print(f"Failed to update channel: {e}")


# ---------------- Bot Events ----------------
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    await bot.tree.sync()
    print("Synced application commands")

    # Start Roblox stats updater
    if not update_stats_channel.is_running():
        update_stats_channel.start()
        print("Roblox stats updater started.")

    # Optional startup message
    channel = bot.get_channel(1458277133519552643)
    if channel:
        embed = discord.Embed(
            title="🤖 Bot Started",
            description=f"{bot.user.name} is now online!",
            color=0x00FF00,
            timestamp=datetime.datetime.now(datetime.timezone.utc)
        )
        await channel.send(embed=embed)
    else:
        print("Bot started but couldn't send startup message.")


# ---------------- Slash Commands ----------------
@tree.command(name="ping", description="Check the bot's latency")
async def ping(interaction: discord.Interaction):
    latency = bot.latency * 1000
    await interaction.response.send_message(f"Pong! Latency: {latency:.2f} ms")

@tree.command(name="purge", description="Delete a specified number of messages from the channel")
@discord.app_commands.describe(number="The number of messages to delete")
@command_check("purge")
async def purge(interaction: discord.Interaction, number: int):
    if not 1 <= number <= 100:
        await interaction.response.send_message(
            "Please specify a number between 1 and 100.",
            ephemeral=True
        )
        return

    embed = discord.Embed(
        color=15105570,
        title="Purge in Progress",
        description=f"Deleting **{number}** messages from this channel.\n\nPlease wait…",
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)
    deleted = await interaction.channel.purge(limit=number)
    newembed = discord.Embed(
        color=7439189,
        title="Purge Complete",
        description=f"Successfully deleted **{len(deleted)}** messages from this channel.",
    )
    await interaction.followup.send(embed=newembed, ephemeral=True)


# ---------------- Command Error Handling ----------------
@tree.error
async def on_app_command_error(interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
    if isinstance(error, discord.app_commands.CheckFailure):
        embed = discord.Embed(
            color=15158332,
            title="Permission Denied",
            description="You don’t have the required role or permissions to use this command in this server.",
        )
        embed.set_footer(text="If you believe this is a mistake, contact buddywinte.")
        if interaction.response.is_done():
            await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    raise error


# ---------------- Run Bot ----------------
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
bot.run(TOKEN)

import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv
import os
from typing import Optional
import asyncio
import aiohttp

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
    1456538100481396762: { # Affiliates Server
        "purge": [
            1456740431168536661,
            1456680897603440853
        ]
    }
}

STAT_FORMATTERS = {
    "likes": lambda d: f"・👍 Likes: {d['upvotes']}",
    "visits": lambda d: f"・👁️ Visits: {d['visits']}",
    "playing": lambda d: f"・{d['playing_emoji']} Playing: {d['playing']}",
    "favorited": lambda d: f"・⭐ Favorites: {d['favorited']}",
    "members": lambda d: f"・👥 Group Members: {d['members']}",
}

async def track_stats(
    UniverseId: int,
    GroupId: int,
    InfoChannel: discord.TextChannel,
    StatChannels: dict[str, discord.TextChannel]
):
    if not all((UniverseId, GroupId, InfoChannel, StatChannels)):
        print("missing required arguments")
        return
    message = None
    last_stats = {}
    timeout = aiohttp.ClientTimeout(total=10)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        while True:
            try:
                async with session.get(
                    f"https://ujina-proxy.buddywinte.workers.dev/?universe={UniverseId}&group={GroupId}"
                ) as r:
                    if r.status != 200:
                        print(f"worker returned {r.status}, retrying in 10s")
                        await asyncio.sleep(10)
                        continue
                    data = await r.json()
                    game = data.get("game", {})
                    group = data.get("group", {})
                    stats = {
                        "upvotes": game.get("upVotes", 0),
                        "downvotes": game.get("downVotes", 0),
                        "visits": game.get("visits", 0),
                        "playing": game.get("playing", 0),
                        "favorited": game.get("favorited", 0),
                        "members": group.get("members", 0),
                    }
                    stats["playing_emoji"] = "🟢" if stats["playing"] > 0 else "🔴"
                    if stats != last_stats:
                        game_embed = discord.Embed(
                            title="🎮 Game Statistics",
                            color=7439189
                        )
                        game_embed.add_field(name="👍 Likes", value=f"**{stats['upvotes']}**", inline=True)
                        game_embed.add_field(name="👁️ Visits", value=f"**{stats['visits']}**", inline=True)
                        game_embed.add_field(
                            name=f"{stats['playing_emoji']} Playing",
                            value=f"**{stats['playing']}**",
                            inline=True
                        )
                        game_embed.add_field(
                            name="⭐ Favorited",
                            value=f"**{stats['favorited']}**",
                            inline=True
                        )
                        group_embed = discord.Embed(
                            title="👥 Group Statistics",
                            color=3447003
                        )
                        group_embed.add_field(
                            name="Total Members",
                            value=f"**{stats['members']}**",
                            inline=True
                        )
                        if message is None:
                            message = await InfoChannel.send(
                                embeds=[game_embed, group_embed]
                            )
                        else:
                            await message.edit(
                                embeds=[game_embed, group_embed]
                            )
                        for stat_name, channel in StatChannels.items():
                            key = stat_name.lower()
                            formatter = STAT_FORMATTERS.get(key)
                            if not formatter:
                                continue
                            new_name = formatter(stats)
                            if channel.name != new_name:
                                bot.logging_cog._self_updates.add(channel.id)
                                await channel.edit(name=new_name)
                                await asyncio.sleep(0.3)
                        last_stats = stats.copy()
            except Exception as e:
                print(f"stats task error: {type(e).__name__}: {e}")
            await asyncio.sleep(60)



# 3277208800 universe id

bot = commands.Bot(command_prefix="!", intents=intents)
tree=bot.tree

# do we have permissions function
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

# slash commands helper
def command_check(command_name: str):
    async def predicate(interaction: discord.Interaction):
        return has_command_permission(interaction, command_name)
    return discord.app_commands.check(predicate)


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    if not hasattr(bot, "group_task"):
        info_channel = bot.get_channel(1462833382185762950)
        if info_channel:
            stat_channels = {
                "likes": bot.get_channel(1462935332772118702),
                "visits": bot.get_channel(1462935504407494656),
                "playing": bot.get_channel(1462935516117864468),
                "favorited": bot.get_channel(1462935528037945375),
                "members": bot.get_channel(1462935543624106095),
            }
            missing = [k for k, v in stat_channels.items() if v is None]
            if missing:
                print(f"Missing channels: {missing}")
            else:
                bot.group_task = bot.loop.create_task(
                    track_stats(3277208800, 756148344, info_channel, stat_channels)
                )
                print("logging")
        else:
            print("Info channel not found")

@bot.event
async def setup_hook():
    await bot.load_extension("cogs.logging")
    await bot.add_cog(Tickets(bot))
    await bot.tree.sync()

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    if message.content.strip().lower() == "/e dance":
        await message.channel.send("<a:edance:1464108231969345648>")
    elif message.content.strip().lower() == "/e stare":
        await message.channel.send("...")
    elif message.content.strip().lower() == "ean":
        await message.channel.send("<:ean:1464110856144031951>")
    elif message.content.strip().lower() == "egg":
        await message.channel.send("<:egg:1464110854470373523>")
    elif message.content.strip().lower() == "cheezburger":
        await message.channel.send("<a:cheezburger:1464111559998705716>")
    await bot.process_commands(message)

@tree.command(name="ping", description="Check the bot's latency")
async def ping(interaction: discord.Interaction):
    latency = bot.latency * 1000
    await interaction.response.send_message(f"Pong! Latency: {latency:.2f} ms")


# purge command
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
        description=f"Deleting **{str(number)}** messages from this channel.\n\nPlease wait…",
    )
    await interaction.response.send_message(
        embed=embed,
        ephemeral=True)
    deleted = await interaction.channel.purge(limit=number)
    newembed = discord.Embed(
        color=7439189,
        title="Purge Complete",
        description=f"Successfully deleted **{len(deleted)}** messages from this channel.",
    )
    await interaction.followup.send(
        embed=newembed,
        ephemeral=True
    )






# command errors
@tree.error
async def on_app_command_error(
    interaction: discord.Interaction,
    error: discord.app_commands.AppCommandError
):
    if isinstance(error, discord.app_commands.CheckFailure):
        embed = discord.Embed(
                color=15158332,
                title="Permission Denied",
                description="You don’t have the required role or permissions to use this command in this server.",
            )
        embed.set_footer(
            text="If you believe this is a mistake, contact buddywinte.",
        )
        if interaction.response.is_done():
            await interaction.followup.send(
                embed=embed,
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                embed=embed,
                ephemeral=True
            )
        return
    raise error

class Tickets(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    ticket = app_commands.Group(
        name="ticket",
        description="Ticket management commands"
    )

    # /ticket add
    @ticket.command(name="add", description="Add a user or role to the ticket")
    @discord.app_commands.describe(
        user="User to add to the ticket",
        role="Role to add to the ticket"
    )
    async def ticket_add(
        self,
        interaction: discord.Interaction,
        user: Optional[discord.Member] = None,
        role: Optional[discord.Role] = None,
    ):
        if not user and not role:
            embed = discord.Embed(
                color=15158332,
                title="Paremeters Error",
                description="You should probably give all the required paremeters for this command.",
            )
            await interaction.response.send_message(
                embed=embed,
                ephemeral=True
            )

    # /ticket rename
    @ticket.command(name="rename", description="Rename the current ticket")
    @app_commands.describe(name="New name for the ticket")
    async def ticket_rename(self, interaction: discord.Interaction, name: str):
        await interaction.response.send_message(
            f"✏️ Ticket renamed to **{name}**",
            ephemeral=True
        )

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
bot.run(TOKEN)

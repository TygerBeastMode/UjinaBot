import discord
import datetime
from discord.ext import commands

PERM_NAMES = {
    "add_reactions": "Add Reactions",
    "administrator": "Administrator",
    "attach_files": "Attach Files",
    "ban_members": "Ban Members",
    "change_nickname": "Change Nickname",
    "connect": "Connect",
    "create_instant_invite": "Create Invite",
    "deafen_members": "Deafen Members",
    "embed_links": "Embed Links",
    "kick_members": "Kick Members",
    "manage_channels": "Manage Channels",
    "manage_emojis": "Manage Emojis",
    "manage_guild": "Manage Server",
    "manage_messages": "Manage Messages",
    "manage_nicknames": "Manage Nicknames",
    "manage_permissions": "Manage Permissions",
    "manage_roles": "Manage Roles",
    "manage_threads": "Manage Threads",
    "manage_webhooks": "Manage Webhooks",
    "mention_everyone": "Mention Everyone",
    "move_members": "Move Members",
    "mute_members": "Mute Members",
    "priority_speaker": "Priority Speaker",
    "read_message_history": "Read Message History",
    "request_to_speak": "Request to Speak",
    "send_messages": "Send Messages",
    "send_messages_in_threads": "Send Messages in Threads",
    "send_tts_messages": "Send TTS Messages",
    "speak": "Speak",
    "stream": "Stream",
    "use_application_commands": "Use Commands",
    "use_embedded_activities": "Use Activities",
    "use_external_emojis": "Use External Emojis",
    "use_external_stickers": "Use External Stickers",
    "use_voice_activation": "Voice Activation",
    "view_audit_log": "View Audit Log",
    "view_channel": "View Channel",
    "view_guild_insights": "View Server Insights",
}

LOG_CHANNELS = {
    1457579511297216626: {  # Presidential Server
        "misc": 1462606414164922398,
    },
    1456538100481396762: { # Alliances Server
        "misc": 1456729696778588263,
        "messages": 1456730217791094784
    },
    1450322192989687861: { # Departments Server
        "misc": 1454301298307633182
    },
    1446923448822665380: { # Main Server
        "misc": 1448347223644569661,
        "messages": 1457599061225115778,
        "channels": 1462628809315586249
    }
}

GLOBAL_LOG_CHANNELS = {
    "mod_logs": 1462606414164922398  # mod logs
}

def format_overwrites_ansi(overwrites: dict):
    formatted = []
    for target, overwrite in overwrites.items():
        perms = []
        for perm_name, value in overwrite:
            readable = PERM_NAMES.get(perm_name, perm_name.replace("_", " ").title())
            if value is True:
                perms.append(f"\u001b[1;32m{readable}\u001b[0m")
            elif value is False:
                perms.append(f"\u001b[1;31m{readable}\u001b[0m")
        perms_text = ", ".join(perms) if perms else "\u001b[0;37mNo specific permissions\u001b[0m"
        formatted.append(f"{target}: {perms_text}")
    return "\n".join(formatted)

def highlight_diff_ansi(before: str, after: str):
    if before == after:
        return None
    return f"\u001b[1;31m{before}\u001b[0m ➜ \u001b[1;32m{after}\u001b[0m"


class Logging(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._self_updates: set[int] = set()
        bot.logging_cog = self

    # lifecycle
    @commands.Cog.listener()
    async def on_ready(self):
        print("logging cod loaded")

    # helpers
    async def get_channel(self, guild: discord.Guild, category: str) -> discord.TextChannel | None:
        if category in GLOBAL_LOG_CHANNELS:
            channel_id = GLOBAL_LOG_CHANNELS[category]
        else:
            guild_channels = LOG_CHANNELS.get(guild.id, {})
            channel_id = guild_channels.get(category) or guild_channels.get("misc")
        if not channel_id:
            return None
        return guild.get_channel(channel_id)
    
    async def send_log(self, guild: discord.Guild, category: str, embed: discord.Embed):
        channel = await self.get_channel(guild, category)
        if not channel:
            print(f"[Logging] No channel found for category '{category}' in guild '{guild.name}'")
            return
        
        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel: discord.abc.GuildChannel):
        if channel.id in self._self_updates:
            self._self_updates.discard(channel.id)
            return
        embed = discord.Embed(
            title="🗑️ Channel Deleted",
            description=f"A channel was deleted in **{channel.guild.name}**",
            color=0xE74C3C,
            timestamp=datetime.datetime.now(datetime.timezone.utc)
        )
        if channel.guild.me.guild_permissions.view_audit_log:
            async for entry in channel.guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_delete):
                if entry.target.id == channel.id:
                    embed.set_author(name=f"Deleted by {entry.user}", icon_url=entry.user.display_avatar.url)
                    break
        topic = getattr(channel, "topic", None)
        if topic and len(topic) > 200:
            topic = topic[:200] + "..."
        perms = []
        for target, overwrite in channel.overwrites.items():
            perms.append(f"{target}: {overwrite}")
        perms_text = format_overwrites_ansi(channel.overwrites)
        info = [
            f"**Name:** {channel.name} (`{channel.id}`)",
            f"**Type:** {channel.type}",
            f"**Category:** {channel.category if channel.category else 'None'}",
            f"**Topic:** {topic if topic else 'None'}",
            f"**Position:** {channel.position}",
            f"**Created At:** {channel.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}",
            f"**NSFW:** {getattr(channel, 'is_nsfw', lambda: False)()}",
            f"**Permissions:** {f"```ansi\n{perms_text}\n```" if perms else 'None'}"
        ]
        if isinstance(channel, discord.VoiceChannel):
            info.append(f"**Bitrate:** {channel.bitrate}")
            info.append(f"**User Limit:** {channel.user_limit}")
        elif isinstance(channel, discord.TextChannel):
            info.append(f"**Slowmode:** {channel.slowmode_delay} seconds")
        elif isinstance(channel, discord.ForumChannel):
            info.append(f"**Default Emoji:** {channel.default_reaction_emoji}")
            info.append(f"**Default Thread Slowmode:** {channel.default_thread_slowmode_delay} seconds")
        embed.add_field(
            name="Channel Info",
            value="\n".join(info),
            inline=False
        )
        embed.set_footer(
            text=f"Guild ID: {channel.guild.id}",
            icon_url=channel.guild.icon.url if channel.guild.icon else None
        )
        await self.send_log(channel.guild, "channels", embed)

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel: discord.abc.GuildChannel):
        if channel.id in self._self_updates:
            self._self_updates.discard(channel.id)
            return
        embed = discord.Embed(
            title="📥 Channel Created",
            description=f"A new channel was created in **{channel.guild.name}**",
            color=0x2ECC71,
            timestamp=datetime.datetime.now(datetime.timezone.utc)
        )
        topic = getattr(channel, "topic", None)
        if topic and len(topic) > 200:
            topic = topic[:200] + "…"
        perms = []
        for target, overwrite in channel.overwrites.items():
            perms.append(f"{target}: {overwrite}")
        perms_text = format_overwrites_ansi(channel.overwrites)
        info = [
            f"**Name:** {channel.name}",
            f"**ID:** {channel.id}",
            f"**Type:** {channel.type}",
            f"**Category:** {channel.category if channel.category else 'None'}",
            f"**NSFW:** {getattr(channel, 'is_nsfw', lambda: False)()}",
            f"**Permissions:** {f"```ansi\n{perms_text}\n```" if perms else 'None'}"
        ]
        if isinstance(channel, discord.VoiceChannel):
            info.append(f"**Bitrate:** {channel.bitrate}")
            info.append(f"**User Limit:** {channel.user_limit}")
        elif isinstance(channel, discord.TextChannel):
            info.append(f"**Slowmode:** {channel.slowmode_delay} seconds")
        elif isinstance(channel, discord.ForumChannel):
            info.append(f"**Default Emoji:** {channel.default_reaction_emoji}")
            info.append(f"**Default Thread Slowmode:** {channel.default_thread_slowmode_delay} seconds")
        if topic:
            info.append(f"**Topic:** {topic}")
        embed.add_field(
            name="Channel Info",
            value="\n".join(info),
            inline=False
        )
        if channel.guild.me.guild_permissions.view_audit_log:
            async for entry in channel.guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_create):
                if entry.target.id == channel.id:
                    embed.set_author(name=f"Created by {entry.user}", icon_url=entry.user.display_avatar.url)
                    break
        if getattr(channel, "jump_url", None):
            embed.add_field(name="Channel Link", value=channel.jump_url, inline=False)
        embed.set_footer(
            text=f"Guild ID: {channel.guild.id}",
            icon_url=channel.guild.icon.url if channel.guild.icon else None
        )
        await self.send_log(channel.guild, "channels", embed)

    @commands.Cog.listener()
    async def on_guild_channel_update(self, before: discord.abc.GuildChannel, after: discord.abc.GuildChannel):
        if after.id in self._self_updates:
            self._self_updates.discard(after.id)
            return
        changes = []
        def normalize_topic(topic):
            return None if not topic else topic # discord topics are weird?
        def fmt(val):
            return "None" if val is None else str(val)
        if before.name != after.name:
            changes.append(f"**Name:** `{before.name}` ➜ `{after.name}`")
        if before.category != after.category:
            changes.append(f"**Category:** `{fmt(before.category)}` ➜ `{fmt(after.category)}`")
        if normalize_topic(getattr(before, "topic", None)) != normalize_topic(getattr(after, "topic", None)):
            changes.append(f"**Topic:** `{fmt(before.topic)}` ➜ `{fmt(after.topic)}`")
        if before.position != after.position:
            changes.append(f"**Position:** `{before.position}` ➜ `{after.position}`")
        if getattr(before, "nsfw", None) != getattr(after, "nsfw", None):
            changes.append(f"**NSFW:** `{before.is_nsfw()}` ➜ `{after.is_nsfw()}`")
        if isinstance(before, discord.TextChannel) and before.slowmode_delay != after.slowmode_delay:
            changes.append(f"**Slowmode:** `{before.slowmode_delay}` ➜ `{after.slowmode_delay}`")
        if isinstance(before, discord.VoiceChannel):
            if before.bitrate != after.bitrate:
                changes.append(f"**Bitrate:** `{before.bitrate}` ➜ `{after.bitrate}`")
            if before.user_limit != after.user_limit:
                changes.append(f"**User Limit:** `{before.user_limit}` ➜ `{after.user_limit}`")
        if isinstance(before, discord.ForumChannel):
            if before.default_thread_slowmode_delay != after.default_thread_slowmode_delay:
                changes.append(f"**Default Thread Slowmode:** `{before.default_thread_slowmode_delay}` ➜ `{after.default_thread_slowmode_delay}`")
            if before.default_reaction_emoji != after.default_reaction_emoji:
                changes.append(f"**Default Emoji:** `{before.default_reaction_emoji}` ➜ `{after.default_reaction_emoji}`")
        def perms_diff_ansi(before_overwrites, after_overwrites):
            diffs = []
            all_targets = set(before_overwrites.keys()).union(after_overwrites.keys())
            for target in all_targets:
                before_perm = before_overwrites.get(target, discord.PermissionOverwrite())
                after_perm = after_overwrites.get(target, discord.PermissionOverwrite())
                changes_list = []
                for perm_name, _ in before_perm:
                    b_val = getattr(before_perm, perm_name, None)
                    a_val = getattr(after_perm, perm_name, None)
                    if b_val != a_val:
                        readable = PERM_NAMES.get(perm_name, perm_name.replace("_", " ").title())
                        if a_val is True:
                            changes_list.append(f"\u001b[1;32m{readable}\u001b[0m")  # allowed
                        elif a_val is False:
                            changes_list.append(f"\u001b[1;31m{readable}\u001b[0m")  # denied
                if changes_list:
                    diffs.append(f"{target}: {', '.join(changes_list)}")
            return "\n".join(diffs)
        perms_changes = perms_diff_ansi(before.overwrites, after.overwrites)
        if perms_changes:
            changes.append(f"**Permissions Changed:**\n{perms_changes}")
        if not changes:
            return # nothihg changes that we care about
        embed = discord.Embed(
            title="✏️ Channel Updated",
            description=f"A channel was updated in **{after.guild.name}**",
            color=0x3498DB,
            timestamp=datetime.datetime.now(datetime.timezone.utc)
        )
        if getattr(after, "jump_url", None):
            embed.add_field(name="Channel Link", value=after.jump_url, inline=False)
        embed.add_field(name="Changes", value="\n".join(changes), inline=False)
        embed.set_footer(
            text=f"Guild ID: {after.guild.id}",
            icon_url=after.guild.icon.url if after.guild.icon else None
        )
        if after.guild.me.guild_permissions.view_audit_log:
            async for entry in after.guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_update):
                if entry.target.id == after.id:
                    embed.set_author(name=f"Updated by {entry.user}", icon_url=entry.user.display_avatar.url)
                    break
        await self.send_log(after.guild, "channels", embed)

    # MESSAGE LOGS
    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        if before.author.bot:
            return
        changes = []
        content_diff = highlight_diff_ansi(before.content[:500], after.content[:500])
        if content_diff:
            changes.append(f"**Content:** ```ansi\n{content_diff}\n```")
        
        before_attachments = [a.url for a in before.attachments]
        after_attachments = [a.url for a in after.attachments]
        if before_attachments != after_attachments:
            changes.append(f"**Attachments:** `{before_attachments}` ➜ `{after_attachments}`")

        if not changes:
            return

        embed = discord.Embed(
            title="✏️ Message Edited",
            description=f"Message edited in {after.channel.mention}",
            color=0x3498DB,
            timestamp=datetime.datetime.now(datetime.timezone.utc)
        )
        embed.add_field(name="Author", value=after.author.mention, inline=False)
        embed.add_field(name="Message Link", value=after.jump_url, inline=False)
        embed.add_field(name="Changes", value="\n".join(changes), inline=False)
        embed.set_footer(text=f"Author ID: {after.author.id} | Guild ID: {after.guild.id}" if after.guild else f"Author ID: {after.author.id}")
        await self.send_log(after.guild, "messages", embed)

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        if message.author.bot:
            return
        embed = discord.Embed(
            title="🗑️ Message Deleted",
            description=f"Message deleted in {message.channel.mention}",
            color=0xE74C3C,
            timestamp=datetime.datetime.now(datetime.timezone.utc)
        )
        if message.content:
            content = message.content[:500]
            embed.add_field(name="Content", value=f"```ansi\n\u001b[1;31m{content}\u001b[0m\n```", inline=False)

        if message.attachments:
            urls = [a.url for a in message.attachments]
            embed.add_field(name="Attachments", value="\n".join(urls), inline=False)
        
        embed.add_field(name="Author", value=message.author.mention, inline=False)
        embed.set_footer(text=f"Author ID: {message.author.id} | Guild ID: {message.guild.id}" if message.guild else f"Author ID: {message.author.id}")

        await self.send_log(message.guild, "messages", embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(Logging(bot))

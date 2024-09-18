import discord
from discord.ext import commands
import json
import asyncio

intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='?', intents=intents)

ADMIN_ID = 1238444724386533417
user_afk = {}
blacklist = {}
triggers = {}
auto_mod_links = {}
auto_mod_nsfw = {}
auto_mod_scams = {}
mod_log = {}
announcements = {}
warns = {}
punishments = {}
server_data = {}
server_copy_data = {}
anti_nuke = {}
bot_adders = {}

def has_permissions(**perms):
    def predicate(ctx):
        return all(getattr(ctx.author.permissions_in(ctx.channel), perm) for perm in perms)
    return commands.check(predicate)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

@bot.event
async def on_guild_channel_create(channel):
    if 'anti_nuke' in anti_nuke.get(channel.guild.id, {}):
        anti_nuke[channel.guild.id]['changes'] += 1
        if anti_nuke[channel.guild.id]['changes'] > 5:
            await handle_nuke(channel.guild)

@bot.event
async def on_guild_channel_delete(channel):
    if 'anti_nuke' in anti_nuke.get(channel.guild.id, {}):
        anti_nuke[channel.guild.id]['changes'] += 1
        if anti_nuke[channel.guild.id]['changes'] > 5:
            await handle_nuke(channel.guild)

@bot.event
async def on_guild_role_create(role):
    if 'anti_nuke' in anti_nuke.get(role.guild.id, {}):
        anti_nuke[role.guild.id]['changes'] += 1
        if anti_nuke[role.guild.id]['changes'] > 5:
            await handle_nuke(role.guild)

@bot.event
async def on_guild_role_delete(role):
    if 'anti_nuke' in anti_nuke.get(role.guild.id, {}):
        anti_nuke[role.guild.id]['changes'] += 1
        if anti_nuke[role.guild.id]['changes'] > 5:
            await handle_nuke(role.guild)

async def handle_nuke(guild):
    await revert_changes(guild)
    bot_user = guild.me
    if bot_user:
        await guild.ban(bot_user)
    adder = bot_adders.get(guild.id)
    if adder:
        adder_user = guild.get_member(adder)
        if adder_user:
            await guild.ban(adder_user)
    owner = guild.owner
    if owner:
        await owner.send(f"The server {guild.name} has been nuked. The bot was banned, and the user who added the bot was also banned. User who added the bot: {adder_user}")

async def revert_changes(guild):
    channels = [channel for channel in guild.channels if isinstance(channel, discord.TextChannel)]
    roles = [role for role in guild.roles]
    for channel in channels:
        await guild.create_text_channel(channel.name)
    for role in roles:
        await guild.create_role(name=role.name)
    if guild.icon:
        await guild.edit(icon=guild.icon)
    if guild.banner:
        await guild.edit(banner=guild.banner)

@bot.command()
@commands.has_permissions(administrator=True)
async def enable_anti_nuke(ctx):
    anti_nuke[ctx.guild.id] = {'changes': 0}
    bot_adders[ctx.guild.id] = None
    await ctx.send("Anti-Nuke system enabled.")

@bot.command()
@commands.has_permissions(administrator=True)
async def disable_anti_nuke(ctx):
    if ctx.guild.id in anti_nuke:
        del anti_nuke[ctx.guild.id]
        await ctx.send("Anti-Nuke system disabled.")

@bot.command()
@commands.has_permissions(administrator=True)
async def set_bot_adder(ctx, user: discord.User):
    bot_adders[ctx.guild.id] = user.id
    await ctx.send(f"User {user} set as the bot adder.")

@bot.command()
@commands.has_permissions(administrator=True)
async def check_bot_adder(ctx):
    adder_id = bot_adders.get(ctx.guild.id)
    if adder_id:
        adder = ctx.guild.get_member(adder_id)
        if adder:
            await ctx.send(f"User who added the bot: {adder}")
        else:
            await ctx.send(f"User ID {adder_id} not found in the server.")
    else:
        await ctx.send("No bot adder set for this server.")


@bot.command()
async def ping(ctx):
    await ctx.send(f'Pong! Latency is {round(bot.latency * 1000)}ms')

@bot.command()
@has_permissions(administrator=True)
async def ban(ctx, user: discord.User, *, reason: str = "No reason provided"):
    await ctx.guild.ban(user, reason=reason)
    await ctx.send(f'Banned {user.mention} for {reason}')

@bot.command()
@has_permissions(administrator=True)
async def unban(ctx, user_id: int):
    user = await bot.fetch_user(user_id)
    await ctx.guild.unban(user)
    await ctx.send(f'Unbanned {user.mention}')

@bot.command()
@has_permissions(administrator=True)
async def kick(ctx, user: discord.User, *, reason: str = "No reason provided"):
    await ctx.guild.kick(user, reason=reason)
    await ctx.send(f'Kicked {user.mention} for {reason}')

@bot.command()
@has_permissions(administrator=True)
async def mute(ctx, user: discord.Member, duration: int, *, reason: str = "No reason provided"):
    role = discord.utils.get(ctx.guild.roles, name='Muted')
    if not role:
        role = await ctx.guild.create_role(name='Muted')
        for channel in ctx.guild.channels:
            await channel.set_permissions(role, speak=False, send_messages=False)
    await user.add_roles(role)
    await ctx.send(f'{user.mention} has been muted for {duration} minutes for {reason}')
    await asyncio.sleep(duration * 60)
    await user.remove_roles(role)
    await ctx.send(f'{user.mention} has been unmuted')

@bot.command()
@has_permissions(administrator=True)
async def unmute(ctx, user: discord.Member):
    role = discord.utils.get(ctx.guild.roles, name='Muted')
    if role in user.roles:
        await user.remove_roles(role)
        await ctx.send(f'{user.mention} has been unmuted')

@bot.command()
@has_permissions(administrator=True)
async def timeout(ctx, user: discord.Member, duration: int):
    await user.edit(timeout_until=discord.utils.utcnow() + discord.timedelta(minutes=duration))
    await ctx.send(f'{user.mention} has been timed out for {duration} minutes')

@bot.command()
@has_permissions(administrator=True)
async def untimeout(ctx, user: discord.Member):
    await user.edit(timeout_until=None)
    await ctx.send(f'{user.mention} has been untimed out')

@bot.command()
@has_permissions(administrator=True)
async def warn(ctx, user: discord.Member, *, reason: str = "No reason provided"):
    guild_id = ctx.guild.id
    if guild_id not in warns:
        warns[guild_id] = {}
    if user.id not in warns[guild_id]:
        warns[guild_id][user.id] = []
    warns[guild_id][user.id].append(reason)
    
    user_warns = len(warns[guild_id][user.id])
    
    if guild_id in punishments:
        for limit, punishment in sorted(punishments[guild_id].items()):
            if user_warns == limit:
                if punishment['action'] == 'mute':
                    await mute(ctx, user, punishment.get('duration', 1440), punishment.get('reason', 'Warn limit reached'))
                elif punishment['action'] == 'ban':
                    await ctx.guild.ban(user, reason=punishment.get('reason', 'Warn limit reached'))
                break

    await ctx.send(f'Warned {user.mention} for {reason}. Total warns: {user_warns}')

@bot.command()
@has_permissions(administrator=True)
async def add_punishment(ctx, warn_limit: int, action: str, duration: int = None, *, reason: str = "No reason provided"):
    guild_id = ctx.guild.id
    if guild_id not in punishments:
        punishments[guild_id] = {}
    punishments[guild_id][warn_limit] = {'action': action, 'duration': duration, 'reason': reason}
    await ctx.send(f'Punishment for {warn_limit} warns set to {action} with duration {duration} and reason: {reason}')

@bot.command()
@has_permissions(administrator=True)
async def clear_punishments(ctx):
    guild_id = ctx.guild.id
    if guild_id in punishments:
        punishments[guild_id] = {}
        await ctx.send('All punishments cleared.')
    else:
        await ctx.send('No punishments to clear.')

@bot.command()
@has_permissions(administrator=True)
async def check_warns(ctx, user: discord.Member):
    guild_id = ctx.guild.id
    if guild_id in warns and user.id in warns[guild_id]:
        warns_list = warns[guild_id][user.id]
        await ctx.send(f'{user.mention} has {len(warns_list)} warns: {", ".join(warns_list)}')
    else:
        await ctx.send(f'{user.mention} has no warns')

@bot.command()
@has_permissions(administrator=True)
async def clear_warn(ctx, user: discord.Member, warn_id: int):
    guild_id = ctx.guild.id
    if guild_id in warns and user.id in warns[guild_id] and 0 <= warn_id < len(warns[guild_id][user.id]):
        del warns[guild_id][user.id][warn_id]
        await ctx.send(f'Cleared warn {warn_id} for {user.mention}')
    else:
        await ctx.send('Invalid warn ID')

@bot.command()
@has_permissions(administrator=True)
async def purge(ctx, amount: int):
    await ctx.channel.purge(limit=amount)
    await ctx.send(f'Purged {amount} messages')

@bot.command()
async def afk(ctx, *, reason: str = "No reason provided"):
    user_afk[ctx.author.id] = reason
    await ctx.send(f'{ctx.author.mention} is now AFK: {reason}')

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    guild_id = message.guild.id
    
    if guild_id in blacklist:
        for word in blacklist[guild_id]:
            if word in message.content.lower():
                await message.delete()
                await message.channel.send(f'{message.author.mention}, your message contained blacklisted words.')
                break

    if guild_id in triggers:
        for trigger, response in triggers[guild_id].items():
            if trigger in message.content.lower():
                await message.channel.send(response)
                break

    if message.author.id in user_afk:
        del user_afk[message.author.id]
        await message.channel.send(f'Welcome back, {message.author.mention}!')

    if guild_id in mod_log:
        log_channel = bot.get_channel(mod_log[guild_id])
        if log_channel:
            await log_channel.send(f'Message from {message.author} deleted in {message.channel.name}: {message.content}')

    if guild_id in auto_mod_links:
        if any(word in message.content.lower() for word in auto_mod_links[guild_id]):
            await message.delete()
            await message.channel.send(f'{message.author.mention}, your message contained links which are not allowed.')
    
    if guild_id in auto_mod_nsfw:
        if any(word in message.content.lower() for word in auto_mod_nsfw[guild_id]):
            await message.delete()
            await message.channel.send(f'{message.author.mention}, your message contained NSFW content which is not allowed.')
    
    if guild_id in auto_mod_scams:
        if any(word in message.content.lower() for word in auto_mod_scams[guild_id]):
            await message.delete()
            await message.channel.send(f'{message.author.mention}, your message contained scam content which is not allowed.')

    await bot.process_commands(message)

@bot.event
async def on_member_join(member):
    if member.guild.id in server_data and 'welcome_channel' in server_data[member.guild.id]:
        channel_id = server_data[member.guild.id]['welcome_channel']
        channel = bot.get_channel(channel_id)
        if channel:
            await channel.send(f'Welcome to the server, {member.mention}!')

@bot.command()
@has_permissions(administrator=True)
async def setwelcomechannel(ctx, channel: discord.TextChannel):
    guild_id = ctx.guild.id
    if guild_id not in server_data:
        server_data[guild_id] = {}
    server_data[guild_id]['welcome_channel'] = channel.id
    await ctx.send(f'Welcome channel set to {channel.mention}')
@bot.command()
@has_permissions(administrator=True)
async def setmodlog(ctx, channel: discord.TextChannel):
    guild_id = ctx.guild.id
    if guild_id not in server_data:
        server_data[guild_id] = {}
    server_data[guild_id]['mod_log'] = channel.id
    await ctx.send(f'Moderation log channel set to {channel.mention}')

@bot.command()
@has_permissions(administrator=True)
async def add_blacklist(ctx, *, word: str):
    guild_id = ctx.guild.id
    if guild_id not in blacklist:
        blacklist[guild_id] = []
    blacklist[guild_id].append(word.lower())
    await ctx.send(f'Added `{word}` to blacklist.')

@bot.command()
@has_permissions(administrator=True)
async def remove_blacklist(ctx, *, word: str):
    guild_id = ctx.guild.id
    if guild_id in blacklist and word.lower() in blacklist[guild_id]:
        blacklist[guild_id].remove(word.lower())
        await ctx.send(f'Removed `{word}` from blacklist.')
    else:
        await ctx.send(f'`{word}` is not in the blacklist.')

@bot.command()
@has_permissions(administrator=True)
async def add_trigger(ctx, trigger: str, *, response: str):
    guild_id = ctx.guild.id
    if guild_id not in triggers:
        triggers[guild_id] = {}
    triggers[guild_id][trigger.lower()] = response
    await ctx.send(f'Added trigger `{trigger}` with response `{response}`.')

@bot.command()
@has_permissions(administrator=True)
async def remove_trigger(ctx, trigger: str):
    guild_id = ctx.guild.id
    if guild_id in triggers and trigger.lower() in triggers[guild_id]:
        del triggers[guild_id][trigger.lower()]
        await ctx.send(f'Removed trigger `{trigger}`.')
    else:
        await ctx.send(f'`{trigger}` trigger does not exist.')

@bot.command()
@has_permissions(administrator=True)
async def add_auto_mod_link(ctx, *, link: str):
    guild_id = ctx.guild.id
    if guild_id not in auto_mod_links:
        auto_mod_links[guild_id] = []
    auto_mod_links[guild_id].append(link.lower())
    await ctx.send(f'Added `{link}` to auto-mod links.')

@bot.command()
@has_permissions(administrator=True)
async def remove_auto_mod_link(ctx, *, link: str):
    guild_id = ctx.guild.id
    if guild_id in auto_mod_links and link.lower() in auto_mod_links[guild_id]:
        auto_mod_links[guild_id].remove(link.lower())
        await ctx.send(f'Removed `{link}` from auto-mod links.')
    else:
        await ctx.send(f'`{link}` is not in the auto-mod links.')

@bot.command()
@has_permissions(administrator=True)
async def add_auto_mod_nsfw(ctx, *, word: str):
    guild_id = ctx.guild.id
    if guild_id not in auto_mod_nsfw:
        auto_mod_nsfw[guild_id] = []
    auto_mod_nsfw[guild_id].append(word.lower())
    await ctx.send(f'Added `{word}` to NSFW auto-mod words.')

@bot.command()
@has_permissions(administrator=True)
async def remove_auto_mod_nsfw(ctx, *, word: str):
    guild_id = ctx.guild.id
    if guild_id in auto_mod_nsfw and word.lower() in auto_mod_nsfw[guild_id]:
        auto_mod_nsfw[guild_id].remove(word.lower())
        await ctx.send(f'Removed `{word}` from NSFW auto-mod words.')
    else:
        await ctx.send(f'`{word}` is not in the NSFW auto-mod words.')

@bot.command()
@has_permissions(administrator=True)
async def add_auto_mod_scams(ctx, *, word: str):
    guild_id = ctx.guild.id
    if guild_id not in auto_mod_scams:
        auto_mod_scams[guild_id] = []
    auto_mod_scams[guild_id].append(word.lower())
    await ctx.send(f'Added `{word}` to scam auto-mod words.')

@bot.command()
@has_permissions(administrator=True)
async def remove_auto_mod_scams(ctx, *, word: str):
    guild_id = ctx.guild.id
    if guild_id in auto_mod_scams and word.lower() in auto_mod_scams[guild_id]:
        auto_mod_scams[guild_id].remove(word.lower())
        await ctx.send(f'Removed `{word}` from scam auto-mod words.')
    else:
        await ctx.send(f'`{word}` is not in the scam auto-mod words.')
     
        @bot.command()
@commands.has_permissions(administrator=True)
async def enable_anti_nuke(ctx):
    anti_nuke[ctx.guild.id] = {'changes': 0}
    bot_adders[ctx.guild.id] = None
    await ctx.send("Anti-Nuke system enabled.")

@bot.command()
@commands.has_permissions(administrator=True)
async def disable_anti_nuke(ctx):
    if ctx.guild.id in anti_nuke:
        del anti_nuke[ctx.guild.id]
        await ctx.send("Anti-Nuke system disabled.")

@bot.command()
@commands.has_permissions(administrator=True)
async def set_bot_adder(ctx, user: discord.User):
    bot_adders[ctx.guild.id] = user.id
    await ctx.send(f"User {user} set as the bot adder.")

@bot.command()
@commands.has_permissions(administrator=True)
async def check_bot_adder(ctx):
    adder_id = bot_adders.get(ctx.guild.id)
    if adder_id:
        adder = ctx.guild.get_member(adder_id)
        if adder:
            await ctx.send(f"User who added the bot: {adder}")
        else:
            await ctx.send(f"User ID {adder_id} not found in the server.")
    else:
        await ctx.send("No bot adder set for this server.")
        
@bot.command()
@commands.has_permissions(administrator=True)
async def copy_server(ctx):
    guild = ctx.guild
    data = {
        'name': guild.name,
        'icon': str(guild.icon),
        'banner': str(guild.banner),
        'roles': [role.name for role in guild.roles],
        'channels': {
            'text': [channel.name for channel in guild.text_channels],
            'voice': [channel.name for channel in guild.voice_channels]
        },
        'bots': [{
            'name': member.name,
            'id': member.id,
            'invite': f"https://discord.com/oauth2/authorize?client_id={member.id}&scope=bot" if member.bot else None
        } for member in guild.members if member.bot]
    }
    server_copy_data[guild.id] = data
    await ctx.send("Server data copied successfully.")

@bot.command()
@commands.has_permissions(administrator=True)
async def paste_server(ctx, server_id: int):
    if server_id not in server_data:
        await ctx.send("Server data not found.")
        return

    data = server_copy_data[server_id]
    guild = ctx.guild

    await guild.edit(name=data['name'])
    if data['icon']:
        await guild.edit(icon=data['icon'])
    if data['banner']:
        await guild.edit(banner=data['banner'])
    
    for role_name in data['roles']:
        await guild.create_role(name=role_name)
    
    for channel_name in data['channels']['text']:
        await guild.create_text_channel(name=channel_name)
    for channel_name in data['channels']['voice']:
        await guild.create_voice_channel(name=channel_name)

    owner = guild.owner
    if owner:
        for bot in data['bots']:
            invite_link = bot['invite'] or 'No invite link available'
            await owner.send(f"Bot Name: {bot['name']}\nInvite Link: {invite_link}")
    
    await ctx.send("Server data pasted successfully.")        
    
@bot.command()
async def set_status(ctx, status: str, *, text: str = None):
    if ctx.author.id != ADMIN_ID:
        return await ctx.send("You do not have permission to use this command.")
    
    statuses = {
        "online": discord.Status.online,
        "dnd": discord.Status.dnd,
        "idle": discord.Status.idle,
        "invisible": discord.Status.offline
    }
    if status in statuses:
        await bot.change_presence(status=statuses[status], activity=discord.Game(name=text))
        await ctx.send(f'Status set to {status} with text "{text}"')
    else:
        await ctx.send('Invalid status. Choose from online, dnd, idle, or invisible.')

@bot.command()
async def check_servers(ctx):
    if ctx.author.id != ADMIN_ID:
        return await ctx.send("You do not have permission to use this command.")
    
    servers = [f'{guild.name} (ID: {guild.id})' for guild in bot.guilds]
    await ctx.send('\n'.join(servers) if servers else 'Bot is not in any servers.')

@bot.command()
async def leave_server(ctx, server_id: int):
    if ctx.author.id != ADMIN_ID:
        return await ctx.send("You do not have permission to use this command.")
    
    guild = bot.get_guild(server_id)
    if guild:
        await guild.leave()
        await ctx.send(f'Left the server with ID: {server_id}')
    else:
        await ctx.send('Server not found.')    

@bot.command()
async def xhelp(ctx):
help_mg = """
**Help Commands:**

**Ping**: `?ping` - Check bot latency.

**Ban**: `?ban <user> [reason]` - Ban a user.

**Unban**: `?unban <user_id>` - Unban a user by ID.

**Kick**: `?kick <user> [reason]` - Kick a user.

**Mute**: `?mute <user> <duration> [reason]` - Mute a user.

**Unmute**: `?unmute <user>` - Unmute a user.

**Giveaway**: `?giveaway` - Create a giveaway.

**Timeout**: `?timeout <user> <duration>` - Timeout a user.

**Untimeout**: `?untimeout <user>` - Remove timeout from a user.

**Warn**: `?warn <user> [reason]` - Warn a user.

**Clear_warn**: `?clear_warn <user> [warning_number]` - Delete a specific warning.

**Purge**: `?purge <amount>` - Purge messages.

**AFK**: `?afk [message]` - Set AFK status.

**Createchannel**: `?createchannel <name>` - Create a new text channel.

**Deletechannel**: `?deletechannel <#channel>` - Delete a text channel.

**Spam**: `?spam <message> <count>` - Send a message multiple times.

**DM**: `?dm @user <message>` - Direct message a user.

**Createrole**: `?createrole <name>` - Create a new role.

**Deleterole**: `?deleterole @role` - Delete a role.

**Gay**: `?gay @user` - Send a random 'gayness' percentage message.

**Addrole**: `?addrole @role @user` - Add a role to a user.

**Removerole**: `?removerole @role @user` - Remove a role from a user.

**PFP**: `?pfp @user` - Get the profile picture of a user.

**Snipe**: `?snipe [amount]` - Snipe deleted messages.

**Steal**: `?steal :stickername:` - Steal a sticker.

**Info**: `?info @user` - Get user info.

**Serverinfo**: `?serverinfo` - Get server info.

**Add Trigger**: `?add_trigger <trigger> <response>` - Add a trigger.

**Remove Trigger**: `?remove_trigger <trigger>` - Remove a trigger.

**Set AutoMod**: `?set_automod <word> <punishment>` - Set up auto mod rules.

**Toggle AutoMod**: `?toggle_automod <on/off>` - Enable or disable auto mod.

**Announcement**: `?announcement <title> <points>` - Create an announcement.

**View Announcement**: `?view_announcement` - View announcements.

**Help**: `?help` - Display this help message.
"""
await ctx.send(help_mg)

bot.run('MTI2ODc0MjEzNzEzNTEwNDA0MA.GGuRwX.hINeKU6T6H88LcuGwNyhqXtxYCAia3cbCkwwZ4')

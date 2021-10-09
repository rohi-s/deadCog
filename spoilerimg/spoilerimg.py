import discord
from discord import Webhook, AsyncWebhookAdapter
import asyncio
import requests
import json
import aiohttp
from redbot.core import Config, commands, checks
from redbot.core.bot import Red

import re
from typing import Dict, Final, Optional, TypedDict, Union, cast


button: Final = "\N{WHITE SQUARE BUTTON}"
content_re: Final = re.compile(r"(?i)^(?:image|video)/")


class Settings(TypedDict):
    enabled: bool

class spoilerimg(commands.Cog):
    """Cog to Spoiler Image"""

    def __init__(self, bot: Red):
        super().__init__()
        self.bot: Final = bot
        self.config: Final[Config] = Config.get_conf(
            self, identifier=2_113_674_295, force_registration=True
        )
        self.config.register_guild(**Settings(enabled=False))

    async def initialize(self):
        all_guilds: Dict[int, Settings] = await self.config.all_guilds()
        self.enabled_guilds = {k for k, v in all_guilds.items() if v["enabled"]}

    # This cog does not store any End User Data
    async def red_get_data_for_user(self, *, user_id: int):
        return {}

    async def red_delete_data_for_user(self, *, requester, user_id: int) -> None:
        pass

    async def sendhookEngine(self, webhook, messageObj, webhookText=None, webhookUser=None, webhookAvatar=None):
        # Start webhook session
        async with aiohttp.ClientSession() as session:
            # Check for attachments
            if messageObj.attachments:
                # Then send each attachment in separate messages
                for msgAttach in messageObj.attachments:
                    try:
                        await webhook.send(
                            webhookText,
                            username=webhookUser,
                            avatar_url=webhookAvatar,
                            file=await msgAttach.to_file(spoiler=True)
                        )
                    except:
                        # Couldn't send, retry sending file as url only
                        await webhook.send(
                            "File: " + str(msgAttach.url),
                            username=webhookUser,
                            avatar_url=webhookAvatar
                        )


    @commands.group(invoke_without_command=True)#.command()
    async def spoiler(self, ctx, *, textmessage=None):
        """Spoiler Image with a command"""

        message = ctx.message
        channel = message.channel

        # Send webhook
        if not any(
                attach.content_type and content_re.match(attach.content_type)
                for attach in message.attachments
        ):
            await channel.send("You didn't attach any images or videos for me to spoil.")
        else:
            webhook = await channel.create_webhook(name=message.author.display_name,avatar=message.author.avatar_url)
            await self.sendhookEngine(webhook, message, textmessage, message.author.display_name, message.author.avatar_url)
            await message.delete(delay=0)
            await webhook.delete()

    @commands.admin_or_permissions(manage_messages=True)
    @commands.guild_only()
    @spoiler.command()
    async def button(self, ctx: commands.GuildContext, *, enable: bool):
        """
        Enable or disable the spoiler button for this guild.
        The spoiler button adds \N{WHITE SQUARE BUTTON} as a reaction to any attachments
        sent by members that are on mobile or that are invisible.
        Clicking this button acts as if they used the `[p]spoiler` command.
        """
        guild = ctx.guild
        if enable:
            self.enabled_guilds.add(guild.id)
            await self.config.guild(guild).enabled.set(True)
        else:
            self.enabled_guilds.discard(guild.id)
            await self.config.guild(guild).enabled.set(False)
        await ctx.send(
            f"The {button} spoiler button is {'now' if enable else 'no longer'} enabled"
        )

    @commands.Cog.listener()
    async def on_message_without_command(self, message: discord.Message, content: Optional[str] = ...):
        if content is ...:
            textmessage = message.content
        author = message.author
        if author.bot:
            return
        if not message.attachments:
            return
        guild = message.guild
        if guild and guild.id not in self.enabled_guilds:
            return
        if (
                sum(attach.size for attach in message.attachments)
                > getattr(guild, "filesize_limit", 1 << 23) - 10_000
        ):
            return
        if all(attach.is_spoiler() for attach in message.attachments):
            return
        me: Union[discord.ClientUser, discord.Member] = (message.guild or message.channel).me  # type: ignore
        # 0x2040 - add_reactions, manage_messages
        if guild and message.channel.permissions_for(me).value & 0x2040 != 0x2040:  # type: ignore
            return
        for dg in [guild] if guild else filter(None, map(self.bot.get_guild, self.enabled_guilds)):
            if (dm := dg.get_member(author.id)) and not await self.bot.cog_disabled_in_guild(
                    self, dg
            ):
                break
        else:
            return
        if dm.status != discord.Status.offline and not dm.is_on_mobile():
            return
        try:
            await message.add_reaction(button)
        except discord.Forbidden:
            return
        try:
            await self.bot.wait_for(
                "reaction_add", timeout=10, check=lambda r, u: r.message == message and u == author
            )
        except asyncio.TimeoutError:
            await message.remove_reaction(button, me)
        else:
            channel = message.channel

            webhook = await channel.create_webhook(name=message.author.display_name,avatar=message.author.avatar_url)
            await self.sendhookEngine(webhook, message, textmessage, message.author.display_name, message.author.avatar_url)
            await message.delete(delay=0)
            await webhook.delete()

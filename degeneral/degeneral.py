#general cog but no hug

import discord
from discord import Webhook, AsyncWebhookAdapter
import asyncio
import requests
import json
import urllib.parse
import aiohttp
from redbot.core import Config, commands, checks
from redbot.core.i18n import Translator, cog_i18n
from redbot.core.utils.menus import menu, DEFAULT_CONTROLS
from redbot.core.utils.chat_formatting import (
    bold,
    escape,
    italics,
    humanize_number,
    humanize_timedelta,
)

_ = T_ = Translator("General", __file__)

@cog_i18n(_)
class deGen(commands.Cog):
    """My custom General cog"""
    
    global _
    _ = lambda s: s
    
    _ = T_

    def __init__(self, bot):
        self.bot = bot
        
    # This cog does not store any End User Data
    async def red_get_data_for_user(self, *, user_id: int):
        return {}
    async def red_delete_data_for_user(self, *, requester, user_id: int) -> None:
        pass
    
    async def sendhookEngine(self, ctx, messageObj, member: discord.Member, channel: discord.TextChannel=None, webhookText=None, webhookUser=None, webhookAvatar=None):
        if channel == None:
            channel = ctx.message.channel
        # Start webhook session
        async with aiohttp.ClientSession() as session:
            
            webhook = await ctx.channel.create_webhook(name=member.name)

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
                            "File: "+str(msgAttach.url), 
                            username=webhookUser,
                            avatar_url=webhookAvatar
                        )
            else:
                await ctx.send("You didn't attach any images or videos for me to spoil.")
                
            
            webhooks = await ctx.channel.webhooks()
            for webhook in webhooks:
                await webhook.delete()
            


    @commands.command()
    async def urban(self, ctx, *, word):
        """Search the Urban Dictionary.
        This uses the unofficial Urban Dictionary API.
        """

        try:
            url = "https://api.urbandictionary.com/v0/define"

            params = {"term": str(word).lower()}

            headers = {"content-type": "application/json"}

            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params) as response:
                    data = await response.json()

        except aiohttp.ClientError:
            await ctx.send(
                _("No Urban Dictionary entries were found, or there was an error in the process.")
            )
            return

        if data.get("error") != 404:
            if not data.get("list"):
                return await ctx.send(_("No Urban Dictionary entries were found."))
            if await ctx.embed_requested():
                # a list of embeds
                embeds = []
                for ud in data["list"]:
                    embed = discord.Embed(color=await ctx.embed_color())
                    title = _("{word} by {author}").format(
                        word=ud["word"].capitalize(), author=ud["author"]
                    )
                    if len(title) > 256:
                        title = "{}...".format(title[:253])
                    embed.title = title
                    embed.url = ud["permalink"]

                    description = _("{definition}\n\n**Example:** {example}").format(**ud)
                    if len(description) > 2048:
                        description = "{}...".format(description[:2045])
                    embed.description = description

                    embed.set_footer(
                        text=_(
                            "{thumbs_down} Down / {thumbs_up} Up, Powered by Urban Dictionary."
                        ).format(**ud)
                    )
                    embeds.append(embed)

                if embeds is not None and len(embeds) > 0:
                    await menu(
                        ctx,
                        pages=embeds,
                        controls=DEFAULT_CONTROLS,
                        message=None,
                        page=0,
                        timeout=30,
                    )
            else:
                messages = []
                for ud in data["list"]:
                    ud.setdefault("example", "N/A")
                    message = _(
                        "<{permalink}>\n {word} by {author}\n\n{description}\n\n"
                        "{thumbs_down} Down / {thumbs_up} Up, Powered by Urban Dictionary."
                    ).format(word=ud.pop("word").capitalize(), description="{description}", **ud)
                    max_desc_len = 2000 - len(message)

                    description = _("{definition}\n\n**Example:** {example}").format(**ud)
                    if len(description) > max_desc_len:
                        description = "{}...".format(description[: max_desc_len - 3])

                    message = message.format(description=description)
                    messages.append(message)

                if messages is not None and len(messages) > 0:
                    await menu(
                        ctx,
                        pages=messages,
                        controls=DEFAULT_CONTROLS,
                        message=None,
                        page=0,
                        timeout=30,
                    )
        else:
            await ctx.send(
                _("No Urban Dictionary entries were found, or there was an error in the process.")
            )
            
    @commands.command()
    async def spoiler(self, ctx, *, webhookText=None):
        """Spoiler Image with a command"""

        message = ctx.message

        # Send webhook
        try:
            await self.sendhookEngine(message, webhookText, message.author.display_name, message.author.avatar_url)
        except:
            await ctx.send("Oops, an error occurred :'(")
        else:
            await ctx.message.delete(delay=0)

from .spoilerimg import spoilerimg

async def setup(bot):
    spoilerIMG = spoilerimg(bot)
    await spoilerIMG.initialize()
    bot.add_cog(spoilerIMG)  

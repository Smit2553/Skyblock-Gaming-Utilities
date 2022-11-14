import discord
from discord.ext import commands


class BugReports(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    class BugModal(discord.ui.Modal):
        def __init__(self, bot):
            super().__init__(title="Bug Report")
            self.bot = bot
            self.add_item(discord.ui.InputText(label="Which command did the bug occur in?"))
            self.add_item(discord.ui.InputText(label="Describe the bug", style=discord.InputTextStyle.long))

        async def callback(self, interaction: discord.Interaction):
            embed = discord.Embed(title="Bug Report", description=f"User: {str(interaction.user)}", color=0xee6940)
            embed.add_field(name="Command", value=self.children[0].value)
            embed.add_field(name="Description", value=self.children[1].value)
            await interaction.response.send_message(embed=embed)
            channel = self.bot.get_channel(1039209390676381696)
            await channel.send(embed=embed)

    @discord.slash_command(description="Report a bug to the developers.")
    async def bugreport(self, ctx):
        modal = self.BugModal(self.bot)
        await ctx.send_modal(modal)


def setup(bot):
    bot.add_cog(BugReports(bot))

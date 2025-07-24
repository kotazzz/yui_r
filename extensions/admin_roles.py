from typing import Callable
import disnake
from disnake.ext import commands
from config import get_settings

def is_admin[T]() -> Callable[[T], T]:
    async def predicate(inter: disnake.ApplicationCommandInteraction) -> bool:
        if await inter.bot.is_owner(inter.author):  # type: ignore
            return True
        admin_roles: list[int] | None = get_settings().get("admin_roles", default=[], type_=list)
        if not admin_roles:
            return False
        if not isinstance(inter.author, disnake.Member):
            return False
        return any(role.id in admin_roles for role in inter.author.roles)
    return commands.check(predicate) # type: ignore

class AdminRoles(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.slash_command(description="Добавить админскую роль")
    @is_admin()
    async def add_admin_role(self, inter: disnake.ApplicationCommandInteraction, role: disnake.Role):
        roles = set(get_settings().get("admin_roles", default=[], type_=list) or [])
        roles.add(role.id)
        get_settings().set("admin_roles", list(roles))
        await inter.response.send_message(f"Добавлена админ-роль: {role.mention}", ephemeral=True)
    @commands.slash_command(description="Удалить админскую роль")
    @is_admin()
    async def remove_admin_role(self, inter: disnake.ApplicationCommandInteraction, role: disnake.Role):
        roles = set(get_settings().get("admin_roles", default=[], type_=list) or [])
        roles.discard(role.id)
        get_settings().set("admin_roles", list(roles))
        await inter.response.send_message(f"Удалена админ-роль: {role.mention}", ephemeral=True)
        await inter.response.send_message(f"Удалена админ-роль: {role.mention}", ephemeral=True)

    @commands.slash_command(description="Список админских ролей")
    async def list_admin_roles(self, inter: disnake.ApplicationCommandInteraction):
        roles = get_settings().get("admin_roles", default=[], type_=list)
        if not roles:
            await inter.response.send_message("Нет админских ролей.", ephemeral=True)
            return
        mentions = [f"<@&{rid}>" for rid in roles]
        await inter.response.send_message("Админские роли: " + ", ".join(mentions), ephemeral=True)

def setup(bot: commands.Bot):
    bot.add_cog(AdminRoles(bot))

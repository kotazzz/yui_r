import disnake
from disnake.ext import commands
from disnake import TextChannel, Role
from config import get_settings
from extensions.admin_roles import is_admin

from typing import Any

# GUILD_ID убран, используйте настройки или переменные окружения для получения ID сервера


def get_local_settings(guild_id: int) -> dict[str, Any]:
    settings: dict[str, Any] | None = get_settings().get(f"verification.{guild_id}", default={}, type_=dict[str, Any])
    if settings is None:
        settings = {}
    return settings

def set_local_setting(guild_id: int, key: str, value: Any) -> None:
    settings = get_local_settings(guild_id)
    settings[key] = value
    get_settings().set(f"verification.{guild_id}", settings)

# --- Persistent View ---
class VerificationView(disnake.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @disnake.ui.button(label="Пройти верификацию", style=disnake.ButtonStyle.green, custom_id="verification:start")
    async def start(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        modal = VerificationModal()
        await inter.response.send_modal(modal)

class VerificationModal(disnake.ui.Modal):
    def __init__(self):
        components = [
            disnake.ui.TextInput(label="Возраст", custom_id="age", style=disnake.TextInputStyle.short, required=True),
            disnake.ui.TextInput(label="Согласен с правилами? (да/нет)", custom_id="rules", style=disnake.TextInputStyle.short, required=True),
            disnake.ui.TextInput(label="Творческие увлечения (если есть)", custom_id="hobbies", style=disnake.TextInputStyle.paragraph, required=False),
        ]
        super().__init__(title="Верификация", components=components)

    async def callback(self, inter: disnake.ModalInteraction):
        if not inter.guild:
            await inter.response.send_message("Сервер не найден.", ephemeral=True)
            return
        guild_id = inter.guild.id
        local_settings = get_local_settings(guild_id)
        mod_channel_id = local_settings.get("mod_channel")
        if not mod_channel_id:
            await inter.response.send_message("Канал модерации не настроен.", ephemeral=True)
            return
        mod_channel = inter.guild.get_channel(mod_channel_id)
        if not mod_channel or not isinstance(mod_channel, disnake.TextChannel):
            await inter.response.send_message("Канал модерации не найден или не поддерживается.", ephemeral=True)
            return
        embed = disnake.Embed(title="Запрос на верификацию", color=disnake.Color.green())
        embed.add_field(name="Пользователь", value=inter.author.mention)
        embed.add_field(name="Возраст", value=inter.text_values["age"])
        embed.add_field(name="Согласен с правилами", value=inter.text_values["rules"])
        embed.add_field(name="Творческие увлечения", value=inter.text_values["hobbies"] or "-")
        view = ModerationView(inter.author.id)
        await mod_channel.send(embed=embed, view=view)
        await inter.response.send_message("Ваша заявка отправлена на рассмотрение.", ephemeral=True)

class ModerationView(disnake.ui.View):
    def __init__(self, user_id: int):
        super().__init__(timeout=None)
        self.user_id = user_id

    @disnake.ui.button(label="Верифицировать", style=disnake.ButtonStyle.green, custom_id="verification:approve")
    async def approve(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        await self._verify(inter, nsfw=False)

    @disnake.ui.button(label="Верифицировать с NSFW", style=disnake.ButtonStyle.red, custom_id="verification:approve_nsfw")
    async def approve_nsfw(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        await self._verify(inter, nsfw=True)

    async def _verify(self, inter: disnake.MessageInteraction, nsfw: bool):
        if not inter.guild:
            await inter.response.send_message("Сервер не найден.", ephemeral=True)
            return
        guild_id = inter.guild.id
        local_settings = get_local_settings(guild_id)
        verified_role_id = local_settings.get("verified_role")
        nsfw_role_id = local_settings.get("nsfw_role")
        member = inter.guild.get_member(self.user_id)
        if not member:
            await inter.response.send_message("Пользователь не найден.", ephemeral=True)
            return
        roles_to_add = []
        if verified_role_id:
            role = inter.guild.get_role(verified_role_id)
            if role:
                roles_to_add.append(role)
        if nsfw and nsfw_role_id:
            role = inter.guild.get_role(nsfw_role_id)
            if role:
                roles_to_add.append(role)
        if roles_to_add:
            await member.add_roles(*roles_to_add, reason="Верификация")
        await inter.message.edit(content=f"Верифицирован: {member.mention} модератором {inter.author.mention}", view=None)
        await inter.response.send_message("Пользователь верифицирован.", ephemeral=True)

# --- Extension ---
class Verification(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.persistent_views_added = False
        
    @commands.Cog.listener()
    async def on_ready(self):
            if not self.persistent_views_added:
                self.bot.add_view(VerificationView())
                self.persistent_views_added = True

    @commands.slash_command(description="Создать кнопку верификации")
    @is_admin()
    async def create_verification(self, inter: disnake.ApplicationCommandInteraction):
        if not inter.guild:
            await inter.response.send_message("Эта команда должна использоваться в сервере.", ephemeral=True)
            return
        local_settings = get_local_settings(inter.guild.id)
        channel_id = local_settings.get("verification_channel")
        if not channel_id:
            await inter.response.send_message("Канал для кнопки не настроен.", ephemeral=True)
            return
        channel = inter.guild.get_channel(channel_id)
        if not channel or not isinstance(channel, disnake.TextChannel):
            await inter.response.send_message("Канал не найден или не поддерживается.", ephemeral=True)
            return
        await channel.send("Нажмите для верификации:", view=VerificationView())
        await inter.response.send_message("Кнопка создана.", ephemeral=True)

    @commands.slash_command(description="Настроить канал для кнопки верификации")
    @is_admin()
    async def set_verification_channel(self, inter: disnake.ApplicationCommandInteraction, channel: TextChannel):
        if not inter.guild:
            await inter.response.send_message("Эта команда должна использоваться в сервере.", ephemeral=True)
            return
        set_local_setting(inter.guild.id, "verification_channel", channel.id)
        await inter.response.send_message(f"Канал для кнопки верификации установлен: {channel.mention}", ephemeral=True)

    @commands.slash_command(description="Настроить канал для модерации")
    @is_admin()
    async def set_mod_channel(self, inter: disnake.ApplicationCommandInteraction, channel: TextChannel):
        if not inter.guild:
            await inter.response.send_message("Эта команда должна использоваться в сервере.", ephemeral=True)
            return
        set_local_setting(inter.guild.id, "mod_channel", channel.id)
        await inter.response.send_message(f"Канал для модерации установлен: {channel.mention}", ephemeral=True)

    @commands.slash_command(description="Настроить роль для верификации")
    @is_admin()
    async def set_verified_role(self, inter: disnake.ApplicationCommandInteraction, role: Role):
        if not inter.guild:
            await inter.response.send_message("Эта команда должна использоваться в сервере.", ephemeral=True)
            return
        set_local_setting(inter.guild.id, "verified_role", role.id)
        await inter.response.send_message(f"Роль для верификации установлена: {role.mention}", ephemeral=True)

    @commands.slash_command(description="Настроить NSFW роль для верификации")
    @is_admin()
    async def set_nsfw_role(self, inter: disnake.ApplicationCommandInteraction, role: Role):
        if not inter.guild:
            await inter.response.send_message("Эта команда должна использоваться в сервере.", ephemeral=True)
            return
        set_local_setting(inter.guild.id, "nsfw_role", role.id)
        await inter.response.send_message(f"NSFW роль для верификации установлена: {role.mention}", ephemeral=True)


def setup(bot: commands.Bot):
    bot.add_cog(Verification(bot))

# language: Python 3.11, file: bot.py
import sys, types
try:
    import audioop
except ImportError:
    sys.modules["audioop"] = types.ModuleType("audioop")

import os, asyncio, discord
from datetime import datetime, timezone
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

TOKEN          = os.getenv("DISCORD_TOKEN")
GUILD_ID       = int(os.getenv("GUILD_ID", "1532403639115845742"))
ADMIN_ID       = int(os.getenv("ADMIN_ID", "1518482876566605877"))
VIP_CHANNEL_ID = int(os.getenv("VIP_CHANNEL_ID", "1553383142377914389"))

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
bot = commands.Bot(command_prefix="!", intents=intents)


async def log_admin(user, guild, siparis, odeme, adres):
    try:
        admin = await bot.fetch_user(ADMIN_ID)
    except Exception:
        return
    e = discord.Embed(title="🍔 Yemek İhbarı", color=0xe67e22,
                      timestamp=datetime.now(timezone.utc))
    e.add_field(name="Kullanıcı",
                value=f"{user.mention}\n`{user.name}` (`{user.id}`)",
                inline=False)
    if guild:
        e.add_field(name="Sunucu", value=guild.name, inline=True)
    e.add_field(name="Sipariş", value=f"`{siparis}`", inline=False)
    e.add_field(name="Ödeme", value=f"`{odeme}`", inline=True)
    e.add_field(name="Adres", value=f"`{adres}`", inline=False)
    try:
        await admin.send(embed=e)
    except Exception:
        pass


class AdresModal(discord.ui.Modal, title="📍 Adres Bilgisi"):
    adres = discord.ui.TextInput(
        label="Adres",
        placeholder="Atatürk Cad. No:5 D:3 Kadıköy/İstanbul",
        required=True, max_length=300,
    )

    def __init__(self, siparis, odeme):
        super().__init__()
        self.siparis = siparis
        self.odeme = odeme

    async def on_submit(self, i):
        await i.response.defer(thinking=True, ephemeral=True)

        e1 = discord.Embed(
            title="🍔 SİPARİŞ ALINDI",
            description=(
                f"**Sipariş:** `{self.siparis}`\n"
                f"**Ödeme:** `{self.odeme}`\n"
                f"**Adres:** `{self.adres.value}`"
            ),
            color=0xf39c12,
        )
        e1.add_field(name="Durum",
                     value="⏳ Hazırlanıyor... 5 dakika bekleyin.",
                     inline=False)
        e1.set_footer(text="/Asayissube — Yemek İhbar Sistemi")
        await i.followup.send(embed=e1, ephemeral=True)

        await log_admin(i.user, i.guild, self.siparis, self.odeme,
                        self.adres.value)

        await asyncio.sleep(300)

        e2 = discord.Embed(
            title="✅ SİPARİŞ OLUŞTURULDU",
            description=(
                f"**Sipariş:** `{self.siparis}`\n"
                f"**Ödeme:** `{self.odeme}`\n"
                f"**Adres:** `{self.adres.value}`"
            ),
            color=0x2ecc71,
        )
        e2.add_field(name="Durum",
                     value="✅ Yemek ihbarınız iletilmiştir.",
                     inline=False)
        e2.add_field(name="Tahmini Teslimat",
                     value="🕐 20-30 dakika", inline=True)
        e2.set_footer(text="/Asayissube — Yemek İhbar Sistemi")
        try:
            await i.followup.send(embed=e2, ephemeral=True)
        except Exception:
            pass


class AdresView(discord.ui.View):
    def __init__(self, siparis, odeme):
        super().__init__(timeout=300)
        self.siparis = siparis
        self.odeme = odeme

    @discord.ui.button(label="📍 Adres Gir", style=discord.ButtonStyle.success)
    async def adres_btn(self, i, b):
        await i.response.send_modal(
            AdresModal(siparis=self.siparis, odeme=self.odeme)
        )


class YemekModal(discord.ui.Modal, title="🍔 Yemek İhbar"):
    siparis = discord.ui.TextInput(
        label="Sipariş",
        placeholder="5 döner 3 ayran",
        required=True, max_length=200,
    )
    odeme = discord.ui.TextInput(
        label="Ödeme yöntemi",
        placeholder="Kapıda Ödeme",
        required=False,
        default="Kapıda Ödeme",
        max_length=50,
    )

    async def on_submit(self, i):
        await i.response.defer(thinking=True, ephemeral=True)
        sip = self.siparis.value.strip()
        odm = (self.odeme.value or "Kapıda Ödeme").strip()

        view = AdresView(siparis=sip, odeme=odm)
        await i.followup.send(
            f"**Sipariş:** `{sip}`\n"
            f"**Ödeme:** `{odm}`\n\n"
            f"📍 Şimdi adres bilgisini gir:",
            view=view,
            ephemeral=True,
        )


class PanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Yemek İhbar", emoji="🍔",
                       style=discord.ButtonStyle.danger,
                       custom_id="btn_yemek")
    async def b_yemek(self, i, b):
        await i.response.send_modal(YemekModal())


def panel_embed():
    e = discord.Embed(
        title="🍔 Yemek İhbar Paneli",
        description=(
            "Butona bas, siparişini yaz, adresini gir.\n"
            "5 dakika sonra onay DM'ine gelir.\n"
            "**Sonuç sadece sana görünür.**"
        ),
        color=0xe67e22,
    )
    e.add_field(name="🍔 Yemek İhbar",
                value="Sipariş + adres + kapıda ödeme",
                inline=False)
    e.set_footer(text="/Asayissube")
    return e


@bot.tree.command(name="panel", description="Yemek ihbar panelini aç")
@app_commands.default_permissions(administrator=True)
async def panel_cmd(i: discord.Interaction):
    if i.user.id != ADMIN_ID:
        await i.response.send_message("yetkin yok.", ephemeral=True)
        return
    if GUILD_ID and (i.guild is None or i.guild.id != GUILD_ID):
        await i.response.send_message("yetkisiz sunucu.", ephemeral=True)
        return
    if VIP_CHANNEL_ID and i.channel.id != VIP_CHANNEL_ID:
        await i.response.send_message(
            f"sadece <#{VIP_CHANNEL_ID}> kanalında çalışır.", ephemeral=True)
        return
    await i.response.send_message(embed=panel_embed(), view=PanelView())


@bot.event
async def on_ready():
    print(f"[+] {bot.user} online")
    try:
        await bot.change_presence(status=discord.Status.online,
                                  activity=discord.Game(name="Yemek İhbar"))
    except Exception:
        pass
    bot.add_view(PanelView())
    if GUILD_ID:
        for g in list(bot.guilds):
            if g.id != GUILD_ID:
                try:
                    await g.leave()
                except Exception:
                    pass
        guild = discord.Object(id=GUILD_ID)
        bot.tree.copy_global_to(guild=guild)
        await bot.tree.sync(guild=guild)
        print(f"[+] synced: {GUILD_ID}")
    else:
        await bot.tree.sync()


if __name__ == "__main__":
    if not TOKEN:
        raise SystemExit("DISCORD_TOKEN eksik")
    bot.run(TOKEN)

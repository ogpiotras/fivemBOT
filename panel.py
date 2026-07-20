import discord
import db

def _kat(emoji):
    return {"🔫": "Broń", "📦": "Amunicja", "💀": "Dodatki", "💊": "Dragi"}.get(emoji, "Inne")

KATEGORIE = {}
for _nazwa, _emoji in db.ITEMY:
    KATEGORIE.setdefault(_kat(_emoji), []).append((_nazwa, _emoji))

def fmt(n):
    return f"{n:,}".replace(",", " ")

def buduj_embed(guild_id):
    stan = db.get_stan(guild_id)
    embed = discord.Embed(title="📦 Magazyn", color=0x2b2d31)
    for kat, itemy in KATEGORIE.items():
        linie = [f"{emoji} **{nazwa}** — `{fmt(stan.get(nazwa, 0))} szt.`"
                 for nazwa, emoji in itemy]
        embed.add_field(name=kat, value="\n".join(linie), inline=False)
    return embed

class MagazynView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Dodaj", emoji="➕",
                       style=discord.ButtonStyle.success, custom_id="mag_dodaj")
    async def dodaj(self, interaction, button):
        await interaction.response.send_message(
            "Wybierz kategorię:",
            view=KategoriaView("dodaj", interaction.message),
            ephemeral=True,
        )

    @discord.ui.button(label="Pobierz", emoji="➖",
                       style=discord.ButtonStyle.danger, custom_id="mag_pobierz")
    async def pobierz(self, interaction, button):
        await interaction.response.send_message(
            "Wybierz kategorię:",
            view=KategoriaView("pobierz", interaction.message),
            ephemeral=True,
        )

    @discord.ui.button(label="Historia", emoji="📜",
                       style=discord.ButtonStyle.secondary, custom_id="mag_historia")
    async def historia(self, interaction, button):
        rows = db.get_historia(interaction.guild_id, 30)
        if not rows:
            await interaction.response.send_message("Brak operacji.", ephemeral=True)
            return

        linie = []
        for r in rows:
            znak = "➕" if r["zmiana"] > 0 else "➖"

            powod_txt = f" 📝 *{r['powod']}*" if r['powod'] else ""

            linie.append(f"{znak} **{r['user_tag']}** — {r['nazwa']}: "
                         f"{r['zmiana']:+} (stan: {r['ilosc_po']}){powod_txt} · {r['czas']}")

        opis = "\n".join(linie)[:4000]
        embed = discord.Embed(title="📜 Historia (ostatnie 30)",
                              description=opis, color=0x2b2d31)
        await interaction.response.send_message(embed=embed, ephemeral=True)


class KategoriaView(discord.ui.View):
    def __init__(self, tryb, panel_msg):
        super().__init__(timeout=120)
        self.add_item(KategoriaSelect(tryb, panel_msg))


class KategoriaSelect(discord.ui.Select):
    def __init__(self, tryb, panel_msg):
        self.tryb = tryb
        self.panel_msg = panel_msg
        opcje = [discord.SelectOption(label=kat) for kat in KATEGORIE]
        super().__init__(placeholder="Kategoria...", options=opcje)

    async def callback(self, interaction):
        kat = self.values[0]
        await interaction.response.edit_message(
            content=f"Wybierz przedmiot ({kat}):",
            view=ItemView(self.tryb, kat, self.panel_msg),
        )


class ItemView(discord.ui.View):
    def __init__(self, tryb, kat, panel_msg):
        super().__init__(timeout=120)
        self.add_item(ItemSelect(tryb, kat, panel_msg))


class ItemSelect(discord.ui.Select):
    def __init__(self, tryb, kat, panel_msg):
        self.tryb = tryb
        self.panel_msg = panel_msg
        opcje = [discord.SelectOption(label=nazwa, emoji=emoji)
                 for nazwa, emoji in KATEGORIE[kat]]
        super().__init__(placeholder="Przedmiot...", options=opcje)

    async def callback(self, interaction):
        await interaction.response.send_modal(
            IloscModal(self.tryb, self.values[0], self.panel_msg))


class IloscModal(discord.ui.Modal):
    def __init__(self, tryb, nazwa, panel_msg):
        tytul = "Dodaj" if tryb == "dodaj" else "Pobierz"
        super().__init__(title=f"{tytul}: {nazwa}"[:45])
        self.tryb = tryb
        self.nazwa = nazwa
        self.panel_msg = panel_msg

        self.pole_ilosc = discord.ui.TextInput(
            label="Ilość",
            placeholder="np. 100",
            style=discord.TextStyle.short
        )
        self.add_item(self.pole_ilosc)

        self.pole_powod = discord.ui.TextInput(
            label="Powód (opcjonalnie)",
            placeholder="np. Wydane dla rekruta...",
            style=discord.TextStyle.short,
            required=False,
            max_length=150
        )
        self.add_item(self.pole_powod)

    async def on_submit(self, interaction):
        try:
            n = int(self.pole_ilosc.value)
            if n <= 0:
                raise ValueError
        except ValueError:
            await interaction.response.send_message(
                "Podaj dodatnią liczbę całkowitą.", ephemeral=True)
            return

        delta = n if self.tryb == "dodaj" else -n

        wpisany_powod = self.pole_powod.value.strip()
        powod_do_bazy = wpisany_powod if wpisany_powod else None

        ok, ilosc_po = db.zmien_ilosc(
            interaction.guild_id, interaction.user.id,
            str(interaction.user), self.nazwa, delta, powod_do_bazy
        )

        if not ok:
            await interaction.response.send_message(
                f"Nie można pobrać {fmt(n)} — w magazynie jest tylko {fmt(ilosc_po)}.",
                ephemeral=True)
            return

        try:
            await self.panel_msg.edit(
                embed=buduj_embed(interaction.guild_id), view=MagazynView())
        except Exception:
            pass

        slowo = "Dodano" if self.tryb == "dodaj" else "Pobrano"
        await interaction.response.send_message(
            f"✅ {slowo} {fmt(n)} × {self.nazwa}. Nowy stan: {fmt(ilosc_po)}.",
            ephemeral=True)
from discord import Embed


def create_embed(title: str, desc: str) -> Embed:
    embed = Embed(title=title, description=desc, color=0x005EBC)
    return embed
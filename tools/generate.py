#!/usr/bin/env python3
"""Generates Eclipsia's eclipse timelines, timing constants, textures and data files.

The eclipse schedule lives here once and is written to both:
  * data/eclipsia/timeline/*.json - the vanilla timeline system darkens the sky,
    lowers sky light and stops monsters burning on both server and client
  * EclipseTimings.java - the same numbers for the Java gameplay code

Run from anywhere:  python3 tools/generate.py   (requires Pillow)
"""
import json
import math
import random
import shutil
from pathlib import Path

from PIL import Image, ImageDraw

MOD_ID = "eclipsia"
ROOT = Path(__file__).resolve().parent.parent
RES = ROOT / "src" / "main" / "resources"
ASSETS = RES / "assets" / MOD_ID
DATA = RES / "data" / MOD_ID
JAVA_OUT = ROOT / "src" / "main" / "java" / "com" / "eclipsia" / "eclipse" / "EclipseTimings.java"

DAY = 24000
# Vanilla's moon timeline repeats every 8 days: day 0 is a full moon, day 4 a new moon.
# Eclipses repeat every two lunar cycles, solar ones on a new moon at noon and
# lunar ones on a full moon at midnight, so the world sees one every 8 days.
PERIOD = 16 * DAY
ECLIPSES = {
    "solar": {"peak": 4 * DAY + 6000, "partial": 1800, "total": 400},
    "lunar": {"peak": 8 * DAY + 18000, "partial": 2400, "total": 800},
}


# --------------------------------------------------------------------------- helpers

def write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2) + "\n", encoding="utf-8")


def rid(path: str) -> str:
    return f"{MOD_ID}:{path}"


def argb_int(hex_rgb: str) -> int:
    """Opaque ARGB as the signed int vanilla uses for cloud_color."""
    value = 0xFF000000 | int(hex_rgb.lstrip("#"), 16)
    return value - (1 << 32)


# --------------------------------------------------------------------------- timelines

def ramp(eclipse, outside, inside):
    """Keyframes that move from `outside` to `inside` over the partial phase and back."""
    peak, partial, total = eclipse["peak"], eclipse["partial"], eclipse["total"]
    return [
        {"ticks": peak - partial, "value": outside},
        {"ticks": peak - total, "value": inside},
        {"ticks": peak + total, "value": inside},
        {"ticks": peak + partial, "value": outside},
    ]


def solar_timeline():
    e = ECLIPSES["solar"]
    return {
        "clock": "minecraft:overworld",
        "period_ticks": PERIOD,
        "tracks": {
            "minecraft:gameplay/sky_light_level": {"keyframes": ramp(e, 1.0, 0.25), "modifier": "multiply"},
            "minecraft:visual/sky_light_factor": {"keyframes": ramp(e, 1.0, 0.3), "modifier": "multiply"},
            "minecraft:visual/sky_light_color": {"keyframes": ramp(e, "#ffffff", "#8a8ab8"), "modifier": "multiply"},
            "minecraft:visual/sky_color": {"keyframes": ramp(e, "#ffffff", "#141a33"), "modifier": "multiply"},
            "minecraft:visual/fog_color": {"keyframes": ramp(e, "#ffffff", "#262a40"), "modifier": "multiply"},
            "minecraft:visual/cloud_color": {
                "keyframes": ramp(e, argb_int("#ffffff"), argb_int("#3a3a4a")), "modifier": "multiply"},
            "minecraft:visual/star_brightness": {"keyframes": ramp(e, 0.0, 0.4), "modifier": "maximum"},
            # Undead don't burn while the sun is hidden.
            "minecraft:gameplay/monsters_burn": {
                "keyframes": [
                    {"ticks": e["peak"] - e["partial"] // 2, "value": False},
                    {"ticks": e["peak"] + e["partial"] // 2, "value": True},
                ],
                "modifier": "and",
            },
        },
    }


def lunar_timeline():
    e = ECLIPSES["lunar"]
    return {
        "clock": "minecraft:overworld",
        "period_ticks": PERIOD,
        "tracks": {
            # The Earth's shadow turns the moonlight blood red.
            "minecraft:visual/sky_light_color": {"keyframes": ramp(e, "#ffffff", "#ff3a2a"), "modifier": "multiply"},
            "minecraft:visual/fog_color": {"keyframes": ramp(e, "#ffffff", "#ff4a4a"), "modifier": "multiply"},
            "minecraft:visual/cloud_color": {
                "keyframes": ramp(e, argb_int("#ffffff"), argb_int("#ff6050")), "modifier": "multiply"},
            "minecraft:visual/star_brightness": {"keyframes": ramp(e, 0.0, 0.85), "modifier": "maximum"},
        },
    }


def java_source():
    s, l = ECLIPSES["solar"], ECLIPSES["lunar"]
    return f"""// GENERATED FILE - do not edit by hand.
// Edit tools/generate.py and run `python3 tools/generate.py` instead.
package com.eclipsia.eclipse;

/** Eclipse timings in overworld clock ticks. Must match data/eclipsia/timeline. */
public final class EclipseTimings {{
    public static final long PERIOD = {PERIOD}L;

    public static final long SOLAR_PEAK = {s["peak"]}L;
    public static final long SOLAR_PARTIAL = {s["partial"]}L;
    public static final long SOLAR_TOTAL = {s["total"]}L;

    public static final long LUNAR_PEAK = {l["peak"]}L;
    public static final long LUNAR_PARTIAL = {l["partial"]}L;
    public static final long LUNAR_TOTAL = {l["total"]}L;

    private EclipseTimings() {{
    }}
}}
"""


# --------------------------------------------------------------------------- textures

def rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def mix(a, b, t):
    return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))


def rgba(c, a=255):
    return (*c, a)


def shard(core, mid, rim, glint):
    """A crystal shard pointing to the top right, edged with a rim colour."""
    img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    mask = Image.new("L", (16, 16))
    ImageDraw.Draw(mask).polygon([(1, 12), (4, 15), (13, 7), (15, 0), (8, 3)], fill=255)
    m, px = mask.load(), img.load()
    for y in range(16):
        for x in range(16):
            if not m[x, y]:
                continue
            edge = any(not (0 <= x + dx < 16 and 0 <= y + dy < 16) or not m[x + dx, y + dy]
                       for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
            side = (x + y) - 15
            px[x, y] = rgba(rim if edge else (mid if side < -1 else core))
    for x, y in ((13, 2), (12, 3), (7, 7)):
        px[x, y] = rgba(glint)
    return img


def noise_block(dark, light, speck, seed):
    rng = random.Random(seed)
    img = Image.new("RGBA", (16, 16))
    px = img.load()
    for y in range(16):
        for x in range(16):
            px[x, y] = rgba(mix(dark, light, rng.random() * 0.55))
    for _ in range(9):
        px[rng.randrange(16), rng.randrange(16)] = rgba(speck)
    for i in range(16):  # bevel
        px[i, 0] = rgba(mix(light, (255, 255, 255), 0.15))
        px[0, i] = rgba(mix(light, (255, 255, 255), 0.15))
        px[i, 15] = rgba(mix(dark, (0, 0, 0), 0.4))
        px[15, i] = rgba(mix(dark, (0, 0, 0), 0.4))
    return img


def eclipse_disc(size, background, ring, core):
    """A dark disc with a glowing corona: the picture of a total solar eclipse."""
    img = Image.new("RGBA", (size, size), background)
    px = img.load()
    c = (size - 1) / 2
    for y in range(size):
        for x in range(size):
            r = math.hypot(x - c, y - c) / (size / 2)
            ang = math.atan2(y - c, x - c)
            rays = 0.06 * (1 + math.sin(ang * 9)) + 0.03 * (1 + math.sin(ang * 23 + 1))
            if r < 0.42:
                px[x, y] = rgba(core)
            elif r < 0.5:
                px[x, y] = rgba(mix(ring, (255, 255, 255), 0.5))
            elif r < 0.58 + rays:
                t = (r - 0.5) / (0.08 + rays)
                px[x, y] = rgba(mix(ring, background[:3], min(t, 1.0)))
    return img


def glasses():
    img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    frame, lens, glint = (24, 22, 30, 255), (52, 40, 70, 255), (140, 120, 190, 255)
    for x0 in (1, 9):
        d.rectangle([x0, 6, x0 + 5, 10], fill=frame)
        d.rectangle([x0 + 1, 7, x0 + 4, 9], fill=lens)
        img.putpixel((x0 + 1, 7), glint)
    d.line([(7, 7), (8, 7)], fill=frame)
    d.line([(0, 6), (1, 6)], fill=frame)
    d.line([(14, 6), (15, 6)], fill=frame)
    return img


def almanac():
    img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle([3, 1, 13, 14], fill=(26, 30, 62, 255))  # cover
    d.rectangle([2, 1, 3, 14], fill=(16, 18, 40, 255))  # spine
    d.line([(13, 2), (13, 14)], fill=(226, 218, 190, 255))  # pages
    d.line([(4, 14), (13, 14)], fill=(226, 218, 190, 255))
    d.ellipse([5, 4, 11, 10], fill=(255, 214, 110, 255))  # corona
    d.ellipse([6, 5, 10, 9], fill=(8, 8, 14, 255))  # moon
    for x, y in ((8, 3), (8, 11), (4, 7), (12, 7)):
        img.putpixel((x, y), (255, 196, 72, 255))
    return img


# --------------------------------------------------------------------------- data

def item_def(model):
    return {"model": {"type": "minecraft:model", "model": model}}


def self_drop(block):
    return {
        "type": "minecraft:block",
        "pools": [{"rolls": 1, "entries": [{"type": "minecraft:item", "name": rid(block)}],
                   "conditions": [{"condition": "minecraft:survives_explosion"}]}],
        "random_sequence": rid("blocks/" + block),
    }


def shaped(pattern, key, result, count=1, category="misc"):
    return {"type": "minecraft:crafting_shaped", "category": category, "pattern": pattern,
            "key": key, "result": {"id": result, "count": count}}


def shapeless(ingredients, result, count=1, category="misc"):
    return {"type": "minecraft:crafting_shapeless", "category": category, "ingredients": ingredients,
            "result": {"id": result, "count": count}}


def unlock(recipe, item):
    return {
        "parent": "minecraft:recipes/root",
        "criteria": {
            "has_the_recipe": {"trigger": "minecraft:recipe_unlocked", "conditions": {"recipe": rid(recipe)}},
            "has_item": {"trigger": "minecraft:inventory_changed", "conditions": {"items": [{"items": item}]}},
        },
        "requirements": [["has_the_recipe", "has_item"]],
        "rewards": {"recipes": [rid(recipe)]},
    }


def advancement(name, icon, frame="task", parent="root", announce=True, hidden=False, criteria=None):
    adv = {
        "display": {
            "icon": {"id": rid(icon)},
            "title": {"translate": f"advancements.{MOD_ID}.{name}.title"},
            "description": {"translate": f"advancements.{MOD_ID}.{name}.description"},
            "frame": frame,
            "show_toast": True,
            "announce_to_chat": announce,
            "hidden": hidden,
        },
        "criteria": criteria or {"witnessed": {"trigger": "minecraft:impossible"}},
    }
    if parent:
        adv["parent"] = rid(parent)
    return adv


LANG = {
    "itemGroup.eclipsia": "Eclipsia",
    "item.eclipsia.umbral_shard": "Umbral Shard",
    "item.eclipsia.sanguine_shard": "Sanguine Shard",
    "item.eclipsia.eclipse_glasses": "Eclipse Glasses",
    "item.eclipsia.eclipse_almanac": "Eclipse Almanac",
    "item.eclipsia.eclipse_glasses.tooltip": "Wear these to look at a solar eclipse safely",
    "item.eclipsia.eclipse_almanac.tooltip": "Use to see when the next eclipses arrive",
    "block.eclipsia.umbral_block": "Block of Umbra",
    "block.eclipsia.sanguine_block": "Block of Sanguine",
    "block.eclipsia.corona_lamp": "Corona Lamp",
    "eclipsia.solar.title": "Solar Eclipse",
    "eclipsia.solar.subtitle": "The moon creeps across the sun",
    "eclipsia.solar.totality": "Totality! Darkness falls at midday...",
    "eclipsia.solar.end": "The sun returns.",
    "eclipsia.lunar.title": "Blood Moon",
    "eclipsia.lunar.subtitle": "The world's shadow swallows the moon",
    "eclipsia.lunar.totality": "The moon bleeds red. Monsters grow bold...",
    "eclipsia.lunar.end": "The blood moon fades.",
    "eclipsia.sun_glare": "Ow! Never look straight at the sun without Eclipse Glasses.",
    "eclipsia.almanac.header": "Eclipse Almanac",
    "eclipsia.almanac.now": "%s: happening now (%s%% covered)",
    "eclipsia.almanac.next": "%s: in %s days, %s hours",
    "eclipsia.solar": "Solar eclipse",
    "eclipsia.lunar": "Lunar eclipse",
    "eclipsia.almanac.not_overworld": "The almanac only charts the Overworld sky.",
    "commands.eclipsia.next": "Next %s in %s ticks. Run /time add %s to jump to it.",
    "advancements.eclipsia.root.title": "Eclipsia",
    "advancements.eclipsia.root.description": "Prepare for the sky to go dark",
    "advancements.eclipsia.totality.title": "Path of Totality",
    "advancements.eclipsia.totality.description": "Stand under the open sky during a total solar eclipse",
    "advancements.eclipsia.blood_moon.title": "Once in a Blood Moon",
    "advancements.eclipsia.blood_moon.description": "Stand under the open sky during a total lunar eclipse",
    "advancements.eclipsia.sun_glare.title": "Don't Look Up",
    "advancements.eclipsia.sun_glare.description": "Stare at a solar eclipse without eye protection",
    "advancements.eclipsia.safe_viewing.title": "Safety First",
    "advancements.eclipsia.safe_viewing.description": "Watch a solar eclipse through Eclipse Glasses",
    "advancements.eclipsia.umbral_hunter.title": "Creatures of the Umbra",
    "advancements.eclipsia.umbral_hunter.description": "Collect a shard from a monster empowered by an eclipse",
}


def main():
    for d in [ASSETS / "textures", ASSETS / "models", ASSETS / "items", ASSETS / "blockstates", DATA, RES / "data" / "minecraft"]:
        shutil.rmtree(d, ignore_errors=True)

    # timelines (added to the overworld's timeline tag so the dimension runs them)
    write_json(DATA / "timeline" / "solar_eclipse.json", solar_timeline())
    write_json(DATA / "timeline" / "lunar_eclipse.json", lunar_timeline())
    write_json(RES / "data" / "minecraft" / "tags" / "timeline" / "in_overworld.json",
               {"replace": False, "values": [rid("solar_eclipse"), rid("lunar_eclipse")]})

    # textures
    tb, ti = ASSETS / "textures" / "block", ASSETS / "textures" / "item"
    tb.mkdir(parents=True)
    ti.mkdir(parents=True)
    shard(rgb("#1e1430"), rgb("#3a2a5c"), rgb("#e8b040"), rgb("#fff2c0")).save(ti / "umbral_shard.png")
    shard(rgb("#5a0a14"), rgb("#9a1a26"), rgb("#2a0408"), rgb("#ff8a8a")).save(ti / "sanguine_shard.png")
    glasses().save(ti / "eclipse_glasses.png")
    almanac().save(ti / "eclipse_almanac.png")
    noise_block(rgb("#120c1e"), rgb("#2e2048"), rgb("#e8b040"), "umbra").save(tb / "umbral_block.png")
    noise_block(rgb("#3a060c"), rgb("#7a1420"), rgb("#ff6a5a"), "sanguine").save(tb / "sanguine_block.png")
    eclipse_disc(16, (28, 20, 12, 255), (255, 200, 80), (6, 6, 10)).save(tb / "corona_lamp.png")
    eclipse_disc(32, (10, 14, 36, 255), (255, 196, 72), (4, 4, 8)).resize((128, 128), Image.NEAREST) \
        .save(ASSETS / "icon.png")

    # models
    for item in ("umbral_shard", "sanguine_shard", "eclipse_glasses", "eclipse_almanac"):
        write_json(ASSETS / "models" / "item" / f"{item}.json",
                   {"parent": "minecraft:item/generated", "textures": {"layer0": rid(f"item/{item}")}})
        write_json(ASSETS / "items" / f"{item}.json", item_def(rid(f"item/{item}")))
    blocks = ("umbral_block", "sanguine_block", "corona_lamp")
    for block in blocks:
        write_json(ASSETS / "models" / "block" / f"{block}.json",
                   {"parent": "minecraft:block/cube_all", "textures": {"all": rid(f"block/{block}")}})
        write_json(ASSETS / "blockstates" / f"{block}.json", {"variants": {"": {"model": rid(f"block/{block}")}}})
        write_json(ASSETS / "items" / f"{block}.json", item_def(rid(f"block/{block}")))
        write_json(DATA / "loot_table" / "blocks" / f"{block}.json", self_drop(block))
    write_json(RES / "data" / "minecraft" / "tags" / "block" / "mineable" / "pickaxe.json",
               {"replace": False, "values": [rid(b) for b in blocks]})
    write_json(ASSETS / "lang" / "en_us.json", LANG)

    # recipes
    recipes = {
        "eclipse_glasses": (shaped(["I I", "TST"], {"I": "minecraft:iron_nugget", "T": "minecraft:tinted_glass",
                                                     "S": "minecraft:string"}, rid("eclipse_glasses"),
                                   category="equipment"), "minecraft:tinted_glass"),
        "eclipse_almanac": (shapeless(["minecraft:book", "minecraft:clock"], rid("eclipse_almanac")),
                            "minecraft:clock"),
        "umbral_block": (shaped(["###", "###", "###"], {"#": rid("umbral_shard")}, rid("umbral_block"),
                                category="building"), rid("umbral_shard")),
        "sanguine_block": (shaped(["###", "###", "###"], {"#": rid("sanguine_shard")}, rid("sanguine_block"),
                                  category="building"), rid("sanguine_shard")),
        "umbral_shard_from_block": (shapeless([rid("umbral_block")], rid("umbral_shard"), 9), rid("umbral_block")),
        "sanguine_shard_from_block": (shapeless([rid("sanguine_block")], rid("sanguine_shard"), 9),
                                      rid("sanguine_block")),
        "corona_lamp": (shaped([" U ", "UGU", " S "], {"U": rid("umbral_shard"), "G": "minecraft:glowstone",
                                                        "S": rid("sanguine_shard")}, rid("corona_lamp"),
                               category="building"), rid("umbral_shard")),
    }
    for name, (recipe, trigger) in recipes.items():
        write_json(DATA / "recipe" / f"{name}.json", recipe)
        write_json(DATA / "advancement" / "recipes" / f"{name}.json", unlock(name, trigger))

    # advancements (the impossible ones are granted from code)
    adv = DATA / "advancement"
    write_json(adv / "root.json", {
        **advancement("root", "eclipse_almanac", parent=None, announce=False, criteria={
            "glasses": {"trigger": "minecraft:inventory_changed",
                        "conditions": {"items": [{"items": rid("eclipse_glasses")}]}},
            "almanac": {"trigger": "minecraft:inventory_changed",
                        "conditions": {"items": [{"items": rid("eclipse_almanac")}]}},
            "umbral": {"trigger": "minecraft:inventory_changed",
                       "conditions": {"items": [{"items": rid("umbral_shard")}]}},
            "sanguine": {"trigger": "minecraft:inventory_changed",
                         "conditions": {"items": [{"items": rid("sanguine_shard")}]}},
        }),
        "requirements": [["glasses", "almanac", "umbral", "sanguine"]],
    })
    adv_root = json.loads((adv / "root.json").read_text())
    adv_root["display"]["background"] = "minecraft:gui/advancements/backgrounds/end"
    write_json(adv / "root.json", adv_root)
    write_json(adv / "totality.json", advancement("totality", "corona_lamp", frame="goal"))
    write_json(adv / "blood_moon.json", advancement("blood_moon", "sanguine_shard", frame="goal"))
    write_json(adv / "sun_glare.json", advancement("sun_glare", "umbral_shard", hidden=True))
    write_json(adv / "safe_viewing.json", advancement("safe_viewing", "eclipse_glasses"))
    write_json(adv / "umbral_hunter.json", advancement("umbral_hunter", "umbral_shard", criteria={
        "umbral": {"trigger": "minecraft:inventory_changed",
                   "conditions": {"items": [{"items": rid("umbral_shard")}]}},
        "sanguine": {"trigger": "minecraft:inventory_changed",
                     "conditions": {"items": [{"items": rid("sanguine_shard")}]}},
    }) | {"requirements": [["umbral", "sanguine"]]})

    JAVA_OUT.parent.mkdir(parents=True, exist_ok=True)
    JAVA_OUT.write_text(java_source(), encoding="utf-8")
    print("Generated Eclipsia data.")


if __name__ == "__main__":
    main()

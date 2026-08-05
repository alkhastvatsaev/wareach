"""Outreach message templates — copy/paste for ops (no auto-send in v0.3)."""

from __future__ import annotations

from app.core.config import get_settings

TEMPLATES: dict[str, str] = {
    "reddit": (
        "Salut — je suis de l’équipe LuxFind FR. On tient un guide discret pour "
        "acheteurs exigeants ({brand}). Si tu cherches des infos fiables (vendeurs, "
        "QC, livraison FR), voici le lien : {luxfind_link} — pas de spam, juste le guide."
    ),
    "telegram": (
        "Bonjour 👋 LuxFind FR ici. Guide discret {brand} pour acheteurs FR "
        "(vendeurs vérifiés, tips douane, QC). Rejoins-nous : {luxfind_link}"
    ),
    "discord": (
        "Hey — LuxFind FR partage un guide premium discret autour de {brand} "
        "pour la communauté FR. Lien : {luxfind_link}"
    ),
    "youtube": (
        "Bonjour, super contenu. LuxFind FR propose un guide discret pour acheteurs "
        "FR intéressés par {brand}. Lien : {luxfind_link}"
    ),
    "email": (
        "Bonjour,\n\n"
        "LuxFind FR est un guide discret pour acheteurs exigeants "
        "(marques comme {brand}, focus livraison France).\n"
        "Découvrir le guide : {luxfind_link}\n\n"
        "Cordialement,\nL’équipe LuxFind FR"
    ),
    "web": (
        "Bonjour — LuxFind FR : guide discret {brand} pour acheteurs FR. "
        "{luxfind_link}"
    ),
}


def luxfind_link() -> str:
    s = get_settings()
    return getattr(s, "facade_telegram_url", None) or "/guide"


def render_template(
    platform: str,
    *,
    brand: str = "luxe",
    luxfind_url: str | None = None,
    platform_label: str | None = None,
    **_: object,
) -> dict[str, str]:
    key = (platform or "web").lower()
    if key not in TEMPLATES:
        key = "web" if key not in {"reddit", "telegram", "discord", "youtube", "email"} else key
    tpl = TEMPLATES.get(key, TEMPLATES["web"])
    link = luxfind_url or luxfind_link()
    body = tpl.format(
        brand=brand or "luxe",
        luxfind_link=link,
        platform=platform_label or platform,
    )
    return {
        "platform": platform,
        "subject": f"LuxFind FR — guide {brand}" if key == "email" else "",
        "body": body,
    }


def all_templates(*, brand: str = "Louis Vuitton") -> dict[str, dict[str, str]]:
    return {k: render_template(k, brand=brand) for k in TEMPLATES}

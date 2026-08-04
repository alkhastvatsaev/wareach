"""OSINT extraction + classification for luxury brand protection."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from urllib.parse import urlparse

from app.data.brands import (
    BRAND_KEYWORDS,
    GEO_CLUSTERS,
    HQ_REPLICA_SIGNALS,
    JEWELRY_FACTORY_SIGNALS,
    REPLICA_GENERAL,
    brand_to_group,
)

WHATSAPP_PATTERNS = [
    re.compile(
        r"(?:whats?app|wa\.me|whatsAPP|Whatapp|WhatApp)\s*[:：]?\s*\+?\s*(86)?[\s\-]?([1][3-9]\d[\s\-]?\d{4}[\s\-]?\d{4})",
        re.I,
    ),
    re.compile(r"(?:whats?app|wa\.me).*?\+?(86)[\s\-]?([1][3-9]\d{9})", re.I),
    re.compile(r"\+86[\s\-]?([1][3-9]\d{9})"),
    re.compile(r"(?:wa\.me/)(86)?([1][3-9]\d{9})", re.I),
    re.compile(r"(?:whats?app[^0-9]{0,20})(\+?86)?[\s\-]?([1][3-9]\d{9})", re.I),
]

WECHAT_PATTERNS = [
    re.compile(r"(?:wechat|weixin|微信|VX|vx|薇信)\s*[:：ID\s]*([A-Za-z][\w\-]{4,31}|\d{6,20})", re.I),
    re.compile(r"(?:WeChat|wechat)\s*(?:ID)?\s*[:：]?\s*([A-Za-z][\w\-]{4,31})", re.I),
]

TELEGRAM_PATTERNS = [
    re.compile(
        r"(?:t\.me/|telegram\.me/|telegram\s*[:：@]|TG\s*[:：@]|飞机号?\s*[:：@]?)\s*@?([A-Za-z][\w]{3,31})",
        re.I,
    ),
]

QQ_PATTERNS = [re.compile(r"(?:QQ|qq)\s*[:：]?\s*(\d{5,12})", re.I)]
EMAIL_PATTERN = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")
PHONE_CN = re.compile(r"(?<!\d)(1[3-9]\d{9})(?!\d)")


@dataclass
class ExtractedContact:
    contact_type: str
    raw_value: str
    normalized_value: str


@dataclass
class ExtractionResult:
    contacts: list[ExtractedContact] = field(default_factory=list)
    brands: list[str] = field(default_factory=list)
    groups: list[str] = field(default_factory=list)
    signals: list[str] = field(default_factory=list)
    hq_signals: list[str] = field(default_factory=list)
    jewelry_signals: list[str] = field(default_factory=list)
    geo_clusters: list[str] = field(default_factory=list)
    lead_type: str = "unknown"
    # hq_replica | jewelry_factory | jewelry_oem | multi_reseller | gray_jeweler | unknown
    quality_tier: str = "unknown"
    # god_tier | high | mid | low | unknown
    risk_score: float = 0.0
    priority_score: float = 0.0


def url_hash(url: str) -> str:
    return hashlib.sha256(url.strip().encode()).hexdigest()


def domain_of(url: str) -> str:
    try:
        return urlparse(url).netloc.lower().removeprefix("www.")
    except Exception:
        return ""


def normalize_phone_cn(digits: str) -> str:
    d = re.sub(r"\D", "", digits)
    if d.startswith("86") and len(d) == 13:
        d = d[2:]
    if len(d) == 11 and d.startswith("1"):
        return f"+86{d}"
    if d.startswith("86"):
        return f"+{d}"
    return f"+{d}" if d else ""


def detect_brands(text: str) -> list[str]:
    low = text.lower()
    found = []
    for brand, kws in BRAND_KEYWORDS.items():
        if any(k.lower() in low for k in kws):
            found.append(brand)
    return found


def _match_list(text: str, items: list[str]) -> list[str]:
    low = text.lower()
    return [s for s in items if s.lower() in low]


NEWS_OR_NOISE_DOMAINS = {
    "thepaper.cn",
    "36kr.com",
    "qq.com",
    "news.qq.com",
    "sina.com.cn",
    "sohu.com",
    "baidu.com",
    "zhihu.com",
    "wikipedia.org",
    "reuters.com",
    "bloomberg.com",
    "nytimes.com",
    "ft.com",
    "cbndata.com",
    "wto168.net",
    "news.wto168.net",
}

# Search-engine redirect hosts — never crawl; they starve the Yupoo queue
CRAWL_JUNK_DOMAINS = {
    "bing.com",
    "cn.bing.com",
    "www.bing.com",
    "microsoft.com",
    "google.com",
    "google.co.uk",
    "google.com.hk",
    "googleusercontent.com",
    "duckduckgo.com",
    "yandex.com",
    "yandex.ru",
    "search.yahoo.com",
    "yahoo.com",
    "wappass.baidu.com",
    "baidu.com",
    "so.com",
    "sogou.com",
}


def is_noise_domain(domain: str) -> bool:
    d = (domain or "").lower()
    return any(d == n or d.endswith("." + n) for n in NEWS_OR_NOISE_DOMAINS)


def is_junk_crawl_domain(domain: str) -> bool:
    d = (domain or "").lower().removeprefix("www.")
    return any(d == n or d.endswith("." + n) for n in CRAWL_JUNK_DOMAINS)


def classify_lead(
    hq: list[str],
    jewelry: list[str],
    general: list[str],
    brands: list[str],
    *,
    domain: str = "",
    has_direct_contact: bool = False,
) -> tuple[str, str]:
    if is_noise_domain(domain) and not has_direct_contact:
        return "noise_media", "low"

    jewelry_brands = {
        "cartier",
        "van_cleef_arpels",
        "tiffany",
        "bulgari",
        "chaumet",
        "piaget",
        "buccellati",
        "fred",
    }
    has_jewelry_brand = any(b in jewelry_brands for b in brands)
    commercial = any(
        x in (domain or "")
        for x in ["yupoo", "weidian", "dhgate", "alibaba", "1688", "made-in-china", "wsxc"]
    )

    if jewelry and (has_jewelry_brand or any(x in jewelry for x in ["水贝", "shuibei", "足金", "18k", "真金真钻", "oem jewelry"])):
        factoryish = any(
            x in jewelry
            for x in ["工厂", "factory", "厂家", "manufacturer", "oem", "odm", "水贝", "shuibei"]
        )
        if factoryish and (has_direct_contact or commercial or "shuibei" in " ".join(jewelry).lower() or "水贝" in " ".join(jewelry)):
            return "jewelry_factory", "high"
        if has_direct_contact:
            return "gray_jeweler", "high"
        if commercial:
            return "gray_jeweler", "mid"
        return "noise_media", "low"

    god = any(
        x in " ".join(hq).lower()
        for x in ["god factory", "godfactory", "过验", "原厂皮", "原厂五金", "super clone", "顶级"]
    )
    if hq and god and (has_direct_contact or commercial):
        return "hq_replica", "god_tier"
    if hq and (has_direct_contact or commercial):
        return "hq_replica", "high"
    if general and brands and has_direct_contact:
        return "multi_reseller", "mid"
    if brands and has_direct_contact:
        return "multi_reseller", "low"
    return "unknown", "unknown"


def compute_scores(
    *,
    brands: list[str],
    hq: list[str],
    jewelry: list[str],
    general: list[str],
    contacts: list[ExtractedContact],
    source_url: str,
    lead_type: str,
    quality_tier: str,
) -> tuple[float, float]:
    """risk_score (0-100 enforcement relevance) + priority_score (ops triage)."""
    risk = 0.0
    risk += min(35.0, 7.0 * len(hq))
    risk += min(30.0, 6.0 * len(jewelry))
    risk += min(15.0, 3.0 * len(general))
    risk += min(25.0, 8.0 * len(brands))
    wa = sum(1 for c in contacts if c.contact_type == "whatsapp")
    risk += min(15.0, 8.0 * wa)
    url_l = (source_url or "").lower()
    if any(x in url_l for x in ["yupoo", "weidian", "dhgate", "made-in-china", "1688", "alibaba"]):
        risk += 12.0
    if quality_tier == "god_tier":
        risk += 20.0
    elif quality_tier == "high":
        risk += 12.0
    if lead_type == "jewelry_factory":
        risk += 18.0
    risk = min(100.0, risk)

    priority = risk
    if lead_type in {"jewelry_factory", "hq_replica"}:
        priority = min(100.0, priority + 10)
    if any(b in brands for b in ["cartier", "van_cleef_arpels", "hermes", "louis_vuitton", "tiffany"]):
        priority = min(100.0, priority + 5)
    return risk, priority


def extract_all(text: str, source_url: str = "") -> ExtractionResult:
    contacts: list[ExtractedContact] = []
    seen: set[tuple[str, str]] = set()

    def add(ctype: str, raw: str, norm: str):
        key = (ctype, norm)
        if not norm or key in seen:
            return
        seen.add(key)
        contacts.append(ExtractedContact(ctype, raw.strip(), norm))

    for pat in WHATSAPP_PATTERNS:
        for m in pat.finditer(text):
            groups = [g for g in m.groups() if g]
            digits = "".join(re.findall(r"\d", "".join(groups)))
            if len(digits) >= 11:
                if not digits.startswith("86") and len(digits) == 11:
                    digits = "86" + digits
                norm = normalize_phone_cn(digits)
                if norm:
                    add("whatsapp", m.group(0), norm)

    for pat in WECHAT_PATTERNS:
        for m in pat.finditer(text):
            val = m.group(1).strip()
            if val.lower() in {"id", "wechat", "微信"}:
                continue
            add("wechat", m.group(0), val.lower())

    for pat in TELEGRAM_PATTERNS:
        for m in pat.finditer(text):
            handle = m.group(1).strip().lstrip("@")
            if handle.lower() in {"telegram", "channel", "group", "http", "https", "www"}:
                continue
            if len(handle) < 4:
                continue
            add("telegram", f"@{handle}", handle.lower())

    for pat in QQ_PATTERNS:
        for m in pat.finditer(text):
            add("qq", m.group(0), m.group(1))

    for m in EMAIL_PATTERN.finditer(text):
        add("email", m.group(0), m.group(0).lower())

    if any(s in text.lower() for s in ["whatsapp", "whats", "wa:", "联系", "厂家", "微信", "珠宝", "工厂"]):
        for m in PHONE_CN.finditer(text):
            add("phone", m.group(1), normalize_phone_cn(m.group(1)))

    if source_url:
        d = domain_of(source_url)
        if d:
            add("website", source_url, d)
        # Yupoo / China shop subdomains often embed WA: whatsap8615… / 18613186639bag.x.yupoo.com
        host = (d or "").split(":")[0]
        sub = host.split(".")[0] if host else ""
        for blob in (sub, source_url):
            for m in re.finditer(r"(?:whats?a?pp?)?(?:86)?(1[3-9]\d{9})", blob, re.I):
                mobile = m.group(1)
                norm = normalize_phone_cn("86" + mobile)
                if norm:
                    add("whatsapp", m.group(0), norm)
        # On Yupoo/weidian/wsxc, bare CN mobiles in title/snippet are almost always WA storefronts
        if any(x in (d or "") for x in ["yupoo", "weidian", "wsxc"]):
            for m in PHONE_CN.finditer(text):
                add("whatsapp", m.group(1), normalize_phone_cn("86" + m.group(1)))

    brands = detect_brands(text)
    groups = sorted({g for b in brands if (g := brand_to_group(b))})
    hq = _match_list(text, HQ_REPLICA_SIGNALS)
    jewelry = _match_list(text, JEWELRY_FACTORY_SIGNALS)
    general = _match_list(text, REPLICA_GENERAL)
    geos = [name for name, kws in GEO_CLUSTERS.items() if any(k.lower() in text.lower() for k in kws)]

    domain = domain_of(source_url) if source_url else ""
    has_direct = any(c.contact_type in {"whatsapp", "wechat", "telegram", "qq", "phone"} for c in contacts)
    lead_type, quality_tier = classify_lead(
        hq,
        jewelry,
        general,
        brands,
        domain=domain,
        has_direct_contact=has_direct,
    )
    risk, priority = compute_scores(
        brands=brands,
        hq=hq,
        jewelry=jewelry,
        general=general,
        contacts=contacts,
        source_url=source_url,
        lead_type=lead_type,
        quality_tier=quality_tier,
    )
    if lead_type == "noise_media":
        risk = min(risk, 15.0)
        priority = min(priority, 10.0)

    return ExtractionResult(
        contacts=contacts,
        brands=brands,
        groups=groups,
        signals=sorted(set(hq + jewelry + general)),
        hq_signals=hq,
        jewelry_signals=jewelry,
        geo_clusters=geos,
        lead_type=lead_type,
        quality_tier=quality_tier,
        risk_score=risk,
        priority_score=priority,
    )


def supplier_key_from_contacts(contacts: list[ExtractedContact], domain: str = "") -> str | None:
    for ctype in ("whatsapp", "wechat", "telegram", "qq", "phone"):
        for c in contacts:
            if c.contact_type == ctype:
                return f"{ctype}:{c.normalized_value}"
    if domain:
        return f"website:{domain}"
    return None

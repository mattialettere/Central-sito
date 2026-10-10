"""Contatore delle visite di getcentral.net.

POST /site/hit      dal sito, una chiamata per pagina vista. Nessun login.
GET  /site/stats    per il pannello, solo moderatori.

Il sito manda la visita con navigator.sendBeacon e corpo text/plain: e' una
richiesta "semplice" per il browser, quindi niente preflight CORS e niente
da configurare. La risposta e' sempre 204 e il sito non la legge.

Privacy (models/site_visit.py): niente cookie, niente IP salvati, impronta
del visitatore che cambia ogni giorno. Con questo trattamento il contatore
non richiede il banner dei cookie; va comunque citato nell'informativa.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
import random
import re
from datetime import date, datetime, timedelta, timezone
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from auth import get_current_user
from database import get_db
from models.site_visit import SiteVisit
from models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/site", tags=["site"])

ROMA = ZoneInfo("Europe/Rome")
SITE_HOSTS = {"getcentral.net", "www.getcentral.net"}
CONSERVAZIONE_GIORNI = 400

BOT = re.compile(
    r"bot|crawl|spider|slurp|preview|facebookexternalhit|embedly|headless|lighthouse|"
    r"pingdom|uptime|monitor|curl|wget|python-requests|httpx|go-http|java/|okhttp",
    re.I,
)

# Dominio del referrer -> nome leggibile. Il primo che corrisponde vince.
SORGENTI = [
    (re.compile(r"(^|\.)google\."), "Google"),
    (re.compile(r"(^|\.)bing\.com$"), "Bing"),
    (re.compile(r"(^|\.)duckduckgo\.com$"), "DuckDuckGo"),
    (re.compile(r"(^|\.)ecosia\.org$"), "Ecosia"),
    (re.compile(r"(^|\.)yahoo\."), "Yahoo"),
    (re.compile(r"(^|\.)(facebook\.com|fb\.com|fb\.me)$"), "Facebook"),
    (re.compile(r"(^|\.)instagram\.com$"), "Instagram"),
    (re.compile(r"(^|\.)tiktok\.com$"), "TikTok"),
    (re.compile(r"(^|\.)(t\.co|x\.com|twitter\.com)$"), "X"),
    (re.compile(r"(^|\.)(reddit\.com|redd\.it)$"), "Reddit"),
    (re.compile(r"(^|\.)(youtube\.com|youtu\.be)$"), "YouTube"),
    (re.compile(r"(^|\.)(linkedin\.com|lnkd\.in)$"), "LinkedIn"),
    (re.compile(r"(^|\.)(whatsapp\.com|wa\.me)$"), "WhatsApp"),
    (re.compile(r"(^|\.)(t\.me|telegram\.org)$"), "Telegram"),
    (re.compile(r"(^|\.)play\.google\.com$"), "Google Play"),
]
UTM_NOMI = {
    "ig": "Instagram", "instagram": "Instagram", "fb": "Facebook", "facebook": "Facebook",
    "tiktok": "TikTok", "tt": "TikTok", "reddit": "Reddit", "youtube": "YouTube", "yt": "YouTube",
    "linkedin": "LinkedIn", "whatsapp": "WhatsApp", "telegram": "Telegram", "email": "Email",
    "newsletter": "Email", "google": "Google", "x": "X", "twitter": "X",
}


def _oggi() -> date:
    return datetime.now(ROMA).date()


def _impronta(ip: str, ua: str, giorno: date) -> str:
    """Impronta giornaliera: non reversibile e diversa ogni giorno."""
    segreto = (os.getenv("SECRET_KEY") or "central").encode()
    chiave_del_giorno = hmac.new(segreto, f"visite:{giorno.isoformat()}".encode(), hashlib.sha256).digest()
    return hmac.new(chiave_del_giorno, f"{ip}|{ua}".encode(), hashlib.sha256).hexdigest()[:16]


def _dispositivo(ua: str) -> str:
    u = ua.lower()
    if "ipad" in u or "tablet" in u or ("android" in u and "mobile" not in u):
        return "tablet"
    if "mobi" in u or "iphone" in u or "android" in u:
        return "mobile"
    return "desktop"


def _host(url: str | None) -> str | None:
    if not url:
        return None
    try:
        h = (urlparse(url).hostname or "").lower()
    except ValueError:
        return None
    return h[4:] if h.startswith("www.") else (h or None)


def classifica(referrer: str | None, utm_source: str | None) -> tuple[str, str | None]:
    """(provenienza leggibile, dominio del referrer)."""
    host = _host(referrer)
    if utm_source:
        u = utm_source.strip().lower()[:40]
        return UTM_NOMI.get(u, utm_source.strip()[:40]), host
    if not host:
        return "Diretto", None
    if host in SITE_HOSTS or host == "getcentral.net":
        return "Interno", host
    for regex, nome in SORGENTI:
        if regex.search(host):
            return nome, host
    return host[:80], host


def _pulisci_path(path: str | None) -> str:
    p = (path or "/").split("?")[0].split("#")[0].strip() or "/"
    if not p.startswith("/"):
        p = "/" + p
    if p.endswith("/index.html"):
        p = p[: -len("index.html")]
    return p[:200]


@router.post("/hit", status_code=204)
async def hit(request: Request, db: AsyncSession = Depends(get_db)) -> Response:
    vuota = Response(status_code=204)
    ua = request.headers.get("user-agent", "")[:400]
    if not ua or BOT.search(ua):
        return vuota
    # Solo dal nostro sito: un'altra pagina che ci chiamasse gonfierebbe i numeri.
    origine = _host(request.headers.get("origin") or request.headers.get("referer"))
    if origine not in SITE_HOSTS and origine != "getcentral.net" and origine not in ("localhost", "127.0.0.1"):
        return vuota
    try:
        corpo = json.loads((await request.body())[:4000] or b"{}")
        if not isinstance(corpo, dict):
            return vuota
    except (ValueError, UnicodeDecodeError):
        return vuota

    oggi = _oggi()
    ip = request.client.host if request.client else ""
    visitatore = _impronta(ip, ua, oggi)
    fonte, host = classifica(corpo.get("referrer"), corpo.get("utm_source"))
    campagna = (str(corpo.get("utm_campaign") or "").strip()[:80]) or None

    gia_visto = await db.scalar(
        select(SiteVisit.id).where(SiteVisit.day == oggi, SiteVisit.visitor == visitatore).limit(1)
    )
    db.add(SiteVisit(
        day=oggi,
        path=_pulisci_path(str(corpo.get("path") or "/")),
        source=fonte,
        referrer_host=host[:120] if host else None,
        campaign=campagna,
        device=_dispositivo(ua),
        visitor=visitatore,
        entry=gia_visto is None,
    ))
    # Pulizia occasionale delle righe oltre il periodo di conservazione.
    if random.random() < 0.01:
        await db.execute(delete(SiteVisit).where(SiteVisit.day < oggi - timedelta(days=CONSERVAZIONE_GIORNI)))
    await db.commit()
    return vuota


@router.get("/stats")
async def stats(
    days: int = 30,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    from routers.reports import _require_moderator

    _require_moderator(user)
    days = max(1, min(days, 366))
    oggi = _oggi()
    dal = oggi - timedelta(days=days - 1)
    nel_periodo = SiteVisit.day >= dal

    pagine_viste = await db.scalar(select(func.count()).where(nel_periodo)) or 0
    # Visitatori unici: somma dei visitatori diversi di ogni giorno (l'impronta
    # cambia a mezzanotte, quindi chi torna domani conta di nuovo).
    visitatori = await db.scalar(
        select(func.count(func.distinct(func.concat(SiteVisit.day, SiteVisit.visitor)))).where(nel_periodo)
    ) or 0

    per_giorno = {
        d: (v, p)
        for d, v, p in (
            await db.execute(
                select(SiteVisit.day, func.count(func.distinct(SiteVisit.visitor)), func.count())
                .where(nel_periodo).group_by(SiteVisit.day)
            )
        ).all()
    }
    serie = []
    for i in range(days):
        d = dal + timedelta(days=i)
        v, p = per_giorno.get(d, (0, 0))
        serie.append({"day": d.isoformat(), "visitors": v, "pageviews": p})

    async def classifica_per(colonna, solo_ingressi: bool = False, limite: int = 12):
        cond = [nel_periodo, colonna.isnot(None)]
        if solo_ingressi:
            cond.append(SiteVisit.entry.is_(True))
        righe = (
            await db.execute(
                select(colonna, func.count(), func.count(func.distinct(func.concat(SiteVisit.day, SiteVisit.visitor))))
                .where(*cond).group_by(colonna).order_by(func.count().desc()).limit(limite)
            )
        ).all()
        return [{"name": n or "—", "pageviews": p, "visitors": v} for n, p, v in righe]

    oggi_v, oggi_p = per_giorno.get(oggi, (0, 0))
    return {
        "days": days,
        "from": dal.isoformat(),
        "to": oggi.isoformat(),
        "visitors": visitatori,
        "pageviews": pagine_viste,
        "today": {"visitors": oggi_v, "pageviews": oggi_p},
        "series": serie,
        "pages": await classifica_per(SiteVisit.path),
        # Provenienza: solo la pagina d'ingresso, altrimenti ogni click
        # interno al sito comparirebbe come "Interno".
        "sources": await classifica_per(SiteVisit.source, solo_ingressi=True),
        "campaigns": await classifica_per(SiteVisit.campaign, solo_ingressi=True, limite=8),
        "devices": await classifica_per(SiteVisit.device, limite=3),
    }

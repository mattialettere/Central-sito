"""Visite al sito getcentral.net, contate dal nostro server.

Senza cookie e senza servizi esterni: chi visita il sito non viene
riconosciuto da un giorno all'altro e nessun dato esce dall'Europa.

Cosa NON si salva: indirizzo IP, browser completo, posizione. Il
"visitatore" e' un'impronta di 16 caratteri calcolata da IP + browser +
una chiave che cambia ogni giorno: serve solo a contare le persone
diverse di quel giorno, e il giorno dopo la stessa persona ha
un'impronta nuova che non si puo' collegare alla precedente.
"""

from datetime import date, datetime, timezone

from sqlalchemy import Boolean, Date, DateTime, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class SiteVisit(Base):
    __tablename__ = "site_visits"
    __table_args__ = (
        Index("ix_site_visits_day", "day"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    # Giorno in ora italiana: e' quello in cui si ragiona guardando i numeri.
    day: Mapped[date] = mapped_column(Date, nullable=False)

    # Pagina vista, senza parametri ("/", "/aziende.html").
    path: Mapped[str] = mapped_column(String(200), nullable=False)
    # Provenienza leggibile: "Google", "Instagram", "Diretto", "Interno"
    # (da un'altra pagina del sito) o il dominio di chi ha linkato.
    source: Mapped[str] = mapped_column(String(80), nullable=False)
    # Dominio esatto del referrer, quando c'e'.
    referrer_host: Mapped[str | None] = mapped_column(String(120), nullable=True)
    # utm_campaign, se il link ne aveva una ("tiktok-ottobre").
    campaign: Mapped[str | None] = mapped_column(String(80), nullable=True)
    # "mobile" | "desktop" | "tablet"
    device: Mapped[str] = mapped_column(String(10), nullable=False)
    # Impronta giornaliera del visitatore (vedi sopra).
    visitor: Mapped[str] = mapped_column(String(16), nullable=False)
    # Prima pagina della visita di quel visitatore in quel giorno.
    entry: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")

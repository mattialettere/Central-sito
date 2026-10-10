"""Contatore delle visite di getcentral.net."""

import json

import pytest

from routers.site_analytics import classifica
from tests.aiuti import intestazione, nuovo_utente, sql

ORIGINE = {"Origin": "https://getcentral.net", "Content-Type": "text/plain"}
TELEFONO = "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 Chrome/128 Mobile Safari/537.36"
PC = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/128 Safari/537.36"


@pytest.fixture
async def mod(monkeypatch):
    uid = await nuovo_utente("Mattia")
    monkeypatch.setenv("MODERATOR_USER_IDS", uid)
    return uid


async def _hit(client, ua, **corpo):
    return await client.post("/site/hit", content=json.dumps(corpo), headers={**ORIGINE, "User-Agent": ua})


def test_provenienze():
    assert classifica("https://www.google.com/", None) == ("Google", "google.com")
    assert classifica("https://l.instagram.com/?u=x", None)[0] == "Instagram"
    assert classifica("https://getcentral.net/aziende.html", None)[0] == "Interno"
    assert classifica("", None) == ("Diretto", None)
    assert classifica(None, "tiktok")[0] == "TikTok"
    assert classifica("https://blog.esempio.it/post", None) == ("blog.esempio.it", "blog.esempio.it")


async def test_visitatori_pagine_e_provenienza(client, mod):
    # Stesso telefono: 1 visitatore, 3 pagine; la provenienza e' quella d'ingresso.
    assert (await _hit(client, TELEFONO, path="/", referrer="https://www.google.com/")).status_code == 204
    await _hit(client, TELEFONO, path="/aziende.html", referrer="https://getcentral.net/")
    await _hit(client, TELEFONO, path="/white-label.html?x=1", referrer="https://getcentral.net/aziende.html")
    # Un PC arriva da Instagram con campagna.
    await _hit(client, PC, path="/index.html", referrer="", utm_source="ig", utm_campaign="reel-ottobre")

    r = await client.get("/site/stats?days=7", headers=intestazione(mod))
    assert r.status_code == 200, r.text
    s = r.json()
    assert s["visitors"] == 2 and s["pageviews"] == 4
    assert s["today"] == {"visitors": 2, "pageviews": 4}
    assert {p["name"]: p["pageviews"] for p in s["pages"]} == {"/": 2, "/aziende.html": 1, "/white-label.html": 1}
    assert {x["name"]: x["visitors"] for x in s["sources"]} == {"Google": 1, "Instagram": 1}
    assert s["campaigns"] == [{"name": "reel-ottobre", "pageviews": 1, "visitors": 1}]
    assert {d["name"] for d in s["devices"]} == {"mobile", "desktop"}
    assert len(s["series"]) == 7


async def test_scarta_bot_e_altri_siti(client):
    await client.post("/site/hit", content='{"path":"/"}',
                      headers={**ORIGINE, "User-Agent": "Googlebot/2.1 (+http://www.google.com/bot.html)"})
    await client.post("/site/hit", content='{"path":"/"}',
                      headers={"Origin": "https://altro-sito.it", "User-Agent": PC})
    await client.post("/site/hit", content="non json", headers={**ORIGINE, "User-Agent": PC})
    assert (await sql("select count(*) from site_visits")).scalar_one() == 0


async def test_nessun_ip_salvato(client):
    await _hit(client, PC, path="/")
    riga = (await sql("select * from site_visits")).mappings().one()
    assert "127.0.0.1" not in json.dumps({k: str(v) for k, v in riga.items()})
    assert len(riga["visitor"]) == 16


async def test_statistiche_solo_moderatori(client, mod):
    altro = await nuovo_utente("Curioso")
    assert (await client.get("/site/stats", headers=intestazione(altro))).status_code == 404

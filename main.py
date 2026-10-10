"""
Main FastAPI application entry point — Central 2.
"""
import asyncio
import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from database import engine, Base
import i18n
from routers import i18n_packs
from routers import auth, users, friends, chats, groups, boards, devices, gallery, trips, blocks, broadcast, share, scheduled, media, websocket, communities, calls, turn, call_reports, guardian, geofence, check_in, legal, guardian_dashboard, reports, sanctions, announcements, poi, safety_log, map_events, billing, city, city_live
# Import necessario solo per far scoprire il modello a Base.metadata.create_all
# (la tabella consent_records viene creata automaticamente al primo avvio,
# nessuna ALTER manuale serve perché è una tabella nuova, non una esistente).
from models.consent import ConsentRecord  # noqa: F401
# Stessa ragione: la tabella dei provvedimenti disciplinari deve essere
# nota a Base.metadata, e il modello non e importato da nessun altro punto
# raggiunto all'avvio.
from models.sanction import UserSanction  # noqa: F401
# Registro degli upload: serve a cancellare dallo storage anche i file il cui
# URL vive dentro un payload cifrato (immagini delle lavagne). Tabella nuova,
# quindi create_all basta.
from models.media_object import MediaObject  # noqa: F401
# Segnalazioni di contenuti e utenti: tabella nuova, create_all basta.
from models.content_report import ContentReport  # noqa: F401
# Central City: profili e registro monete, tabelle nuove (create_all basta).
from models.city import CityGift, CityNote, CityNoteReport, CityProfile, CityVisit, CityWatering, CoinLedger  # noqa: F401
# Il logging va configurato a mano.
#
# Uvicorn imposta i propri logger ("uvicorn", "uvicorn.access") e non tocca
# quello radice: senza basicConfig, i messaggi di questo modulo finiscono
# sul gestore di ripiego di Python, che scrive solo da WARNING in su. E'
# il motivo per cui le righe INFO dell'avvio non comparivano nei log di
# Railway mentre i print e gli avvisi si vedevano: non e' che il codice non
# girava, e' che nessuno ascoltava.
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s [%(name)s] %(message)s",
)

logger = logging.getLogger(__name__)
async def _run_lightweight_migrations(conn) -> None:
    """
    Base.metadata.create_all crea solo le tabelle mancanti, non aggiunge colonne
    a tabelle già esistenti in produzione. Per le nuove colonne E2E (public_key,
    iv) usiamo ALTER TABLE ... IF NOT EXISTS, idempotente e sicuro da rieseguire
    ad ogni deploy senza bisogno di una vera pipeline Alembic.
    """
    await conn.execute(text(
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS public_key TEXT"
    ))
    await conn.execute(text(
        "ALTER TABLE messages ADD COLUMN IF NOT EXISTS iv VARCHAR(64)"
    ))
    await conn.execute(text(
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS key_backup_blob TEXT"
    ))
    await conn.execute(text(
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS key_backup_iv VARCHAR(64)"
    ))
    await conn.execute(text(
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS key_backup_salt VARCHAR(64)"
    ))
    # Perimetro di sicurezza: la zona è passata da "attiva/non attiva" a un
    # ciclo di proposta concordata (proposed -> active/rejected). Queste
    # istruzioni servono solo se una versione precedente della tabella era
    # già stata creata in produzione; su un database nuovo create_all fa tutto.
    # Galleria: descrizione della foto e risposte ai commenti. Entrambe
    # colonne nuove su tabelle esistenti, che create_all non tocca.
    # Allarga messages.type: "media_share" non entrava in VARCHAR(10) e
    # l'inserimento falliva. ALTER TYPE su un allargamento non riscrive la
    # tabella, quindi e istantaneo anche con molte righe.
    await conn.execute(text(
        "ALTER TABLE messages ALTER COLUMN type TYPE VARCHAR(20)"
    ))

    # Preferenze personali sulla conversazione: fissata in alto e svuotata.
    # Colonne nuove su una tabella esistente, che create_all non tocca.
    await conn.execute(text(
        "ALTER TABLE chat_members ADD COLUMN IF NOT EXISTS pinned_at TIMESTAMPTZ"
    ))
    await conn.execute(text(
        "ALTER TABLE chat_members ADD COLUMN IF NOT EXISTS cleared_at TIMESTAMPTZ"
    ))

    await conn.execute(text(
        "ALTER TABLE user_media ADD COLUMN IF NOT EXISTS caption TEXT"
    ))
    await conn.execute(text(
        "ALTER TABLE media_comments ADD COLUMN IF NOT EXISTS parent_id VARCHAR "
        "REFERENCES media_comments(id) ON DELETE CASCADE"
    ))

    await conn.execute(text(
        "ALTER TABLE geofence_zones ADD COLUMN IF NOT EXISTS status VARCHAR(20) NOT NULL DEFAULT 'active'"
    ))
    await conn.execute(text(
        "ALTER TABLE geofence_zones ADD COLUMN IF NOT EXISTS proposed_by VARCHAR(10) NOT NULL DEFAULT 'guardian'"
    ))
    await conn.execute(text(
        "ALTER TABLE geofence_zones ADD COLUMN IF NOT EXISTS responded_at TIMESTAMPTZ"
    ))
    await conn.execute(text(
        "ALTER TABLE geofence_zones DROP COLUMN IF EXISTS active"
    ))
    # Chat di gruppo. Le tabelle esistono gia in produzione, quindi
    # create_all non aggiungerebbe le nuove colonne: servono le ALTER.
    # La tabella group_keys invece e nuova e viene creata da create_all.
    await conn.execute(text(
        "ALTER TABLE chats ADD COLUMN IF NOT EXISTS creator_id VARCHAR"
    ))
    await conn.execute(text(
        "ALTER TABLE chat_members ADD COLUMN IF NOT EXISTS role VARCHAR(10) NOT NULL DEFAULT 'member'"
    ))
    await conn.execute(text(
        "ALTER TABLE chat_members ADD COLUMN IF NOT EXISTS joined_at TIMESTAMPTZ"
    ))
    # Le chat 1:1 gia esistenti non hanno joined_at: lo allineiamo alla data
    # di creazione della chat, cosi l'ordinamento dei membri e la promozione
    # automatica ad admin hanno sempre un riferimento temporale valido.
    await conn.execute(text(
        "UPDATE chat_members SET joined_at = chats.created_at "
        "FROM chats WHERE chats.id = chat_members.chat_id "
        "AND chat_members.joined_at IS NULL"
    ))
    await conn.execute(text(
        "ALTER TABLE messages ADD COLUMN IF NOT EXISTS key_version INTEGER"
    ))
    # Check-in settimanale: la tabella esiste gia in produzione, quindi le
    # colonne nuove vanno aggiunte a mano. Il default 'daily' fa si che tutte
    # le pianificazioni gia concordate continuino a valere identiche.
    await conn.execute(text(
        "ALTER TABLE check_in_schedules ADD COLUMN IF NOT EXISTS mode VARCHAR(10) "
        "NOT NULL DEFAULT 'daily'"
    ))
    await conn.execute(text(
        "ALTER TABLE check_in_schedules ADD COLUMN IF NOT EXISTS weekly_times TEXT"
    ))
    # Tentativi falliti sul codice di reset password: senza contatore, sei
    # cifre si esauriscono a forza bruta prima che il codice scada.
    await conn.execute(text(
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS reset_code_attempts "
        "INTEGER NOT NULL DEFAULT 0"
    ))
    # Stesso contatore per il codice di verifica email (vedi models/user.py).
    await conn.execute(text(
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS verification_code_attempts "
        "INTEGER NOT NULL DEFAULT 0"
    ))
    # Community: post dei membri con approvazione (vedi la migrazione
    # a7d3e9c1f264). La tabella delle segnalazioni la crea create_all.
    await conn.execute(text(
        "ALTER TABLE communities ADD COLUMN IF NOT EXISTS member_posts_enabled "
        "BOOLEAN NOT NULL DEFAULT false"
    ))
    await conn.execute(text(
        "ALTER TABLE community_posts ADD COLUMN IF NOT EXISTS status "
        "VARCHAR(20) NOT NULL DEFAULT 'published'"
    ))
    await conn.execute(text(
        "ALTER TABLE community_posts ADD COLUMN IF NOT EXISTS reviewed_by "
        "VARCHAR REFERENCES users(id) ON DELETE SET NULL"
    ))
    await conn.execute(text(
        "ALTER TABLE community_posts ADD COLUMN IF NOT EXISTS reviewed_at TIMESTAMPTZ"
    ))
    # Risposte ai commenti delle community.
    await conn.execute(text(
        "ALTER TABLE community_post_comments ADD COLUMN IF NOT EXISTS parent_id "
        "VARCHAR REFERENCES community_post_comments(id) ON DELETE CASCADE"
    ))
    # Viaggia sicuro: passeggiata e batteria (migrazione c8f2a6d4e173).
    await conn.execute(text(
        "ALTER TABLE trips ADD COLUMN IF NOT EXISTS mode VARCHAR(12) NOT NULL DEFAULT 'destination'"
    ))
    await conn.execute(text("ALTER TABLE trips ADD COLUMN IF NOT EXISTS battery_level INTEGER"))
    await conn.execute(text("ALTER TABLE trips ADD COLUMN IF NOT EXISTS battery_alert_level INTEGER"))
    # Chat: messaggi a tempo e sondaggi (migrazione d1a7c4e9f352). Le
    # tabelle message_reactions e poll_votes le crea create_all.
    await conn.execute(text("ALTER TABLE messages ADD COLUMN IF NOT EXISTS expires_at TIMESTAMPTZ"))
    await conn.execute(text(
        "CREATE INDEX IF NOT EXISTS ix_messages_expires_at ON messages (expires_at)"
    ))
    await conn.execute(text("ALTER TABLE messages ADD COLUMN IF NOT EXISTS poll_options SMALLINT"))
    await conn.execute(text("ALTER TABLE messages ADD COLUMN IF NOT EXISTS poll_multiple BOOLEAN"))
    await conn.execute(text("ALTER TABLE messages ADD COLUMN IF NOT EXISTS poll_closed_at TIMESTAMPTZ"))
    # Community: post fissati (migrazione e2b8d5f1a463). Eventi e risposte
    # sono tabelle nuove: le crea create_all.
    await conn.execute(text("ALTER TABLE community_posts ADD COLUMN IF NOT EXISTS pinned_at TIMESTAMPTZ"))
    # Segnalazioni: copia allegata dal client e sua provenienza.
    await conn.execute(text(
        "ALTER TABLE content_reports ADD COLUMN IF NOT EXISTS snapshot_source "
        "VARCHAR(10) NOT NULL DEFAULT 'server'"
    ))
    await conn.execute(text(
        "ALTER TABLE content_reports ADD COLUMN IF NOT EXISTS evidence_url VARCHAR(500)"
    ))
    # Avviso di revoca differito al guardiano.
    await conn.execute(text(
        "ALTER TABLE guard_links ADD COLUMN IF NOT EXISTS guardian_notify_at TIMESTAMPTZ"
    ))
    await conn.execute(text(
        "ALTER TABLE guard_links ADD COLUMN IF NOT EXISTS guardian_notified_at TIMESTAMPTZ"
    ))
    # Non letti calcolati dal server: fin dove ogni membro ha letto.
    # Resta NULL sulle righe esistenti, e va bene cosi: NULL significa "mai
    # aperta" e il conteggio ripiega su joined_at, che c'e' gia per tutti.
    await conn.execute(text(
        "ALTER TABLE chat_members ADD COLUMN IF NOT EXISTS last_read_at TIMESTAMPTZ"
    ))
    # Il conteggio dei non letti e il recupero con 'after' filtrano sempre per
    # chat e ordinano per data. Senza questo indice ogni apertura dell'elenco
    # chat fa una scansione per conversazione, e con lo storico che cresce
    # diventa il collo di bottiglia della schermata piu usata dell'app.
    # CONCURRENTLY non e usabile dentro una transazione, quindi si accetta il
    # lock: la tabella e piccola adesso, ed e il momento giusto per farlo.
    # Lingua dell'app per push ed email (NULL = italiano, come prima).
    await conn.execute(text(
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS language VARCHAR(8)"
    ))
    await conn.execute(text(
        "CREATE INDEX IF NOT EXISTS ix_messages_chat_timestamp "
        "ON messages (chat_id, timestamp)"
    ))
@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await _run_lightweight_migrations(conn)
    from services.fcm import _get_firebase_app
    _get_firebase_app()

    # Push nella lingua di chi le riceve: vale per api e worker, perche
    # entrambi spediscono notifiche (il worker quelle degli allarmi).
    i18n.install_push_translation()
    lingue_task = asyncio.create_task(i18n.token_language_loop())

    # CICLI IN BACKGROUND: UNA SOLA ISTANZA LI DEVE ESEGUIRE
    #
    # Sono orologi, non gestori di richieste. Girano a intervalli, guardano
    # il database e agiscono: avvisano i controllori di un viaggio scaduto,
    # spediscono i messaggi programmati, cancellano i dati scaduti.
    #
    # Duplicarli non raddoppia la velocita', raddoppia gli effetti. Con due
    # repliche il controllore di un viaggio riceverebbe due allarmi per lo
    # stesso ritardo, un messaggio programmato partirebbe due volte e due
    # processi cancellerebbero le stesse righe. Su funzioni di sicurezza un
    # allarme doppio non e' un fastidio estetico: e' quello che insegna alle
    # persone a ignorare gli allarmi.
    #
    # Da qui la divisione in due servizi Railway che condividono questo
    # codice: "api", con quante repliche servono e questa variabile a
    # "false", e "worker", con una replica sola e la variabile a "true".
    #
    # Il valore predefinito e' "true" di proposito: finche' il servizio e'
    # uno solo — cioe' oggi — non cambia niente e il deploy di questa
    # modifica non spegne nessun orologio per distrazione. E' il servizio
    # "api" a doverla mettere a "false" esplicitamente, nel momento in cui
    # il worker esiste davvero.
    esegui_cicli = os.getenv("RUN_BACKGROUND_JOBS", "true").strip().lower() != "false"
    task_di_fondo: list[asyncio.Task] = []

    if not esegui_cicli:
        logger.info("Cicli in background disattivati su questa istanza (RUN_BACKGROUND_JOBS=false)")
        yield
        lingue_task.cancel()
        return
    # Purga periodica degli eventi di perimetro oltre il periodo di
    # conservazione (minimizzazione GDPR).
    from services.geofence_retention import geofence_retention_loop
    retention_task = asyncio.create_task(geofence_retention_loop())
    # Sorveglianza dei check-in giornalieri: promemoria alla persona prima
    # della scadenza, avviso ai guardiani se la conferma non arriva.
    from services.check_in_monitor import check_in_monitor_loop
    check_in_task = asyncio.create_task(check_in_monitor_loop())
    # Viaggia sicuro: avviso al viaggiatore in ritardo, poi allarme ai
    # controllori. Deve girare qui e non sul telefono, altrimenti un
    # telefono spento non farebbe scattare nulla.
    from services.trip_monitor import trip_monitor_loop
    trip_task = asyncio.create_task(trip_monitor_loop())
    # Messaggi programmati: la consegna deve avvenire anche col telefono
    # spento, quindi l'orologio che conta e questo.
    from services.scheduled_monitor import scheduled_monitor_loop
    scheduled_task = asyncio.create_task(scheduled_monitor_loop())
    # Viaggia sicuro, conservazione: l'ultima posizione di un viaggio
    # concluso resta consultabile 24 ore e poi viene cancellata qui. Prima
    # spariva nell'istante della conferma d'arrivo, che e' proprio il momento
    # in cui puo' ancora servire.
    from services.trip_retention import trip_retention_loop
    trip_retention_task = asyncio.create_task(trip_retention_loop())
    # Revoca di un collegamento di tutela: l'avviso al guardiano parte a
    # distanza di ore quando a revocare e stata la persona monitorata. Deve
    # girare qui perche il telefono di quella persona potrebbe essere stato
    # appena spento — e in alcuni scenari e proprio quello che e successo.
    from services.guardian_revocation import guardian_revocation_loop
    guardian_revocation_task = asyncio.create_task(guardian_revocation_loop())
    # Registro eventi di sicurezza: ogni utente sceglie per quanto tenerlo,
    # fino a un mese. Una passata all'ora basta — non sono dati di posizione
    # e non c'e fretta al minuto; conta che la finestra scelta venga
    # rispettata entro un margine ragionevole.
    from services.safety_log import safety_log_retention_loop
    safety_log_task = asyncio.create_task(safety_log_retention_loop())
    # Ritrovi sulla mappa condivisa: "manca un'ora" e "e' iniziato". Deve
    # girare qui perche' riguardano tutto il gruppo, non solo chi ha creato
    # l'evento — un promemoria sul suo telefono avviserebbe lui soltanto.
    from services.map_event_monitor import map_event_monitor_loop
    map_event_task = asyncio.create_task(map_event_monitor_loop())
    # Messaggi a tempo: la cancellazione deve avvenire anche se nessuno ha
    # l'app aperta, quindi l'orologio che conta e questo.
    from services.message_expiry import message_expiry_loop
    message_expiry_task = asyncio.create_task(message_expiry_loop())
    # Eventi delle community: promemoria un'ora prima a chi partecipa.
    from services.community_event_monitor import community_event_monitor_loop
    community_event_task = asyncio.create_task(community_event_monitor_loop())
    # Aziende clienti: email ai referenti 7 giorni prima della scadenza.
    from services.organizations import organization_monitor_loop
    organization_task = asyncio.create_task(organization_monitor_loop())
    task_di_fondo.extend([
        retention_task, check_in_task, trip_task, scheduled_task,
        trip_retention_task, guardian_revocation_task, safety_log_task,
        map_event_task, message_expiry_task, community_event_task,
        organization_task,
    ])
    logger.info("Cicli in background avviati: %d", len(task_di_fondo))

    yield
    lingue_task.cancel()
    retention_task.cancel()
    check_in_task.cancel()
    trip_task.cancel()
    scheduled_task.cancel()
    trip_retention_task.cancel()
    guardian_revocation_task.cancel()
    safety_log_task.cancel()
    map_event_task.cancel()
    message_expiry_task.cancel()
    community_event_task.cancel()
    organization_task.cancel()
app = FastAPI(title="Central Messaging API", version="2.0.0", lifespan=lifespan)


# ─────────────────────────────────────────────────────────────────────────
# LINGUA DELLA RICHIESTA
# ─────────────────────────────────────────────────────────────────────────
#
# L'app manda X-Central-Lang con la lingua scelta. Si usa un header proprio
# e non Accept-Language perche il browser del pannello web manda sempre il
# suo Accept-Language, e il pannello e scritto in italiano: tradurgli solo
# gli errori darebbe una pagina mezza e mezza. Senza header: italiano.
class _LinguaMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] not in ("http", "websocket"):
            await self.app(scope, receive, send)
            return
        lang = None
        for k, v in scope.get("headers", []):
            if k == b"x-central-lang":
                lang = i18n.normalize(v.decode("latin-1"))
                break
        token = i18n.current_lang.set(lang or i18n.SOURCE)
        try:
            await self.app(scope, receive, send)
        finally:
            i18n.current_lang.reset(token)


app.add_middleware(_LinguaMiddleware)

from fastapi import Request  # noqa: E402
from fastapi.exceptions import RequestValidationError  # noqa: E402
from fastapi.exception_handlers import (  # noqa: E402
    http_exception_handler as _http_handler_base,
    request_validation_exception_handler as _validation_handler_base,
)
from starlette.exceptions import HTTPException as _StarletteHTTPException  # noqa: E402


@app.exception_handler(_StarletteHTTPException)
async def _errore_tradotto(request: Request, exc: _StarletteHTTPException):
    """Gli errori restano scritti in italiano nel codice: qui escono nella
    lingua dell'app. Testi senza traduzione passano invariati."""
    if i18n.current_lang.get() != i18n.SOURCE and exc.detail is not None:
        exc = _StarletteHTTPException(
            status_code=exc.status_code,
            detail=i18n.localize_obj(exc.detail),
            headers=getattr(exc, "headers", None),
        )
    return await _http_handler_base(request, exc)


@app.exception_handler(RequestValidationError)
async def _validazione_tradotta(request: Request, exc: RequestValidationError):
    if i18n.current_lang.get() != i18n.SOURCE:
        errori = []
        for e in exc.errors():
            e = dict(e)
            msg = e.get("msg")
            if isinstance(msg, str) and msg.startswith("Value error, "):
                e["msg"] = "Value error, " + i18n.localize(msg[len("Value error, "):])
            errori.append(e)
        exc = RequestValidationError(errori, body=exc.body)
    return await _validation_handler_base(request, exc)
# CORS: origini esplicite, non "*".
#
# L'app Android non passa dal CORS — e il pannello web a farlo. Con
# allow_origins=["*"] e allow_credentials=True qualunque sito poteva provare
# a far partire richieste autenticate dal browser di un utente collegato;
# oltretutto e una combinazione che le specifiche vietano, quindi non
# funzionava nemmeno come voleva.
#
# CORS_ORIGINS: elenco separato da virgole, es.
#   CORS_ORIGINS=https://central.example.com,https://www.central.example.com
_cors_env = os.getenv("CORS_ORIGINS", "").strip()
_cors_origins = [o.strip() for o in _cors_env.split(",") if o.strip()]
if not _cors_origins:
    # Senza configurazione non si apre a tutti: si apre a nessuno. Il
    # pannello web smette di funzionare e ce ne si accorge subito, che e
    # meglio di una porta lasciata aperta di cui nessuno si accorge.
    _cors_origins = []
    logger.warning(
        "CORS_ORIGINS non configurata: nessuna origine esterna e autorizzata. "
        "Il pannello web non funzionera finche non viene impostata."
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)
app.include_router(auth.router,               prefix="/auth",        tags=["auth"])
app.include_router(users.router,              prefix="/users",       tags=["users"])
app.include_router(friends.router,            prefix="/friends",     tags=["friends"])
app.include_router(chats.router,              prefix="/chats",       tags=["chats"])
# Reazioni e voti dei sondaggi: sotto /chats, accanto ai messaggi.
from routers import message_extras as message_extras_router
app.include_router(message_extras_router.router, prefix="/chats",   tags=["chats"])
app.include_router(groups.router,             prefix="/groups",      tags=["groups"])
app.include_router(boards.router,             prefix="/boards",      tags=["boards"])
app.include_router(devices.router,            prefix="/devices",     tags=["devices"])
app.include_router(gallery.router,            prefix="/gallery",     tags=["gallery"])
app.include_router(trips.router,              prefix="/trips",       tags=["trips"])
app.include_router(blocks.router,             prefix="/blocks",      tags=["blocks"])
app.include_router(broadcast.router,          prefix="/broadcast",   tags=["broadcast"])
app.include_router(share.router,                                     tags=["share"])
app.include_router(scheduled.router,          prefix="/scheduled",   tags=["scheduled"])
app.include_router(communities.router,        prefix="/communities", tags=["communities"])
app.include_router(media.router,              prefix="/api/media",   tags=["media"])
app.include_router(calls.router,              prefix="/calls",       tags=["calls"])
app.include_router(turn.router,               tags=["turn"])
app.include_router(call_reports.router,       tags=["call-reports"])
app.include_router(guardian.router,           tags=["guardian"])
app.include_router(geofence.router,           tags=["geofence"])
app.include_router(check_in.router,           tags=["check-in"])
app.include_router(legal.router,                                     tags=["legal"])
# Pannello web: monitoraggio guardiano, chat con decifratura nel browser,
# esportazione e cancellazione dei propri dati (GDPR art. 15, 17 e 20).
app.include_router(guardian_dashboard.router,                        tags=["guardian-dashboard"])
# Segnalazione di contenuti e utenti + coda di moderazione. Requisito Play
# per ogni app con contenuti generati dagli utenti.
app.include_router(reports.router,          prefix="/reports",      tags=["reports"])
app.include_router(announcements.router,    prefix="/announcements", tags=["announcements"])
# Provvedimenti disciplinari e ricorsi. Gli endpoint sotto /sanctions/me
# sono gli unici che un account escluso puo ancora raggiungere: senza,
# il tasto "ricorso" mostrato nell'app non potrebbe funzionare.
app.include_router(sanctions.router,        prefix="/sanctions",    tags=["sanctions"])
# Zone di interesse: ospedali, forze dell'ordine, vigili del fuoco.
# Le rotte sono secondarie di proposito — l'app porta l'archivio dentro
# l'APK e risponde da sola, senza rete. Qui si serve solo l'aggiornamento
# periodico e una ricerca di riserva. Nessuna di queste interroga
# OpenStreetMap: i dati arrivano da tools/import_poi.py, che gira una volta
# al mese fuori da qualsiasi richiesta di utente.
app.include_router(poi.router,              prefix="/poi",          tags=["poi"])
# Central City: casa, vicini, negozio e monete (routers/city.py).
app.include_router(city.router,             prefix="/city",         tags=["city"])
# Central City dal vivo: WebSocket /ws/city (routers/city_live.py).
app.include_router(city_live.router,        tags=["city"])
# Registro eventi di sicurezza: conferme, mancate conferme, arrivi, SOS.
# Solo lettura e cancellazione — le righe le scrivono i monitor, non l'app.
app.include_router(safety_log.router,       prefix="/safety-log",   tags=["safety-log"])
app.include_router(map_events.router,       prefix="/map-events",   tags=["map-events"])
app.include_router(billing.router,                                   tags=["billing"])
# Aziende clienti: piano Base o Completo per referenti, controllori e
# operatori di un'azienda, gestito dal pannello di chi modera.
from routers import organizations as organizations_router
app.include_router(organizations_router.router,                      tags=["organizations"])
# Contatore delle visite di getcentral.net (senza cookie, dati in Europa).
from routers import site_analytics as site_analytics_router
app.include_router(site_analytics_router.router,                     tags=["site"])
app.include_router(i18n_packs.router,         prefix="/i18n",        tags=["i18n"])
app.include_router(websocket.router,          tags=["websocket"])

# ─────────────────────────────────────────────────────────────────────────
# FILE STATICI SERVITI DA NOI
# ─────────────────────────────────────────────────────────────────────────
#
# Contiene la libreria di crittografia usata dal pannello web quando il
# browser non sa fare X25519 da solo.
#
# Prima veniva caricata al volo da una rete di distribuzione esterna. Era
# la dipendenza piu pericolosa del progetto: quel codice gira nella pagina
# dove l'utente digita la frase di recupero, quindi chi controlla quel
# servizio — o chiunque riesca a sostituirne il contenuto — potrebbe
# servire una versione modificata che si porta via la chiave privata. La
# cifratura da un capo all'altro verrebbe aggirata senza toccare il nostro
# server, e senza lasciare traccia da nessuna parte.
#
# Serve il file da qui: stesso dominio, stessa fiducia del resto della
# pagina, nessun terzo in mezzo. Il file e versionato nel repository e
# cambia solo quando lo cambiamo noi.
_STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
if os.path.isdir(_STATIC_DIR):
    app.mount("/static", StaticFiles(directory=_STATIC_DIR), name="static")
else:
    logger.warning("Cartella static assente: il pannello web perde il ripiego X25519")
# Nota: /media locale rimosso. I file caricati dopo questo deploy vengono
# serviti direttamente dall'URL pubblico di Scaleway Object Storage
# (MEDIA_BASE_URL), non piu' da questo processo. Vedi services/media.py.
@app.get("/health", tags=["health"])
async def health_check() -> dict:
    return {"status": "ok"}

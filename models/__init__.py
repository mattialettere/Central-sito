"""Import all models so Base.metadata is fully populated."""

from .user import User, UserMedia, MediaLike
from .referral import Referral
from .friend_request import FriendRequest
from .chat import Chat, ChatMember, GroupKey
from .board import Board, BoardElement
from .map_event import MapEvent, MapEventPhoto, MapEventPresence
from .device import Device
from .media_comment import MediaComment, MediaHidden
from .trip import Trip, TripWatcher, TripPosition
from .block import BlockedUser
from .broadcast import BroadcastList, BroadcastListMember
from .media_share import MediaShare, MediaLink
from .scheduled import ScheduledMessage
from .message import Message
from .community import Community, CommunityMember, CommunityJoinRequest, CommunityPost, CommunityPostComment, CommunityEvent, CommunityEventRsvp
from .call import Call
from .content_report import ContentReport
from .sanction import UserSanction
from .announcement import Announcement, AnnouncementSeen
# Punti di interesse per la sicurezza (ospedali, forze dell'ordine, vigili
# del fuoco). Non e' importato da nessun altro modello, quindi senza questa
# riga Base.metadata non lo conterrebbe: un --autogenerate futuro non
# vedrebbe la tabella e proporrebbe di CANCELLARLA, perche' Alembic
# confronta il database con cio' che i modelli dichiarano.
from .poi import PointOfInterest

# Registro eventi di sicurezza. Come per i POI, senza questa riga
# Base.metadata non conterrebbe le tabelle e un --autogenerate futuro
# proporrebbe di cancellarle.
from .safety_event import SafetyEvent, SafetyLogPrefs

# Ricevute di consegna e lettura.
from .message_receipt import MessageReceipt

# Stato dell'abbonamento. Come per i POI, senza questa riga Base.metadata
# non conterrebbe la tabella e un --autogenerate futuro proporrebbe di
# cancellarla.
from .subscription import Subscription

# Registro dei regali fatti dal pannello: stesso motivo, una tabella che
# Base.metadata non conosce verrebbe proposta per la cancellazione.
from .subscription_gift import SubscriptionGift

# Aziende clienti e le loro persone: stesso motivo.
from .organization import Organization, OrganizationMember

# Visite al sito getcentral.net (contatore senza cookie).
from .site_visit import SiteVisit

__all__ = [
    "SubscriptionGift",
    "Organization", "OrganizationMember",
    "SiteVisit",
    "User", "UserMedia", "MediaLike",
    "FriendRequest",
    "Chat", "ChatMember", "GroupKey",
    "Board",
    "BoardElement",
    "Referral",
    "MapEvent",
    "MapEventPhoto",
    "MapEventPresence",
    "Device",
    "MediaComment", "MediaHidden",
    "Trip", "TripWatcher", "TripPosition",
    "BlockedUser",
    "BroadcastList", "BroadcastListMember",
    "MediaShare", "MediaLink",
    "ScheduledMessage",
    "Message",
    "Community", "CommunityMember", "CommunityJoinRequest", "CommunityPost", "CommunityPostComment",
    "Call",
    "ContentReport",
    "UserSanction",
    "Announcement", "AnnouncementSeen",
    "PointOfInterest",
    "SafetyEvent", "SafetyLogPrefs",
    "MessageReceipt",
    "Subscription",
]

# Reazioni con emoji e voti dei sondaggi.
from .message_extras import MessageReaction, PollVote

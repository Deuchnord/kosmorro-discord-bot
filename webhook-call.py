import requests

from kosmorrolib import (
    get_events,
    Event,
    EventType,
    Object,
    ObjectIdentifier,
    SeasonType,
    LunarEclipseType,
)
from os import environ
from babel import dates
from datetime import date


def get_object_name(o: Object) -> str:
    return {
        ObjectIdentifier.SUN: "le Soleil",
        ObjectIdentifier.MERCURY: "Mercure",
        ObjectIdentifier.VENUS: "Vénus",
        ObjectIdentifier.MOON: "la Lune",
        ObjectIdentifier.MARS: "Mars",
        ObjectIdentifier.JUPITER: "Jupiter",
        ObjectIdentifier.SATURN: "Saturne",
        ObjectIdentifier.URANUS: "Uranus",
        ObjectIdentifier.NEPTUNE: "Neptune",
        ObjectIdentifier.PLUTO: "Pluton",
    }.get(o.identifier)


def describe_event(event: Event) -> (int, str):
    hour = event.start_time.strftime("%H:%M")
    return {
        EventType.OPPOSITION: (
            5,
            lambda e: "C'est le moment idéal d'observer %s ! :star_struck:"
            % get_object_name(e.objects[0]),
            lambda e: ":star: **%s :** %s arrive à l'opposition"
            % (hour, get_object_name(e.objects[0])),
        ),
        EventType.CONJUNCTION: (
            1,
            lambda e: "Petit rapprochement entre %s et %s aujourd'hui :slight_smile:"
            % (get_object_name(e.objects[0]), get_object_name(e.objects[1])),
            lambda e: ":star: **%s :** %s et %s sont en conjonction"
            % (hour, get_object_name(e.objects[0]), get_object_name(e.objects[1])),
        ),
        EventType.OCCULTATION: (
            2,
            lambda e: "Belle occultation de %s par %s à prévoir !"
            % (get_object_name(e.objects[1]), get_object_name(e.objects[0])),
            lambda e: ":star: **%s :** %s occulte %s"
            % (hour, get_object_name(e.objects[0]), get_object_name(e.objects[1])),
        ),
        EventType.MAXIMAL_ELONGATION: (
            3,
            lambda e: "%s est au plus loin du Soleil ! C'est le moment idéal pour l'observer !"
            % get_object_name(e.objects[0]),
            lambda e: ":star: **%s :** L'élongation de %s est maximale"
            % (hour, get_object_name(e.objects[0])),
        ),
        EventType.PERIGEE: (
            0,
            None,
            lambda e: ":star: **%s :** %s arrive à son périgée"
            % (hour, get_object_name(e.objects[0])),
        ),
        EventType.APOGEE: (
            0,
            None,
            lambda e: ":star: **%s :** %s arrive à son apogée"
            % (hour, get_object_name(e.objects[0])),
        ),
        EventType.SEASON_CHANGE: (
            0,
            None,
            lambda e: ":star: %s a lieu à %s aujourd'hui"
            % (
                "L'équinoxe"
                if event.details["season"]
                in [SeasonType.MARCH_EQUINOX, SeasonType.SEPTEMBER_EQUINOX]
                else "Le solstice",
                hour,
            ),
        ),
        EventType.LUNAR_ECLIPSE: (
            10,
            lambda e: "Ne loupez pas l'éclipse de Lune aujourd'hui !",
            lambda e: ":star: **%s :** éclipse %s de Lune (atteignant son maximum à %s)"
            % (
                hour,
                {
                    LunarEclipseType.PARTIAL: "partielle",
                    LunarEclipseType.PENUMBRAL: "pénombrale",
                    LunarEclipseType.TOTAL: "totale",
                }.get(e.details["type"]),
                e.details["maximum"].strftime("%H:%M"),
            ),
        ),
    }.get(event.event_type)


events = []
best_weight, best_event, message_content = 0, None, None

for event in get_events():
    weight, message, desc = describe_event(event)
    events.append(desc(event))
    if weight > best_weight:
        best_event = event
        message_content = message(event)

today = date.today()

if (today.day, today.month) == (1, 4):
    events.append(":star: **13:00 :** maximum de l'essaim de poissons")


if len(events) == 0:
    print("No events today, no message to send.")
    exit(0)

print("%d events found, calling webhook." % len(events))


WEBHOOK = environ.get("DISCORD_WEBHOOK")


requests.post(
    url=WEBHOOK,
    json={
        "content": message_content
        if message_content is not None
        else "Sortez les télescopes, voici les événements astro du jour !",
        "embeds": [
            {
                "title": dates.format_date(format="full", locale="fr").capitalize(),
                "footer": {
                    "text": "Propulsé par Kosmorrolib - les horaires sont données en UTC.",
                    "icon_url": "https://raw.githubusercontent.com/Kosmorro/logos/main/png/kosmorro-icon.png",
                },
                "description": "\n".join(events),
            }
        ],
    },
)

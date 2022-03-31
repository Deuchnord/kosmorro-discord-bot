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
            lambda e: f":star: **{hour} :** {get_object_name(e.objects[0])} arrive à l'opposition",
            lambda e: f"C'est le moment idéal d'observer {get_object_name(e.objects[0])} ! :star_struck:",
            lambda n: f"Nous avons {n} planètes à l'opposition aujourd'hui ! :telescope:",
        ),
        EventType.CONJUNCTION: (
            1,
            lambda e: f":star: **{hour} :** {get_object_name(e.objects[0])} et {get_object_name(e.objects[1])} sont en conjonction",
            lambda e: f"Petit rapprochement entre {get_object_name(e.objects[0])} et {get_object_name(e.objects[1])} aujourd'hui !",
            lambda n: f"Nous avons {n} planètes qui se rencontrent aujourd'hui !",
        ),
        EventType.OCCULTATION: (
            2,
            lambda e: f":star: **{hour} :** {get_object_name(e.objects[0])} occulte {get_object_name(e.objects[1])}",
            lambda e: f"Belle occultation de {get_object_name(e.objects[1])} par {get_object_name(e.objects[0])} à prévoir !",
            lambda n: f"Sortez les télescopes, il y a {n} occultations à observer aujourd'hui !",
        ),
        EventType.MAXIMAL_ELONGATION: (
            3,
            lambda e: f":star: **{hour} :** L'élongation de {get_object_name(e.objects[0])} est maximale",
            lambda e: f"{get_object_name(e.objects[0])} est au plus loin du Soleil ! C'est le moment idéal pour l'observer !",
            lambda n: f"Mercure et Vénus sont au plus loin du Soleil ! En même temps ! :star_struck:",
        ),
        EventType.PERIGEE: (
            0,
            lambda e: f":star: **{hour} :** {get_object_name(e.objects[0])} arrive à son périgée",
            None,
            None,
        ),
        EventType.APOGEE: (
            0,
            lambda e: f":star: **{hour} :** {get_object_name(e.objects[0])} arrive à son apogée",
            None,
            None,
        ),
        EventType.SEASON_CHANGE: (
            0,
            lambda e: f":star: %s a lieu à {hour} aujourd'hui"
            % (
                "L'équinoxe"
                if event.details["season"]
                in [SeasonType.MARCH_EQUINOX, SeasonType.SEPTEMBER_EQUINOX]
                else "Le solstice"
            ),
            None,
            None,
        ),
        EventType.LUNAR_ECLIPSE: (
            10,
            lambda e: f":star: **{hour} :** éclipse %s de Lune, atteignant son maximum à %s"
            % (
                {
                    LunarEclipseType.PARTIAL: "partielle",
                    LunarEclipseType.PENUMBRAL: "pénombrale",
                    LunarEclipseType.TOTAL: "totale",
                }.get(e.details["type"]),
                e.details["maximum"].strftime("%H:%M"),
            ),
            lambda e: "Ne loupez pas l'éclipse de Lune aujourd'hui !",
            None,
        ),
    }.get(event.event_type)


events = []
best_weight, best_event, message_content = 0, None, None
message_sing, message_plur = None, None
highest_weight_number = 1

for event in get_events():
    weight, desc, message_sing, message_plur = describe_event(event)
    events.append(desc(event))
    print(f"Found {event.event_type}")

    if weight > best_weight:
        print(
            f"    This is a better event than the previous one ({best_event.event_type if best_event is not None else 'none'})."
        )
        highest_weight_number = 1
        best_weight = weight
        best_event = event
    elif event.event_type == best_event.event_type:
        highest_weight_number += 1
        print(f"    There are {highest_weight_number} of them.")

print()

today = date.today()

if (today.day, today.month) == (1, 4):
    events.append(":star: maximum de l'essaim de poissons")


if len(events) == 0:
    print("No events today, no message to send.")
    exit(0)

if highest_weight_number > 1:
    message_content = message_plur(highest_weight_number)
else:
    message_content = message_sing(best_event)

if message_content is None:
    message_content = "Sortez les télescopes, voici les événements astro du jour !"

print("%d events found, calling webhook." % len(events))

WEBHOOK = environ.get("DISCORD_WEBHOOK")

requests.post(
    url=WEBHOOK,
    json={
        "content": message_content,
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

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
from datetime import date, datetime, timedelta, timezone


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


def _get_events() -> [Event]:
    today = date.today()
    min_dt, max_dt = get_bound_dt()

    for d in [today, today + timedelta(days=1)]:
        for event in get_events(d):
            if min_dt <= event.start_time <= max_dt:
                yield event


def get_bound_dt() -> (datetime, datetime):
    now = datetime.now()
    min_dt = datetime(now.year, now.month, now.day, now.hour + 1, tzinfo=timezone.utc)
    max_dt = datetime(now.year, now.month, now.day + 1, now.hour + 1, tzinfo=timezone.utc)

    return min_dt, max_dt


events_txt = []
nb_events = 0
best_weight, best_event, message_content = 0, None, None
message_sing, message_plur = None, None
highest_weight_number = 1
today = date.today()
next_night = False

for event in _get_events():
    nb_events += 1

    if not next_night and today.day != event.start_time.day:
        next_night = True
        print("Tomorrow's events:")
        if nb_events > 1:
            events_txt.append("")
            events_txt.append("**Et la nuit prochaine :**")
        else:
            events_txt.append("**La nuit prochaine :**")

    weight, desc, message_sing, message_plur = describe_event(event)
    events_txt.append(desc(event))
    print(f"Found {event.event_type} at {event.start_time}")

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

if len(events_txt) == 0:
    print("No events found, no message to send.")
    exit(0)

if highest_weight_number > 1:
    message_content = message_plur(highest_weight_number)
else:
    message_content = message_sing(best_event)

if message_content is None:
    message_content = "Sortez les télescopes, voici les événements astro du jour !"

print(f"{nb_events} event{'s' if nb_events > 1 else ''} found, calling webhook.")

WEBHOOK = environ.get("DISCORD_WEBHOOK")

if WEBHOOK is None:
    print("Webhook not provided, please define the `DISCORD_WEBHOOK` environment variable!")
    exit(1)

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
                "description": "\n".join(events_txt),
            }
        ],
    },
)

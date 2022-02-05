import requests

from kosmorrolib import get_events, Event, EventType, Object, ObjectIdentifier
from os import environ
from babel import dates

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


def describe_event(event: Event) -> str:
    return {
            EventType.CONJUNCTION: lambda e: ":star: **%s :** %s et %s sont en conjonction" % (event.start_time.strftime("%H:%M"), get_object_name(e.objects[0]), get_object_name(e.objects[1])),
            EventType.MAXIMAL_ELONGATION: lambda e: ":star: **%s :** L'élongation de %s est maximale" % (event.start_time.strftime("%H:%M"), get_object_name(e.objects[0])),
            EventType.APOGEE: lambda e: ":star: **%s :** %s arrive à son apogée" % (event.start_time.strftime("%H:%M"), get_object_name(e.objects[0])),
            EventType.PERIGEE: lambda e: ":star: **%s :** %s arrive à son périgée" % (event.start_time.strftime("%H:%M"), get_object_name(e.objects[0])),
            EventType.OCCULTATION: lambda e: ":star: **%s :** %s occulte %s" % (event.start_time.strftime("%H:%M"), get_object_name(e.objects[0]), get_object_name(e.objects[1])),
            EventType.OPPOSITION: lambda e: ":star: **%s :** %s arrive à l'opposition" % (event.start_time.strftime("%H:%M"), get_object_name(e.objects[0])),
    }.get(event.event_type)(event)


events = []

for event in get_events():
    events.append(describe_event(event))


if len(events) == 0:
    print("No events today, no message to send.")
    exit(0)


print("%d events found, calling webhook." % len(events))


WEBHOOK = environ.get("DISCORD_WEBHOOK")


requests.post(url=WEBHOOK, json={
	"content": "Sortez les télescopes, voici les événements astro du jour !",
	"embeds": [
		{
			"title": dates.format_date(format="full", locale="fr").capitalize(),
			"footer": {
				"text": "Propulsé par Kosmorrolib - les horaires sont données en UTC.",
				"icon_url": "https://raw.githubusercontent.com/Kosmorro/logos/main/png/kosmorro-icon.png"
			},
			"description": "\n".join(events)
		}
	]
})

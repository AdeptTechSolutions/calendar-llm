import os
import pickle
from datetime import datetime, timedelta

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/calendar"]


def get_google_calendar_service():
    creds = None
    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "secrets/credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)

        with open("token.pickle", "wb") as token:
            pickle.dump(creds, token)

    return build("calendar", "v3", credentials=creds)


def check_availability(start_time, end_time, attendees):
    service = get_google_calendar_service()

    freebusy_query = {
        "timeMin": start_time,
        "timeMax": end_time,
        "items": [{"id": email} for email in attendees],
    }

    response = service.freebusy().query(body=freebusy_query).execute()
    calendars = response.get("calendars", {})

    all_available = True
    for email, busy_info in calendars.items():
        if busy_info["busy"]:
            all_available = False
            break

    return all_available


def schedule_meeting(title, description, start_time, end_time, attendees):
    service = get_google_calendar_service()

    event = {
        "summary": title,
        "description": description,
        "start": {"dateTime": start_time, "timeZone": "Asia/Karachi"},
        "end": {"dateTime": end_time, "timeZone": "Asia/Karachi"},
        "attendees": [{"email": email} for email in attendees],
    }

    event = service.events().insert(calendarId="primary", body=event).execute()
    return event.get("id")


def reschedule_meeting(event_id, new_start_time, new_end_time):
    service = get_google_calendar_service()

    event = service.events().get(calendarId="primary", eventId=event_id).execute()
    event["start"]["dateTime"] = new_start_time
    event["end"]["dateTime"] = new_end_time

    updated_event = (
        service.events()
        .update(calendarId="primary", eventId=event_id, body=event)
        .execute()
    )
    return updated_event.get("id")


def cancel_meeting(event_id):
    service = get_google_calendar_service()
    service.events().delete(calendarId="primary", eventId=event_id).execute()
    return True


tools_description = [
    {
        "type": "function",
        "function": {
            "name": "check_availability",
            "description": "Check calendar availability for attendees in specified time window",
            "parameters": {
                "type": "object",
                "properties": {
                    "start_time": {
                        "type": "string",
                        "description": "Start time in ISO 8601 format with timezone offset (e.g., 2025-01-22T14:00:00+05:00)",
                    },
                    "end_time": {
                        "type": "string",
                        "description": "End time in ISO 8601 format with timezone offset (e.g., 2025-01-22T15:00:00+05:00)",
                    },
                    "attendees": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of attendee email addresses",
                    },
                },
                "required": ["start_time", "end_time", "attendees"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "schedule_meeting",
            "description": "Schedule a new meeting with attendees",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Meeting title"},
                    "description": {
                        "type": "string",
                        "description": "Meeting description",
                    },
                    "start_time": {
                        "type": "string",
                        "description": "Start time in ISO 8601 format with timezone offset (e.g., 2025-01-22T14:00:00+05:00)",
                    },
                    "end_time": {
                        "type": "string",
                        "description": "End time in ISO 8601 format with timezone offset (e.g., 2025-01-22T15:00:00+05:00)",
                    },
                    "attendees": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of attendee email addresses",
                    },
                },
                "required": ["title", "start_time", "end_time", "attendees"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "reschedule_meeting",
            "description": "Reschedule an existing meeting to new time",
            "parameters": {
                "type": "object",
                "properties": {
                    "event_id": {
                        "type": "string",
                        "description": "ID of the event to reschedule",
                    },
                    "new_start_time": {
                        "type": "string",
                        "description": "New start time in ISO 8601 format with timezone offset",
                    },
                    "new_end_time": {
                        "type": "string",
                        "description": "New end time in ISO 8601 format with timezone offset",
                    },
                },
                "required": ["event_id", "new_start_time", "new_end_time"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "cancel_meeting",
            "description": "Cancel an existing meeting",
            "parameters": {
                "type": "object",
                "properties": {
                    "event_id": {
                        "type": "string",
                        "description": "ID of the event to cancel",
                    }
                },
                "required": ["event_id"],
            },
        },
    },
]

import os
import datetime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from backend.config import PROJECT_ROOT

SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]
CREDENTIALS_PATH = PROJECT_ROOT / "credentials.json"
TOKEN_PATH = PROJECT_ROOT / "token.json"

def get_calendar_service():
    creds = None
    if TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
        
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not CREDENTIALS_PATH.exists():
                raise FileNotFoundError(
                    "Google Calendar credentials.json is missing! "
                    "Please download it from Google Cloud Console and place it in the project root."
                )
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_PATH), SCOPES)
            creds = flow.run_local_server(port=0)
            
        with open(TOKEN_PATH, "w") as token:
            token.write(creds.to_json())

    return build("calendar", "v3", credentials=creds)

def get_next_meetings(max_results: int = 3) -> str:
    try:
        service = get_calendar_service()
    except FileNotFoundError as e:
        return str(e)
    except Exception as e:
        return f"Failed to authenticate with Google Calendar: {e}"

    try:
        now = datetime.datetime.utcnow().isoformat() + "Z"  # 'Z' indicates UTC time
        events_result = (
            service.events()
            .list(
                calendarId="primary",
                timeMin=now,
                maxResults=max_results,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
        events = events_result.get("items", [])

        if not events:
            return "You have no upcoming meetings dynamically scheduled."

        result = "Your upcoming meetings are: "
        for event in events:
            start = event["start"].get("dateTime", event["start"].get("date"))
            # convert ISO to readable 
            try:
                dt = datetime.datetime.fromisoformat(start)
                time_str = dt.strftime("%I:%M %p on %A")
            except Exception:
                time_str = start
            summary = event.get("summary", "Untitled Meeting")
            result += f"\n- {summary} at {time_str}"
            
        return result.strip()
        
    except HttpError as error:
        return f"An error occurred reading the calendar: {error}"

import re
import requests
import json
from plugin import Plugin

# Regular expression to match the !np command and the username argument
np_re = re.compile(r"!np(\s+\S+)?")

# Dictionary to store previously seen usernames
seen_usernames = {}


class LastFMPlugin(Plugin):
    def __init__(self, api_key):
        super().__init__()
        self.api_key = api_key
        self.commands = {
            "!np": self.now_playing
        }

    def now_playing(self, username=None):
        global seen_usernames

        np_match = np_re.match(username)
        if np_match:
            np_username = np_match.group(1)

            if not np_username:
                if username in seen_usernames:
                    np_username = seen_usernames[username]
                else:
                    return f"Usage: !np <username>"
            else:
                seen_usernames[username] = np_username

            params = {
                "method": "user.getrecenttracks",
                "user": np_username,
                "api_key": self.api_key,
                "format": "json",
                "limit": 2
            }

            try:
                response = requests.get("https://ws.audioscrobbler.com/2.0/", params=params)
                response.raise_for_status()
                data = json.loads(response.content)
            except requests.exceptions.RequestException:
                return f"Error: failed to fetch {np_username}'s recent tracks."

            tracks = data["recenttracks"]["track"]
            now_playing = False

            if len(tracks) > 0:
                now_playing = tracks[0].get("@attr", {}).get("nowplaying") == "true"

            if now_playing:
                artist = tracks[0]["artist"]["#text"]
                title = tracks[0]["name"]
                return f"{np_username} is now playing: {artist} - {title}"
            elif len(tracks) > 1:
                artist = tracks[1]["artist"]["#text"]
                title = tracks[1]["name"]
                return f"{np_username} is not currently scrobbling. Last scrobbled track: {artist} - {title}"
            else:
                return f"{np_username} has no recent tracks."

        return None

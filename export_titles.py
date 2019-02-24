from google_helpers import buildYoutube, request_all
from input_helpers import inputPlaylist, tryPairseInt

import argparse
import json


def parseTitle(title):
    # extract lection/seminar number and topic
    parts = title.split(".")

    for i, part in enumerate(parts):
        smallerParts = part.split(" ")
        if not smallerParts:
            continue
        maybeNumber = tryPairseInt(smallerParts[-1])
        if maybeNumber is None:
            continue

        topic = "\n".join(filter(None, map(str.strip, parts[i + 1:])))
        return maybeNumber, topic


def extractTitles(youtube, playlistId):
    videos = list(request_all(youtube.playlistItems().list, part="snippet,contentDetails", playlistId=playlistId))
    details = [parseTitle(video["snippet"]["title"]) for video in videos]

    return [
        {
            "id": video["contentDetails"]["videoId"],
            "number": number,
            "topic": topic,
        }
        for video, (number, topic) in zip(videos, details)
    ]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("output", help="Output file with titles")
    args = parser.parse_args()

    youtube = buildYoutube()
    playlist = inputPlaylist(youtube, mine=True) # channelId="UCdxesVp6Fs7wLpnp1XKkvZg")
    titles = extractTitles(youtube, playlist["id"])

    with open(args.output, "wt", encoding="utf-8") as file:
        json.dump(titles, file, indent=4, sort_keys=True, ensure_ascii=False)


if __name__ == "__main__":
    main()
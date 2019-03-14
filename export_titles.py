from google_helpers import buildYoutube, request_all
from input_helpers import inputPlaylist, tryPairseInt

import sys
import argparse
import json
import re
from pprint import pprint


def parseTitle(title):
    removeWhitespace = lambda s: "".join(s.split())
    reg = re.compile(removeWhitespace(
        r"""
        ^(?P<subject>[^\d,]*)\s*(?P<seminar>[,\.]\s*[сС]еминар)?\s*(?P<number>\d+)\.(?P<topic>.*)
        """
    ))
    
    match = reg.match(title)
    if match is None:
        raise ValueError("Can't parse title %r" % title)

    return {
        "subject": match["subject"].strip(),
        "number": int(match["number"].strip()),
        "seminar": match["seminar"] is not None,
        "topic": match["topic"].strip(),
    }


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


def main_gen_base_export_list():
    youtube = buildYoutube()
    playlists = request_all(youtube.playlists().list, mine=True, part="snippet", resultsPerPage=3)

    from pprint import pprint

    smt = [
        {
            "title": playlist["snippet"]["title"],
            "id": playlist["id"],
            "url": "https://www.youtube.com/playlist?list={}".format(playlist["id"]),
            "strategy": None,
        }
        for playlist in playlists
    ]

    with open("export_list.json", "w", encoding="utf-8") as f:
        json.dump(smt, f, indent=4, sort_keys=True, ensure_ascii=False)

def stripComments(text):
    lines = text.split("\n")
    nonCommentLines = [line for line in lines if not line.strip().startswith("//")]
    nonCommentText = "\n".join(nonCommentLines)
    return nonCommentText

if __name__ == "__main__":
    # main_gen_base_export_list()

    youtube = buildYoutube()
    with open("export_list.json", "r", encoding="utf-8") as f:
        export_list = json.loads(stripComments(f.read()))

    with open("templates/info.json", "r", encoding="utf-8") as f:
        templates_info = json.load(f)

    for playlist in export_list:
        if playlist["strategy"] == "auto":
            videos = list(request_all(youtube.playlistItems().list, part="snippet,contentDetails", playlistId=playlist["id"]))
            for video in videos:
                details = parseTitle(video["snippet"]["title"])
                matches = [template["filename"] for template in templates_info if template["subject"] == details["subject"]]
                
                pprint(details)

                if len(matches) == 1:
                    match = matches[0]
                elif not matches:
                    match = None
                else:
                    match = matches

                videoId = video["contentDetails"]["videoId"]
                smt = {
                    "id": videoId,
                    "url": "https://www.youtube.com/watch?v={}&list={}".format(videoId, playlist["id"]),
                    "template": match,
                    "number": details["number"],
                    "topic": details["topic"],
                }
                pprint(smt)

    # videos = []

    # request_all(youtube.playlistItems().list, part="snippet,contentDetails", playlistId=playlist["id"])

    # for playlist in playlists:
    #     print("Processing playlist:", playlist["snippet"]["title"])
    #     playlist_videos = request_all(youtube.playlistItems().list, part="snippet,contentDetails", playlistId=playlist["id"])
    #     videos.extend(playlist_videos)

    # with open("videos.json", "w", encoding="utf-8") as f:
    #     json.dump(videos, f, indent=4, sort_keys=True, ensure_ascii=False)

    # with open("videos.json", "r", encoding="utf-8") as f:
    #     videos = json.load(f)

    # import re
    # removeWhitespace = lambda s: "".join(s.split())
    # reg = re.compile(removeWhitespace(
    #     r"""
    #     ^(?P<name>[^,]*)\s*(?P<seminar>,[^,]*)?\s*(?P<number>\d+)\..*
    #     """
    #     #
    # ))

    # for video in videos:
    #     title = video["snippet"]["title"]
    #     description = video["snippet"]["description"]
    #     m = reg.match(title)
    #     if m is None:
    #         print(title)
    #     # print(m.groups())
    #     # break
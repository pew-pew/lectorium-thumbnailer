from google_helpers import buildYoutube

import os
import argparse
import json

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("titles", help="path to file with video titles")
    parser.add_argument("thumbnails", help="directory with thumbnails")

    args = parser.parse_args()

    with open(args.titles, "rt", encoding="utf-8") as file:
        videos = json.load(file)

    youtube = buildYoutube()

    logProgress = lambda i, msg: print("{:2}/{:2}: {}".format(i, len(videos), msg))
    for i, video in enumerate(videos):
        logProgress(i + 1, "number %s, topic %r" % (video["number"], video["topic"]))
        path = os.path.join(args.thumbnails, "%s.png" % video["number"])
        youtube.thumbnails().set(
            media_body=path,
            videoId=video["id"]
          ).execute()
    print("Done!")
main()
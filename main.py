from thumbnail_generator import ThumbnailGenerator
from google_helpers import buildYoutube, request_all
from input_helpers import inputPlaylist, tryPairseInt, yesno

import os
from pprint import pprint
import argparse


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

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("template", help="path to .psd file")
    # parser.add_argument("topics", help="path to file with topics")
    parser.add_argument("output", help="output directory")

    args = parser.parse_args()

    if not os.path.exists(args.template):
        parser.error("Template file %s doesn't exist" % args.template)
    if not os.path.exists(args.output):
        parser.error("Output directory %s doesn't exist" % args.output)

    youtube = buildYoutube()

    playlist = inputPlaylist(youtube, mine=True) #channelId="UCdxesVp6Fs7wLpnp1XKkvZg")
    print("Selected playlist:", playlist["snippet"]["title"])

    videos = list(request_all(youtube.playlistItems().list, part="snippet,contentDetails", playlistId=playlist["id"]))

    titles = [video["snippet"]["title"] for video in videos]
    topics = list(map(parseTitle, titles))

    pngPathFmt = lambda i: os.path.join(args.output, "%s.png" % i)

    with ThumbnailGenerator(args.template) as thumbGen:
        for i, (title, (number, topic)) in enumerate(zip(titles, topics)):
            print("Making thumbnail for number %s, topic %r" % (number, topic))
            thumbGen.makeThumbnail(number, topic, pngPathFmt(i))
        print("Done!")

    if not yesno("Upload generated thumbnails?"):
        return

    for i, video in enumerate(videos):
        print("Uploading thumbnail for %s" % video["snippet"]["title"])
        youtube.thumbnails().set(
            media_body=pngPathFmt(i),
            videoId=video["contentDetails"]["videoId"]
          ).execute()
    print("Done!")
main()
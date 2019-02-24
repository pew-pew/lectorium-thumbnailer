from thumbnail_generator import ThumbnailGenerator

import argparse
import json
import os


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("template", help=".psd template path")
    parser.add_argument("titles", help="path to json file with titles")
    parser.add_argument("output", help="output directory")
    args = parser.parse_args()

    with open(args.titles, "rt", encoding="utf-8") as file:
        videos = json.load(file)

    with ThumbnailGenerator(args.template) as thumbGen:
        logProgress = lambda i, msg: print("{:2}/{:2}: {}".format(i, len(videos), msg))
        for i, video in enumerate(videos):
            topic, number = video["topic"], video["number"]
            logProgress(i + 1, "number %s, topic %r" % (number, topic))
            path = os.path.join(args.output, "%s.png" % number)
            thumbGen.makeThumbnail(number, topic, path)
        print("Done!")

if __name__ == "__main__":
    main()
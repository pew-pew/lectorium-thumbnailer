from thumbnail_generator import ThumbnailGenerator

import argparse
import json
import os


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("templatesDir", help="directory with templates")
    args = parser.parse_args()

    templatesInfo = []
    for fname in os.listdir(args.templatesDir):
        if not fname.endswith(".psd"):
            continue

        print(fname)
        with ThumbnailGenerator(os.path.join(args.templatesDir, fname)) as thumb:
            subject = thumb.subjectLayer.TextItem.Contents
            lector = thumb.nameLayer.TextItem.Contents
            thumb.makeThumbnail(os.path.join(args.templatesDir, fname + ".png"))
            templatesInfo.append({
                "subject": subject,
                "lector": lector.strip(),
                "filename": fname,
            })


    with open(os.path.join(args.templatesDir, "info.json"), "w", encoding="utf-8") as file:
        json.dump(templatesInfo, file, ensure_ascii=False, indent=4, sort_keys=True)

if __name__ == "__main__":
    main()
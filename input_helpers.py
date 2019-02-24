from google_helpers import request_all


def tryPairseInt(s):
    try:
        return int(s)
    except ValueError:
        return None


def yesno(prompt):
    choice = None
    while choice not in ("yes", "no"):
        choice = input(prompt + " [yes|no]: ")
    return choice == "yes"


def inputChoice(prompt, choices):
    prettyChoicesPairs = [("[%s] %s" % (i, choice), choice) for i, choice in enumerate(sorted(choices))]
    prettyChoices = [prettyKey for prettyKey, choice in prettyChoicesPairs]
    prettyChoicesDict = dict(prettyChoicesPairs)

    print(prompt)
    print("Avaliable choices:", "", *prettyChoices, "", sep="\n")
    while True:
        userChoice = input("Type substring or index: ")
        maybeIndex = tryPairseInt(userChoice)
        if maybeIndex is not None and maybeIndex in range(len(prettyChoices)):
            return prettyChoicesPairs[maybeIndex][1]

        valid = [prettyChoice for prettyChoice, choice in prettyChoicesPairs
                              if userChoice.lower() in choice.lower()]
        if not valid:
            print("Match not found")
        elif len(valid) > 1:
            print("More than 1 match found:", "", *valid, "", sep="\n")
        else:
            return prettyChoicesDict[valid[0]]
        print("Try again")


def inputPlaylist(youtube, **requestParams):
    playlists = request_all(youtube.playlists().list, part="snippet", **requestParams)
    playlistsDict = {pl["snippet"]["title"]: pl for pl in playlists}

    playlistName = inputChoice("Select playlist", playlistsDict.keys())
    return playlistsDict[playlistName]
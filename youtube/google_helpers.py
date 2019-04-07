from googleapiclient.discovery import build
from google_auth_oauthlib.flow import Flow
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from apiclient.http import MediaFileUpload

import pickle
import os


clientIdPath = os.path.join(os.path.dirname(__file__), "client_id_secret.json")
tokenPath = os.path.join(os.path.dirname(__file__), "token.pickle")

def buildYoutube():
    # https://developers.google.com/drive/api/v3/quickstart/python
    creds = None

    if os.path.exists(tokenPath):
        with open(tokenPath, 'rb') as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                clientIdPath,
                scopes=["https://www.googleapis.com/auth/youtube"])
            creds = flow.run_local_server()

        with open(tokenPath, 'wb') as token:
            pickle.dump(creds, token)

    return build("youtube", "v3", credentials=creds)


def request_all(method, resultsPerPage=50, **kwargs):
    # Youtube api pagination implementation
    # https://developers.google.com/youtube/v3/guides/implementation/pagination
    nextPageToken = ''
    while True:
        response = method(**kwargs, **{'maxResults': resultsPerPage, 'pageToken':nextPageToken}).execute()
        yield from response['items']
        if 'nextPageToken' not in response:
            break
        nextPageToken = response['nextPageToken']
import pickle
import os.path
from os.path import join, dirname, abspath

from googleapiclient.discovery import build
from oauth2client.service_account import ServiceAccountCredentials

class Bot:
    GOOGLE_SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
    GOOGLE_CREDENTIALS_FILE = join(dirname(abspath(__file__)), "google-service-account.json")
    SPREADSHEET_ID = "1O1TvSiz3OahPaZQq_M4IMYukYHjFlEyj1fCyimoYIJo"

    def __init__(self):
        self.google_creds = None
        self.google_service = None
        self.sheet = None

    def authenticate_google(self):
        if not self.google_creds:
            self.google_creds = ServiceAccountCredentials.from_json_keyfile_name(
                self.GOOGLE_CREDENTIALS_FILE, self.GOOGLE_SCOPES)

        self.google_service = build('sheets', 'v4', credentials=self.google_creds)
        self.sheet = self.google_service.spreadsheets()

    def execute(self):
        result1 = self.sheet.values().get(spreadsheetId=self.SPREADSHEET_ID,
                                          range="'User Backpack'!A28:C28").execute()
        result1 = result1.get('values', [])
        print(type(result1), result1)

if __name__ == "__main__":
    b = Bot()
    print("Authenticating with Google...")
    b.authenticate_google()
    print("Fetching data from sheet...")
    b.execute()
    print("Done!")

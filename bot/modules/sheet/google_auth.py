import traceback

from googleapiclient.discovery import build
from oauth2client.service_account import ServiceAccountCredentials

from .settings import GOOGLE_SCOPES, GOOGLE_CREDENTIALS_FILE, SPREADSHEET_ID

class GoogleSheet:
    def __init__(self, sheet_api, sheet_id=SPREADSHEET_ID):
        """
        Should be constructed by means of GoogleAPI object

        sheet_api: Authenticated Google Sheets API object
        sheet_id: The spreadsheet to access. Default: settings.SPREADSHEET_ID
        """
        self.sheet_api = sheet_api
        self.sheet_id = sheet_id

    def fetch(self, cell):
        """
        Fetches a cell from the current spreadsheet.

        cell: The cell (or range of cells) to fetch. Must include the sheet
              name. An example format is "Sheet1!A1"
        """
        try:
            result = self.sheet_api.values().get(
                spreadsheetId=self.sheet_id,
                range=cell).execute()
            result = result.get('values', [])
            return result
        except:
            traceback.print_exc()
            return []

class GoogleAPI:
    def __init__(self, scopes=GOOGLE_SCOPES, cred_file=GOOGLE_CREDENTIALS_FILE):
        """
        Construct an authenticated Google API session using a service account
        credential file.

        scopes: The Google API scopes to request
        cred_file: The path to the json file containing credentials
        """
        self.scopes = scopes
        self.cred_file = cred_file

        self.google_creds = None
        self.sheet_api = None

    def authenticate(self):
        if self.google_creds is None:
            self.google_creds = ServiceAccountCredentials.from_json_keyfile_name(
                self.cred_file, self.scopes)


    def make_sheet(self, sheet_id=SPREADSHEET_ID):
        if self.sheet_api is None:
            self.authenticate()
            service = build('sheets', 'v4', credentials=self.google_creds)
            self.sheet_api = service.spreadsheets()

        return GoogleSheet(self.sheet_api, sheet_id)

if __name__ == "__main__":
    b = GoogleAPI()
    print("Authenticating with Google...")
    b.authenticate()
    print("Fetching data from sheet...")
    s = b.make_sheet()
    print(s.fetch("User Directory!C3:D27"))
    print("Done!")

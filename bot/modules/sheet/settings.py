from os.path import join, dirname, abspath

GOOGLE_SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
GOOGLE_CREDENTIALS_FILE = join(dirname(abspath(__file__)), "google-service-account.json")
SPREADSHEET_ID = "1O1TvSiz3OahPaZQq_M4IMYukYHjFlEyj1fCyimoYIJo"

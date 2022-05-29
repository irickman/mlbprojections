import pygsheets
import os
from google.oauth2 import service_account


cred_file=os.environ.get("GOOGLE_GHA_CREDS_PATH")

credentials = service_account.Credentials.from_service_account_file(
        cred_file, scopes=SCOPES)
gc = pygsheets.authorize(custom_credentials =credentials) 

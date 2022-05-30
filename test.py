import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# SERVICE_ACCOUNT_FILE=os.environ.get("GOOGLE_GHA_CREDS_PATH")
# SCOPES = ('https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive')
# creds = service_account.Credentials.from_service_account_file(
#         SERVICE_ACCOUNT_FILE, scopes=SCOPES)

service = build('sheets', 'v4')#, credentials=creds)


spreadsheet_id='18t44o27sqy_FVyZF5wrbqi4qV1AJq5yP3rbQpuJY0aQ'   
range_name='Sheet1A1'  
result = service.spreadsheets().values().get(
    spreadsheetId=spreadsheet_id, range=range_name).execute()
rows = result.get('values', [])
print('{0} rows retrieved.'.format(len(rows)))       
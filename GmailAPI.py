import os.path
import os
import pickle



# for encoding/decoding messages in base64
from base64 import urlsafe_b64decode, urlsafe_b64encode
# for dealing with attachement MIME types
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
from mimetypes import guess_type as guess_mime_type

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]



def start_service():
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    try:
    # Call the Gmail API
        service = build("gmail", "v1", credentials=creds)
        results = service.users().labels().list(userId="me").execute()
        labels = results.get("labels", [])

        if not labels:
            print("No labels found.")

        # print("Labels:")
        for label in labels:
        #   print(label["name"])
            pass
        return service

    except HttpError as error:
    # TODO(developer) - Handle errors from gmail API.
        print(f"An error occurred: {error}")


def search_messages(service, query):
    result = service.users().messages().list(userId='me',q=query).execute()
    messages = [ ]
    if 'messages' in result:
        messages.extend(result['messages'])
    while 'nextPageToken' in result:
        page_token = result['nextPageToken']
        result = service.users().messages().list(userId='me',q=query, pageToken=page_token).execute()
        if 'messages' in result:
            messages.extend(result['messages'])
    return messages

def parse_parts(service, parts, folder_name, result_list):
    """
    Utility function that parses the content of an email partition
    """
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
    if parts:
        for part in parts:
            filename = part.get("filename")
            mimeType = part.get("mimeType")
            body = part.get("body")
            data = body.get("data")
            file_size = body.get("size")
            part_headers = part.get("headers")

            binary_data = urlsafe_b64decode(data)
            if part.get("parts"):
                # recursively call this function when we see that a part
                # has parts inside
                parse_parts(service, part.get("parts"), folder_name, result_list)
            if mimeType == "text/plain":
                # if the email part is text plain
                if data:
                    text = binary_data.decode()
                    print(text)
            elif mimeType == "text/html":
                # if the email part is an HTML content
                # save the HTML file and optionally open it in the browser
                if not filename:
                    filename = "index.html"
                filepath = os.path.join(folder_name, filename)
                print("Saving HTML to", filepath)
                with open(filepath, "wb") as f:
                    f.write(binary_data)
                # print(binary_data.decode())
                result_list.append(binary_data.decode())

        





if __name__ == "__main__":
    service = start_service()
    search_query = 'from:ebay@ebay.com subject:"Da, your order is confirmed"'
    # Call the Gmail API to search for messages
    messages = service.users().messages().list(userId='me', q=search_query).execute()
    html_list = []



    # Check if any messages match the search criteria
    if 'messages' in messages:
        for message in messages['messages']:
            # Get the message details
            msg_id = message['id']
            msg = service.users().messages().get(userId='me', id=msg_id).execute()
            parse_parts(service, msg['payload']['parts'], 'ReceiptFolder', html_list)

            # Print the snippet (preview) of the message
            # print('Message snippet:', msg['snippet'])
            # print(msg['payload'].keys())
            # parts = msg['payload']['parts']
            # print(parts[0].keys())
            # print((parts[0]['body']))
            # Print the full message (optional)
            # print('Full message:', msg)
    else:
        print('No messages found matching the search criteria.')
    print(len(html_list))

import os.path
import os
from bs4 import BeautifulSoup

# for encoding/decoding messages in base64
from base64 import urlsafe_b64decode

# for dealing with attachement MIME types
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
FOLDER_NAME = 'ReceiptFolder'



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
        return service

    except HttpError as error:
    # TODO(developer) - Handle errors from gmail API.
        print(f"An error occurred: {error}")


def parse_parts(parts, file_count, folder_name=FOLDER_NAME):
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

            binary_data = urlsafe_b64decode(data)
            if part.get("parts"):
                # recursively call this function when we see that a part
                # has parts inside
                file_count[0] += 1
                parse_parts(part.get("parts"), folder_name, file_count)
            if mimeType == "text/html":
                # if the email part is an HTML content
                # save the HTML file and optionally open it in the browser
                if not filename:
                    file_count[0] += 1
                    filename = "index"+str(file_count[0])+".html"
                filepath = os.path.join(folder_name, filename)
                print("Saving HTML to", filepath)
                with open(filepath, "wb") as f:
                    f.write(binary_data)
                # print(binary_data.decode())
                return binary_data.decode()

        
def get_ebay_results(service, msg_id, file_count):
    msg = service.users().messages().get(userId='me', id=msg_id).execute()
    html_content = parse_parts(msg['payload']['parts'], file_count, 'ReceiptFolder')
    headers = msg['payload']['headers']
    for header in headers:
        if header['name'].lower() == 'date':
            date = header['value']
        if header['name'].lower() == 'from':
            sender = header['value']
    
    sender = sender.split(' ')[0]
        
    soup = BeautifulSoup(html_content, 'html.parser')
    name_tag = soup.find('a', class_='title')
    name = name_tag.string
    price_tag = soup.find('p', class_='labelValueValue').find('b')
    price = price_tag.string

    return sender, date, name, price
    
def get_walmart_results(service, msg_id, file_count, folder_name = FOLDER_NAME):
    msg = service.users().messages().get(userId='me', id=msg_id).execute()
    binary_data = urlsafe_b64decode(msg['payload']['body']['data'])
    file_count[0] += 1
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
    filename = "index"+str(file_count[0])+".html"
    filepath = os.path.join(folder_name, filename)
    print("Saving HTML to", filepath)
    with open(filepath, "wb") as f:
        f.write(binary_data)
    headers = msg['payload']['headers']
    for header in headers:
        if header['name'].lower() == 'date':
            date = header['value']
        if header['name'].lower() == 'from':
            sender = header['value']
    sender = sender.split('"')[1].split('.')[0]


    return sender, date

def get_amazon_results(service, msg_id, file_count, folder_name = FOLDER_NAME):
    msg = service.users().messages().get(userId='me', id=msg_id).execute()
    html_content = parse_parts(msg['payload']['parts'], file_count, folder_name)
    headers = msg['payload']['headers']
    for header in headers:
        if header['name'].lower() == 'date':
            date = header['value']
        if header['name'].lower() == 'from':
            sender = header['value']
    sender = sender.split('"')[1].split('.')[0]
    return sender, date
    


if __name__ == "__main__":
    service = start_service()

    # Below are some example query, please modify this when running the code
    ebay_search_query = 'from:ebay@ebay.com subject:"Da, your order is confirmed"'
    walmart_search_query = 'from:help@walmart.com subject:"Da, thanks for your order"'
    amazon_search_query = 'from:auto-confirm@amazon.com'

    query = walmart_search_query

    # Call the Gmail API to search for messages
    messages = service.users().messages().list(userId='me', q=query).execute()

    # Check if any messages match the search criteria
    file_count = [0]
    if 'messages' in messages:
        for message in messages['messages']:
            # Get the message details
            msg_id = message['id']
            
            # For eBay
            if query == ebay_search_query:
                sender, date, name, price = get_ebay_results(service, msg_id, file_count)
                print('Merchant Name: ', sender)
                print('Date: ', date)
                print('Item Name: ', name)
                print("Price: ", price)

            # For Walmart
            if query == walmart_search_query:
                sender, date = get_walmart_results(service, msg_id, file_count)
                print('Merchant Name: ', sender)
                print('Date: ', date)

            # For amazon
            if query == amazon_search_query:
                sender, date = get_amazon_results(service, msg_id, file_count)
                print('Merchant Name: ', sender)
                print('Date: ', date)
            
            # Avoid having too many queries
            if file_count[0] >= 10:
                break


    else:
        print('No messages found matching the search criteria.')



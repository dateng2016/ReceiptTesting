import imaplib
import email
from email.header import decode_header
from bs4 import BeautifulSoup


# IMAP server settings for Gmail
APP_PASSWORD = 'hksx zxjb wztw ncvp'

IMAP_SERVER = 'imap.gmail.com'
USERNAME = 'dateng2016@gmail.com'
PASSWORD = APP_PASSWORD

# Connect to the IMAP server
mail = imaplib.IMAP4_SSL(IMAP_SERVER)
mail.login(USERNAME, PASSWORD)

# Select the mailbox (e.g., 'INBOX')
mail.select('INBOX')

subject_content = "Da, your order is confirmed"
# Search for emails based on specific criteria (e.g., subject, sender, date)
search_criteria = f'(SUBJECT "{subject_content}")'
result, data = mail.search(None, search_criteria)

# Get the email IDs
email_ids = data[0].split()

# Retrieve the most recent email (assuming the search returns emails sorted by date)
latest_email_id = email_ids[-1]

# Fetch the email data (headers and body)
result, email_data = mail.fetch(latest_email_id, '(RFC822)')
raw_email = email_data[0][1]

# Parse the raw email data
msg = email.message_from_bytes(raw_email)

# Extract email information (e.g., sender, subject)
sender = msg['From']
subject = decode_header(msg['Subject'])[0][0]

# Print email information
print("Sender:", sender)
print("Subject:", subject)

# You can access email body and attachments similarly
# body = msg.get_payload()

# Function to get the email body
def get_email_body(msg):
    if msg.is_multipart():
        # If the message is multipart, iterate over each part
        for part in msg.walk():
            content_type = part.get_content_type()
            if content_type == "text/plain" or content_type == "text/html":
                # If the part is plain text or HTML, return its payload
                return part.get_payload(decode=True).decode()
    else:
        # If the message is not multipart, return its payload
        return msg.get_payload(decode=True).decode()

# Example usage:
email_body = get_email_body(msg)
# print("Email Body:", email_body)


# Close the connection
mail.close()
mail.logout()

soup = BeautifulSoup(email_body, 'html.parser')

name_tag = soup.find('a', class_='title')
price_tags = soup.find_all('td', class_="item")

print(f'Merchant name: {sender.split(" ")[0]}')
print()
print('Item: ', name_tag.string)
print('Price: ',price_tags[-1].string)
print('Date: ', msg['Date'])
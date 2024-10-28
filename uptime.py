"""Emails a list of unresponsive sites.
The list is a recent snapshot obtained from UptimeRobot API.
Please keep this script compatible with python 3.5.
"""

import smtplib
import urllib.request
import urllib.parse
import json
import datetime
import logging
import sys
from email.message import EmailMessage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from env.uptime import EMAIL_SERVER, EMAIL_TO, EMAIL_FROM, UPTIME_API_KEY


UPTIME_API_URL = 'https://api.uptimerobot.com/v2/getMonitors'
UPTIME_REQUEST_PARAMS = urllib.parse.urlencode({
  'api_key': UPTIME_API_KEY, 
  'format': 'json', 
  'logs': 1,
  'statuses': '8-9',
  'logs_limit': 5, 
})


class Logger:
    def __init__(self):
        self.logger = logging.getLogger('uptime.py')
        self.logger.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        stdout_handler = logging.StreamHandler(sys.stdout)
        stdout_handler.setLevel(logging.INFO)
        stdout_handler.setFormatter(formatter)
        self.logger.addHandler(stdout_handler)

    def log(self, message):
        self.logger.info(message)

class Emailer:
    def __init__(self):
        pass

    def send(self, title, message_plain):
        msg = EmailMessage()

        #msg.set_content(message)

        msg = MIMEMultipart('alternative')
        html = """
        <html>
        <head></head>
        <body>
            <pre>{}</pre>
        </body>
        </html>
        """.format(message_plain)

        part1 = MIMEText(message_plain, 'plain')
        part2 = MIMEText(html, 'html')
        msg.attach(part1)
        msg.attach(part2)

        msg['Subject'] = title
        msg['From'] = EMAIL_FROM
        msg['To'] = ', '.join(EMAIL_TO)

        # Send the message via our own SMTP server.
        s = smtplib.SMTP(EMAIL_SERVER)
        s.sendmail(msg['From'], EMAIL_TO, msg.as_string())
        s.quit()

LOGGER = Logger()

def fetch_sites_list_and_email():

    LOGGER.log('start =========================')

    title = ''
    message = ''
    monitors = []

    # fetch the list from the API
    with urllib.request.urlopen(UPTIME_API_URL, UPTIME_REQUEST_PARAMS.encode('ascii')) as f:
        res = f.read().decode('utf-8')

    res = json.loads(res)

    if res['stat'] != 'ok':
        title = 'Uptime robot returned error'
    else:
        monitors = res['monitors']

    title = '{} site(s) down'.format(len(monitors))

    # compose the email message
    if monitors:
        for monitor in monitors:
            log = monitor['logs'][0]
            duration = log['duration']
            reason = log['reason']['detail']
            duration_friendly = datetime.timedelta(seconds=duration)
            message += '{}, downtime: {} ({})\n\n'.format(monitor['url'], duration_friendly, reason)

    if title: 
        LOGGER.log(title)
        if message:
            EMAILER = Emailer()
            EMAILER.send(title, message)
    else:
        LOGGER.log('ERROR: code 1. title is empty.')
    
    LOGGER.log('done ==========================')


fetch_sites_list_and_email()

from getpass import getpass
from typing import Any, Dict, List
import os

from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib

class EmailHandler:
    def __init__(self, config: Dict[str, Any]):
        self.hostname = config['hostname']
        self.port = config['port']
        self.username = config['username']
        self.__password = config.get('app_password')

    def load_password(self) -> None:
        if self.__password is None:
            self.__password = getpass('Email password: ')

    def send_email(
            self,
            email_to: str,
            subject: str,
            content: str,
            attachments: List[str] = None) -> None:

        msg_root = MIMEMultipart('related')
        msg_root['Subject'] = subject
        msg_root['From'] = self.username
        msg_root['To'] = email_to

        alternative = MIMEMultipart('alternative')
        msg_root.attach(alternative)

        msg_alternative = ''
        msg_text = MIMEText(msg_alternative)
        alternative.attach(msg_text)

        msg_text = MIMEText(content, 'html')
        alternative.attach(msg_text)

        if attachments is not None:
            for filename in attachments:
                with open(filename, 'rb') as attachment:
                    email_attachment = MIMEApplication(attachment.read())
                    email_attachment.add_header("Content-Disposition", "attachment", filename=os.path.basename(filename))

                    msg_root.attach(email_attachment)

        smtp = smtplib.SMTP_SSL(host=self.hostname, port=self.port)
        smtp.login(self.username, self.__password)
        smtp.sendmail(self.username, email_to, msg_root.as_string())
        smtp.quit()

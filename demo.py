import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

sender_email = "info@vibhoospropcare.com"
receiver_email = "kaushikpalvai2004@gmail.com"
password = "Propcare2025@"

# Create the email
msg = MIMEMultipart("alternative")
msg["Subject"] = "Test Email"
msg["From"] = sender_email
msg["To"] = receiver_email

text = "Hi, this is a test email from vibhoospropcare.com!"
msg.attach(MIMEText(text, "plain"))

# Send via GoDaddy SMTP
context = ssl.create_default_context()
with smtplib.SMTP_SSL("smtpout.secureserver.net", 465, context=context) as server:
    server.login(sender_email, password)
    server.sendmail(sender_email, receiver_email, msg.as_string())

print("✅ Email sent successfully")

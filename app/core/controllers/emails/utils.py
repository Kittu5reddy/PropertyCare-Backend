from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
import secrets
from dotenv import load_dotenv
from config import settings


# GoDaddy SMTP settings
SMTP_SERVER = "smtpout.secureserver.net"
SMTP_PORT = 465  # SSL port
EMAIL_ADDRESS = settings.EMAIL_ADDRESS
EMAIL_PASSWORD = settings.EMAIL_PASSWORD
PATH = settings.EMAIL_TOKEN_VERIFICATION


def send_consultation_email(name: str, email: str, preferred_date=None, preferred_time=None, subject=None):
    """Send a professional consultation confirmation email to the user."""
    formatted_date = preferred_date.strftime("%d %b, %Y") if preferred_date else ""
    formatted_time = preferred_time.strftime("%I:%M %p") if preferred_time else ""
    consultation_subject = subject if subject else "General Consultation"

    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Consultation Confirmation - Vibhoos PropCare</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                background: #f7f9fc;
                margin: 0;
                padding: 20px;
                color: #333;
            }}
            .container {{
                max-width: 700px;
                margin: auto;
                background: #fff;
                padding: 30px 40px;
                border-radius: 12px;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
            }}
            .header {{
                text-align: center;
                margin-bottom: 25px;
            }}
            .header img {{
                max-height: 80px;
                width: auto;
                margin-bottom: 10px;
            }}
            h1 {{
                color: #0C4A6E;
                font-size: 22px;
                margin-bottom: 10px;
            }}
            p {{
                font-size: 14px;
                margin: 5px 0;
            }}
            .section {{
                margin-bottom: 25px;
            }}
            .schedule {{
                background: #f0f9ff;
                padding: 20px;
                border-left: 4px solid #0C4A6E;
                border-radius: 8px;
            }}
            .contact {{
                background: #ecfdf5;
                padding: 20px;
                border-left: 4px solid #10b981;
                border-radius: 8px;
            }}
            .footer {{
                text-align: center;
                font-size: 12px;
                color: #555;
                border-top: 1px solid #ccc;
                padding-top: 15px;
                margin-top: 30px;
            }}
            a {{
                color: #0C4A6E;
                text-decoration: none;
            }}
            strong {{
                color: #374151;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <!-- Header with logo -->
            <div class="header">
                <a href="https://www.vibhoospropcare.com">
                    <img src="https://www.vibhoospropcare.com/logo.png" alt="Vibhoos PropCare Logo"/>
                </a>
                <h1>Consultation Request Received!</h1>
                <p>Thank you for reaching out to Vibhoos PropCare</p>
            </div>

            <!-- Greeting -->
            <div class="section">
                <p>Dear <strong>{name}</strong>,</p>
                <p>We have received your consultation request regarding <strong>{consultation_subject}</strong>. Our team is excited to assist you with your property needs.</p>
            </div>

            <!-- Schedule -->
            <div class="section schedule">
                <h2>Your Preferred Schedule</h2>
                <p><strong>Date:</strong> {formatted_date}</p>
                <p><strong>Time:</strong> {formatted_time}</p>
            </div>

            <!-- Contact & Next Steps -->
            <div class="section contact">
                <h2>What Happens Next?</h2>
                <p>Our property expert will contact you within <strong>24 hours</strong> to confirm your consultation and discuss your requirements in detail.</p>
                <p><strong>Email:</strong> <a href="mailto:support@vibhoospropcare.com">support@vibhoospropcare.com</a></p>
                <p><strong>Phone:</strong> <a href="tel:+919000898990">+91 90008 98990</a></p>
                <p><strong>Website:</strong> <a href="https://www.vibhoospropcare.com">www.vibhoospropcare.com</a></p>
                <p><strong>Office Hours:</strong> Mon-Fri: 9:00 AM - 6:00 PM, Sat: 10:00 AM - 4:00 PM</p>
            </div>

            <!-- Closing -->
            <div class="section">
                <p>We look forward to helping you with your property journey!</p>
                <p><strong>Team Vibhoos PropCare</strong></p>
            </div>

            <!-- Footer -->
            <div class="footer">
                <p>If you did not request this consultation, please ignore this email or contact support.</p>
            </div>
        </div>
    </body>
    </html>
    """

    try:
        msg = MIMEMultipart()
        msg['From'] = f"Vibhoos PropCare <{EMAIL_ADDRESS}>"
        msg['To'] = email
        msg['Subject'] = "Your Consultation Request - Vibhoos PropCare"

        msg.attach(MIMEText(html_content, 'html'))

        server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT)
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.sendmail(EMAIL_ADDRESS, email, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print(f"Failed to send consultation email: {e}")
        return False

    
def send_newsletter_email(to_email: str, unsubscribe_url: str):
    """Send the welcome newsletter email."""
    html_content = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2 style="color: #0C4A6E;">Welcome to Vibhoos PropCare Newsletter!</h2>
        <p>Thank you for subscribing to our newsletter!</p>
        <p>You'll now receive the latest updates about:</p>
        <ul style="margin: 20px 0; padding-left: 20px;">
            <li>Latest property listings and market trends</li>
            <li>Investment opportunities and tips</li>
            <li>Property management insights</li>
            <li>Exclusive offers and promotions</li>
            <li>Industry news and updates</li>
        </ul>
        <div style="margin: 30px 0; padding: 20px; border-left: 4px solid #0C4A6E; background-color: #f1f5f9;">
            <p style="margin: 0;"><strong>Contact Information:</strong></p>
            <p style="margin: 5px 0;">Email: support@mypropertyguru.co</p>
            <p style="margin: 5px 0;">Phone: +91 90008 98990</p>
        </div>
        <p>We're excited to have you as part of our community!</p>
        <p style="color: #6b7280; font-size: 14px;">
            Best regards,<br>
            Vibhoos PropCare Team
        </p>
        <hr style="margin: 30px 0; border: none; border-top: 1px solid #e5e7eb;">
        <p style="color: #6b7280; font-size: 12px; text-align: center;">
            If you no longer wish to receive these emails, you can 
            <a href="{unsubscribe_url}" style="color: #0C4A6E;">unsubscribe here</a>.
        </p>
    </div>
    """
    try:
        msg = MIMEMultipart()
        msg['From'] = f"VPC NEWS LETTER <{EMAIL_ADDRESS}>"
        msg['To'] = to_email
        msg['Subject'] = "Welcome to Vibhoos PropCare Newsletter"
        msg['List-Unsubscribe'] = f'<https://api.vibhoospropcare.com/email/unsubscribe-news-letters/{to_email}>'
        msg['List-Unsubscribe-Post'] = 'List-Unsubscribe=One-Click'
        msg.attach(MIMEText(html_content, 'html'))

        server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT)
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.sendmail(EMAIL_ADDRESS, to_email, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print(f"Failed to send newsletter email: {e}")
        return 
    

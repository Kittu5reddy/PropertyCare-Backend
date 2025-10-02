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



def send_consultation_email(name: str, email: str, preferred_date=None, preferred_time=None):
    """Send consultation confirmation email to the user."""
    formatted_date = preferred_date.strftime("%d %b, %Y") if preferred_date else ""
    time = preferred_time.strftime("%I:%M %p") if preferred_time else ""

    html_content = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; background-color: #f9fafb; padding: 20px;">
    <div style="background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
        <div style="text-align: center; margin-bottom: 30px;">
            <h2 style="color: #0C4A6E; margin-bottom: 10px;">Thank You for Your Interest!</h2>
            <p style="color: #6b7280; font-size: 16px; margin: 0;">We've received your consultation request</p>
        </div>
        <p style="font-size: 16px; color: #374151; margin-bottom: 20px;">
            Dear <strong>{name}</strong>,
        </p>
        <p style="color: #6b7280; line-height: 1.6; margin-bottom: 25px;">
            Thank you for reaching out to Vibhoos PropCare! We're excited to help you with your property needs.
        </p>
        <div style="background-color: #f0f9ff; padding: 25px; border-radius: 8px; margin: 25px 0; border-left: 4px solid #0C4A6E;">
            <h3 style="margin-top: 0; color: #0C4A6E; margin-bottom: 15px;">Your Preferred Schedule</h3>
            <div style="margin-bottom: 10px;">
                <span style="font-weight: bold; color: #374151; margin-right: 10px;">Date:</span>
                <span style="color: #059669; font-weight: bold;">{formatted_date}</span>
            </div>
            <div>
                <span style="font-weight: bold; color: #374151; margin-right: 10px;">Time:</span>
                <span style="color: #059669; font-weight: bold;">{time}</span>
            </div>
        </div>
        <div style="background-color: #ecfdf5; padding: 20px; border-radius: 8px; margin: 25px 0; border-left: 4px solid #10b981;">
            <h4 style="margin-top: 0; color: #065f46; margin-bottom: 10px;">What happens next?</h4>
            <p style="color: #047857; margin: 0; line-height: 1.6;">
                Our property expert will contact you within <strong>24 hours</strong> to confirm your consultation and discuss your requirements in detail.
            </p>
        </div>
        <div style="background-color: #f8fafc; padding: 20px; border-radius: 8px; margin: 25px 0; border: 1px solid #e5e7eb;">
            <h4 style="margin-top: 0; color: #0C4A6E; margin-bottom: 15px;">Need to reach us sooner?</h4>
            <div style="margin-bottom: 8px;">
                <strong style="color: #374151;">Email:</strong> 
                <a href="mailto:support@mypropertyguru.co" style="color: #0C4A6E; text-decoration: none;">support@mypropertyguru.co</a>
            </div>
            <div style="margin-bottom: 8px;">
                <strong style="color: #374151;">Phone:</strong> 
                <a href="tel:+919000898990" style="color: #0C4A6E; text-decoration: none;">+91 90008 98990</a>
            </div>
            <div>
                <strong style="color: #374151;">Office Hours:</strong> 
                <span style="color: #6b7280;">Mon-Fri: 9:00 AM - 6:00 PM, Sat: 10:00 AM - 4:00 PM</span>
            </div>
        </div>
        <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #e5e7eb;">
            <p style="color: #6b7280; font-size: 14px; margin-bottom: 5px;">
                Looking forward to helping you with your property journey!
            </p>
            <p style="color: #0C4A6E; font-weight: bold; margin: 0;">Team Vibhoos PropCare</p>
        </div>
    </div>
    </div>
    """

    try:
        msg = MIMEMultipart()
        msg['From'] =  f"VPC Consultation Request <{EMAIL_ADDRESS}>"
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
        return 
    
    
    
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
        msg.attach(MIMEText(html_content, 'html'))

        server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT)
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.sendmail(EMAIL_ADDRESS, to_email, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print(f"Failed to send newsletter email: {e}")
        return 
    

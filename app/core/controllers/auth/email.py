from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
import secrets
from config import settings
from datetime import datetime

# GoDaddy SMTP settings
SMTP_SERVER = "smtpout.secureserver.net"
SMTP_PORT = 465  # SSL port
EMAIL_ADDRESS = settings.EMAIL_ADDRESS
EMAIL_PASSWORD = settings.EMAIL_PASSWORD
PATH = settings.EMAIL_TOKEN_VERIFICATION


def create_verification_token():
    return secrets.token_urlsafe(32)


def send_verification_email(email: str, token: str):
    """Send verification email to user"""
    try:
        msg = MIMEMultipart()
        msg['From'] =  f"VPC <{EMAIL_ADDRESS}>"
        msg['To'] = email
        msg['Subject'] = "Verify Your Email Address"

        verification_link = f"{PATH}/auth/verify-email?token={token}"
        import datetime
        current_year=datetime.datetime.now().year
        body = f"""
        <!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <meta http-equiv="X-UA-Compatible" content="IE=edge" />
    <meta name="format-detection" content="telephone=no" />
    <title>Email Verification</title>
  </head>
  <body
    style="
      margin: 0;
      padding: 0;
      background-color: #f3f4f6;
      font-family: Arial, Helvetica, sans-serif;
      -webkit-text-size-adjust: 100%;
      -ms-text-size-adjust: 100%;
    "
  >
    <!-- Email Container -->
    <table
      role="presentation"
      cellpadding="0"
      cellspacing="0"
      border="0"
      width="100%"
      style="background-color: #f3f4f6"
    >
      <tr>
        <td align="center" style="padding: 20px 10px">
          <!-- Main Email Content -->
          <table
            role="presentation"
            cellpadding="0"
            cellspacing="0"
            border="0"
            width="100%"
            style="
              max-width: 600px;
              background-color: #ffffff;
              border-radius: 8px;
              overflow: hidden;
            "
          >
            <!-- Header with Logo -->
            <tr>
              <td
                style="
                  background-color: #f9fafb;
                  padding: 30px 40px 20px;
                  text-align: center;
                  border-bottom: 1px solid #e5e7eb;
                "
              >
                <img
                  src="https://www.vibhoospropcare.com/logo.png"
                  alt="PropertyCare Logo"
                  width="120"
                  height="auto"
                  style="
                    display: block;
                    margin: 0 auto;
                    max-width: 120px;
                    height: auto;
                  "
                />
              </td>
            </tr>

            <!-- Email Body -->
            <tr>
              <td style="padding: 40px; background-color: #f9fafb">
                <!-- Greeting -->
                <table
                  role="presentation"
                  cellpadding="0"
                  cellspacing="0"
                  border="0"
                  width="100%"
                >
                  <tr>
                    <td
                      style="
                        color: #374151;
                        font-size: 18px;
                        font-weight: bold;
                        line-height: 26px;
                        padding-bottom: 20px;
                      "
                    >
                      Welcome to Vibhoos PropertyCare! Please verify your email address
                    </td>
                  </tr>
                  <tr>
                    <td
                      style="
                        color: #374151;
                        font-size: 16px;
                        line-height: 24px;
                        padding-bottom: 20px;
                      "
                    >
                      Thank you for signing up. Please click the button below to
                      verify your email address:
                    </td>
                  </tr>
                </table>

                <!-- Verification Button -->
                <table
                  role="presentation"
                  cellpadding="0"
                  cellspacing="0"
                  border="0"
                  width="100%"
                >
                  <tr>
                    <td align="center" style="padding: 20px 0">
                      <a
                        href="{verification_link}"
                        style="
                          background-color: #4caf50;
                          color: #ffffff;
                          padding: 12px 28px;
                          font-size: 16px;
                          font-weight: bold;
                          text-decoration: none;
                          border-radius: 6px;
                          display: inline-block;
                        "
                      >
                        Verify Email
                      </a>
                    </td>
                  </tr>
                </table>

                <!-- Alternative Link -->
                <table
                  role="presentation"
                  cellpadding="0"
                  cellspacing="0"
                  border="0"
                  width="100%"
                >
                  <tr>
                    <td
                      style="
                        color: #374151;
                        font-size: 16px;
                        line-height: 24px;
                        padding: 10px 0;
                      "
                    >
                      Or copy and paste this link into your browser:
                    </td>
                  </tr>
                  <tr>
                    <td
                      style="
                        color: #2563eb;
                        font-size: 14px;
                        line-height: 22px;
                        word-break: break-all;
                      "
                    >
                      {verification_link}
                    </td>
                  </tr>
                  <tr>
                    <td
                      style="
                        color: #374151;
                        font-size: 16px;
                        line-height: 24px;
                        padding: 20px 0;
                      "
                    >
                      This link will expire in <strong>60 minutes</strong>.
                    </td>
                  </tr>
                </table>

                <!-- About Section -->
                <table
                  role="presentation"
                  cellpadding="0"
                  cellspacing="0"
                  border="0"
                  width="100%"
                >
                  <tr>
                    <td
                      style="
                        border-top: 1px solid #e5e7eb;
                        padding-top: 20px;
                        padding-bottom: 10px;
                      "
                    >
                      <span
                        style="
                          color: #111827;
                          font-size: 18px;
                          font-weight: bold;
                        "
                        >About Vibhoos Propcare</span
                      >
                    </td>
                  </tr>
                  <tr>
                    <td
                      style="
                        color: #374151;
                        font-size: 15px;
                        line-height: 24px;
                        padding-bottom: 20px;
                      "
                    >
                      <strong>PropertyCare</strong> is your trusted partner in
                      seamless property management. Whether you’re an owner,
                      tenant, or agent, our platform helps you track
                      maintenance, handle tenant requests, and keep everything
                      organized—all in one place.
                    </td>
                  </tr>
                  <tr>
                    <td
                      style="color: #374151; font-size: 15px; line-height: 24px"
                    >
                      If you didn’t create an account, please ignore this email.
                    </td>
                  </tr>
                </table>
              </td>
            </tr>

            <!-- Footer -->
            <tr>
              <td
                style="
                  background-color: #ffffff;
                  padding: 30px 40px;
                  border-top: 1px solid #e5e7eb;
                "
              >
                <table
                  role="presentation"
                  cellpadding="0"
                  cellspacing="0"
                  border="0"
                  width="100%"
                >
                  <tr>
                    <td
                      style="
                        color: #6b7280;
                        font-size: 12px;
                        line-height: 18px;
                        text-align: center;
                        padding-bottom: 10px;
                      "
                    >
                      This is an automated message, please do not reply to this
                      email.
                    </td>
                  </tr>
                  <tr>
                    <td
                      style="
                        color: #6b7280;
                        font-size: 12px;
                        line-height: 18px;
                        text-align: center;
                      "
                    >
                      © {current_year} PropertyCare Private Limited. All rights
                      reserved.<br />
                      <em>Seamless Property Management, Always.</em>
                    </td>
                  </tr>
                </table>
              </td>
            </tr>
          </table>
        </td>
      </tr>
    </table>
  </body>
</html>

        """

        msg.attach(MIMEText(body, 'html'))

        # GoDaddy requires SSL on port 465
        server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT)
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.sendmail(EMAIL_ADDRESS, email, msg.as_string())
        server.quit()

        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False


def send_admin_login_alert_email(email: str, ip_address: str = None, user_agent: str = None):
    """Send an alert email to admin when a login occurs."""
    from datetime import datetime
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = email
        msg['Subject'] = "Admin Login Notification"

        # Compose dynamic info
        time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ip_info = f"<p><b>IP Address:</b> {ip_address}</p>" if ip_address else ""
        ua_info = f"<p><b>Device/Browser:</b> {user_agent}</p>" if user_agent else ""

        body = f"""
        <html>
            <body style="font-family: Arial, sans-serif; color: #333;">
                <h2>Admin Login Alert</h2>
                <p>
                    Your admin account was just logged into on <b>{time_str}</b>.
                </p>
                {ip_info}
                {ua_info}
                <p>If this was you, no action is needed.</p>
                <p><span style="color:red"><b>If this was not you</b></span>, please reset your password immediately and review your account security.</p>
                <hr>
                <p>This is an automated alert for your security.</p>
            </body>
        </html>
        """

        msg.attach(MIMEText(body, 'html'))

        # GoDaddy requires SSL on port 465
        server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT)
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.sendmail(EMAIL_ADDRESS, email, msg.as_string())
        server.quit()

        return True
    except Exception as e:
        print(f"Failed to send admin login alert email: {e}")
        return False



async def send_forgot_password_email(email: str, reset_link: str,context:dict=None):
    """Send forgot password email with Vibhoos PropCare theme."""
    from datetime import datetime
    subject = "Reset Your Vibhoos PropCare Password"
    current_year = datetime.now().year

    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
      <head>
        <meta charset="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <title>Password Reset</title>
      </head>
      <body style="margin:0;padding:0;background-color:#f3f4f6;font-family:Arial,Helvetica,sans-serif;">
        <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="background-color:#f3f4f6">
          <tr>
            <td align="center" style="padding:20px 10px">
              <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" 
                style="max-width:600px;background-color:#ffffff;border-radius:8px;overflow:hidden;">
                
                <!-- Header -->
                <tr>
                  <td style="background-color:#135965;padding:30px 40px 20px;text-align:center;border-bottom:1px solid #e5e7eb;">
                    <img src="https://uploadthingy.s3.us-west-1.amazonaws.com/uCmrv4YNGkminyPEBDKiSe/WhatsApp_Image_2025-09-26_at_19.07.02_626da1d9.jpg"
                         alt="Vibhoos PropCare Logo" width="120" 
                         style="display:block;margin:0 auto;max-width:120px;height:auto;border-radius:4px;">
                  </td>
                </tr>

                <!-- Body -->
                <tr>
                  <td style="padding:40px;background-color:#f9fafb;">
                    <h2 style="color:#135965;font-size:22px;margin-bottom:10px;">Reset Your Password</h2>
                    <p style="color:#374151;font-size:16px;line-height:24px;margin-bottom:20px;">
                      We received a request to reset your password. Click the button below to set a new password:
                    </p>

                    <p style="text-align:center;">
                      <a href="{reset_link}" 
                         style="background-color:#135965;color:#ffffff;padding:12px 28px;
                         font-size:16px;font-weight:bold;text-decoration:none;
                         border-radius:6px;display:inline-block;">
                         Reset Password
                      </a>
                    </p>

                    <p style="color:#374151;font-size:16px;line-height:24px;margin:20px 0;">
                      Or copy and paste this link into your browser:
                    </p>
                    <p style="color:#197a8a;font-size:14px;line-height:22px;word-break:break-all;">
                      {reset_link}
                    </p>

                    <p style="color:#374151;font-size:16px;line-height:24px;margin-top:20px;">
                      This link will expire in <strong>{context.get('link_expire',0)}</strong>.
                    </p>

                    <hr style="border:0;border-top:1px solid #e5e7eb;margin:30px 0;">
                    <h3 style="color:#111827;font-size:18px;font-weight:bold;">Vibhoos PropCare Security Notice</h3>
                    <p style="color:#374151;font-size:15px;line-height:24px;">
                      If you did not request this password reset, please ignore this email. Your account will remain secure.
                    </p>
                  </td>
                </tr>

                <!-- Footer -->
                <tr>
                  <td style="background-color:#ffffff;padding:30px 40px;border-top:1px solid #e5e7eb;text-align:center;">
                    <p style="color:#6b7280;font-size:12px;line-height:18px;">
                      This is an automated message. Please do not reply.
                    </p>
                    <p style="color:#6b7280;font-size:12px;line-height:18px;">
                      © {current_year} Vibhoos PropCare Pvt. Ltd. All rights reserved.<br>
                      <em>Your Property — Our Priority</em>
                    </p>
                  </td>
                </tr>

              </table>
            </td>
          </tr>
        </table>
      </body>
    </html>
    """

    send_email(to=email, subject=subject, html_content=html_content,to_sender="Forgot-Password")




def send_email(to: str, subject: str, html_content: str,to_sender="") -> bool:
    """
    Send an email using GoDaddy SMTP.
    Args:
        to (str): Recipient email address.
        subject (str): Email subject line.
        html_content (str): HTML content to send.
    Returns:
        bool: True if email sent successfully, else False.
    """
    try:
        # Create the message
        msg = MIMEMultipart()
        msg["From"] = f"VPC {to_sender} <{EMAIL_ADDRESS}>"
        msg["To"] = to
        msg["Subject"] = subject
        msg.attach(MIMEText(html_content, "html"))

        # Connect securely using SSL
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.send_message(msg)

        print(f"✅ Email sent to {to}")
        return True

    except Exception as e:
        print(f"❌ Failed to send email to {to}: {e}")
        return False
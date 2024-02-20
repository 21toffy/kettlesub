import pyotp
from django.core.mail import send_mail
from django.conf import settings


def generate_otp(user):
    secret_key = pyotp.random_base32()
    otp = pyotp.TOTP(secret_key)
    otp_code = otp.now()

    return otp_code


def send_otp_email(user, otp_code):
    subject = 'Account Verification OTP'
    message = f'Your OTP for account verification is: {otp_code}'
    from_email = settings.EMAIL_HOST_USER
    recipient_list = [user.email]

    send_mail(subject, message, from_email, recipient_list)

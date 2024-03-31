from assetsData.models import *
from django.core.mail import send_mail
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import get_template
from django.template import Context

from_email = settings.EMAIL_HOST_USER

# This will send new user their new login credentials!
def credentials(username, password, to):

    mail_template = get_template('email/cred.html')
    plaintext = get_template('email/cred.txt')

    d = { 'username': username, 'password':password }

    subject = 'Store Manager Login Credentials!'
    
    html_content = mail_template.render(d)
    text_content = plaintext.render(d)

    msg = EmailMultiAlternatives(subject, text_content, from_email, [to])
    msg.attach_alternative(html_content, "text/html")
    msg.send()


def relocate_department(old_hod, new_hod, to, data):
    mail_template = get_template('email/relocate.html')
    plaintext = get_template('email/assign.txt')

    d = data

    # Sending email to all three parties
    subject = 'Item has been re-assigned!'
    html_content = mail_template.render(d)
    text_content = plaintext.render(d)

    msg = EmailMultiAlternatives(subject, text_content, from_email, [to, old_hod, new_hod])
    msg.attach_alternative(html_content, "text/html")
    msg.send()

def assign(to, hod, data, alt):
    mail_template = get_template('email/assign_new.html')
    plaintext = get_template('email/assign.txt')

    data["location"] = False
    # Sending email to all three parties
    subject = '[Action Required] Item has been Issued!'
    html_content = mail_template.render(data)
    text_content = plaintext.render(data)
    emails = [to, hod]
    if alt:
        emails.extend(alt)
        msg = EmailMultiAlternatives(subject, text_content, from_email, emails)
    else:
        msg = EmailMultiAlternatives(subject, text_content, from_email, emails)
    msg.attach_alternative(html_content, "text/html")
    msg.send()


def issue(to, data):
    mail_template = get_template('email/issue.html')
    plaintext = get_template('email/assign.txt')

    data["location"] = True

    # Sending email to all three parties
    subject = 'Item has been assigned!'
    html_content = mail_template.render(data)
    text_content = plaintext.render(data)

    msg = EmailMultiAlternatives(subject, text_content, from_email, [to])
    msg.attach_alternative(html_content, "text/html")
    msg.send()

def relocate(to, hod, data):
    mail_template = get_template('email/relocate.html')
    plaintext = get_template('email/assign.txt')

    d = data

    # Sending email to all three parties
    subject = 'Following item has been relocated!'
    html_content = mail_template.render(d)
    text_content = plaintext.render(d)

    msg = EmailMultiAlternatives(subject, text_content, from_email, [to, hod])
    msg.attach_alternative(html_content, "text/html")
    msg.send()

def dump(to_user, data):
    mail_template = get_template('email/dump.html')
    plaintext = get_template('email/assign.txt')

    d = data

    # Sending email to all three parties
    subject = 'Items require dump approval'
    html_content = mail_template.render(d)
    text_content = plaintext.render(d)

    msg = EmailMultiAlternatives(subject, text_content, from_email, [to_user])
    msg.attach_alternative(html_content, "text/html")
    msg.send()

def email_send(to_user, data, old_department = False, type = "genaral", alt=None):
    # to_user is the user class
    user_email = to_user.email
    if type != 'credentials':
        hod_email = profile.objects.get(department = profile.objects.get(user = to_user).department, designation__designation_id = "HOD").user.email
        # print("Hod mail",hod_email)
        if old_department:
            old_department_hod_email = profile.objects.get(department__code = old_department, designation__code = "HOD")
            relocate_department(old_department_hod_email, hod_email, user_email, data)
        
        elif type == 'assign':
            assign(user_email, hod_email, data, alt)

        elif type == 'issue':
            issue(user_email, data)
        
        elif type == 'relocate':
            relocate(user_email, hod_email, data)
        elif type == "dump":
            dump(to_user, data)
        else:
            send_mail(
            subject="Your location has been updated!",
            message=data,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[user_email]
            )
    
    else:
        credentials(data["username"], data["password"], user_email)


from django.urls import reverse_lazy
from django.contrib.auth.views import PasswordResetView
from django.contrib.messages.views import SuccessMessageMixin
class ResetPasswordView(SuccessMessageMixin, PasswordResetView):
    template_name = 'users/password_reset.html'
    subject_template_name = 'resistration/password_reset_email'
    success_message = "We've emailed you instructions for setting your password, " \
                      "if an account exists with the email you entered. You should receive them shortly." \
                      " If you don't receive an email, " \
                      "please make sure you've entered the address you registered with, and check your spam folder."
    success_url = reverse_lazy('users-home')
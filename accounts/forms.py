from django import forms
from allauth.account.forms import SignupForm
from captcha.fields import ReCaptchaField
from captcha.widgets import ReCaptchaV2Checkbox # Or ReCaptchaV3 if you prefer

class CustomSignupForm(SignupForm):
    captcha = ReCaptchaField(widget=ReCaptchaV2Checkbox)
    # For ReCaptchaV3, you'd use:
    # captcha = ReCaptchaField(widget=ReCaptchaV3(action='signup'))


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # You can customize other fields here if needed
        # Example: self.fields['email'].widget.attrs.update({'class': 'my-custom-email-class'})

    def save(self, request):
        # Ensure you call the parent save method
        user = super().save(request)
        # Add any custom logic here after user is saved if necessary
        return user

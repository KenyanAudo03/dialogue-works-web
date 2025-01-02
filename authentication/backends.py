from django.contrib.auth.backends import BaseBackend
from django.contrib.auth import get_user_model

User = get_user_model()  # Automatically fetches UserProfile as the user model

class PhoneEmailAuthenticationBackend(BaseBackend):
    """
    Custom backend to authenticate users using either email or phone number.
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            # Determine whether the identifier is an email or phone number
            if "@" in username:  # Likely an email
                user = User.objects.get(email=username)
            else:  # Assume it's a phone number
                user = User.objects.get(phone_number=username)
        except User.DoesNotExist:
            return None

        # Validate the password
        if user.check_password(password):
            return user
        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None

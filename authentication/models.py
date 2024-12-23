from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models
from django.utils.timezone import now

class Interest(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name
        
class UserProfile(AbstractUser):
    # Remove password field since it's already in AbstractUser
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    course = models.CharField(max_length=100)
    reg_number = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=150, unique=True, blank=True, null=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    whatsapp_verified = models.BooleanField(default=False)
    interests = models.ManyToManyField('Interest', blank=True)
    profile_picture = models.ImageField(
        upload_to="profile_pics/", blank=True, null=True
    )
    joined_date = models.DateTimeField(default=now)
    email_verified = models.BooleanField(default=False)

    # Override groups and user_permissions to avoid clashes
    groups = models.ManyToManyField(
        Group,
        related_name="custom_user_groups",
        blank=True,
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name="custom_user_permissions",
        blank=True,
    )

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

class EmailVerificationToken(models.Model):
    user = models.ForeignKey('UserProfile', on_delete=models.CASCADE)
    token = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['token']),
        ]
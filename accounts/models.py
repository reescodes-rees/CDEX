from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(blank=True, null=True)
    # Add other profile fields here in the future, e.g.:
    # profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    # location = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.user.username

# It's common to automatically create/update UserProfile when User instance is saved.
@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
    else:
        # Ensure profile exists, create if not (e.g., for existing users before profile model was added)
        UserProfile.objects.get_or_create(user=instance)
        # If you want to save profile on user update (e.g. if user email change should trigger something in profile)
        # instance.profile.save() # Be cautious with what you save here automatically

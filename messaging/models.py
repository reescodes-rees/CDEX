from django.db import models
from django.conf import settings
from encrypted_model_fields.fields import EncryptedTextField
# Assuming Listing model is in 'listings' app. Adjust if different.
# from listings.models import Listing # This will cause circular import if Offer is also in listings.
# Best to use string reference 'listings.Listing' in ForeignKey.

class Offer(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('ACCEPTED', 'Accepted by Seller'),
        ('REJECTED', 'Rejected by Seller'),
        ('RETRACTED', 'Retracted by Buyer'),
        ('EXPIRED', 'Expired'), # If offer expiry is implemented
    ]
    listing = models.ForeignKey('listings.Listing', on_delete=models.CASCADE, related_name='offers')
    buyer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='made_offers')
    offer_amount = models.DecimalField(max_digits=12, decimal_places=2)
    is_public = models.BooleanField(default=False, help_text="Buyer can choose to make this offer amount visible on the listing.")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    timestamp = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Offer of ${self.offer_amount} by {self.buyer.username} for listing {self.listing.pk}"

class Conversation(models.Model):
    participants = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='conversations')
    related_listing = models.ForeignKey('listings.Listing', on_delete=models.SET_NULL, null=True, blank=True, related_name='conversations')
    related_offer = models.ForeignKey(Offer, on_delete=models.SET_NULL, null=True, blank=True, related_name='conversations')
    created_at = models.DateTimeField(auto_now_add=True)
    last_message_timestamp = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-last_message_timestamp']

    def __str__(self):
        return f"Conversation {self.pk} (last active: {self.last_message_timestamp})"
        # Better str: participant names, needs a method.

    # Consider a method to update last_message_timestamp when a new message is added.
    # Signals are a good way to do this (post_save on Message model).

class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_messages')
    content = EncryptedTextField() # Encrypted field for message body
    timestamp = models.DateTimeField(auto_now_add=True)
    # is_read = models.BooleanField(default=False) # Simplified for V1, or handle via UserConversationStatus in V2

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"Message from {self.sender.username} at {self.timestamp.strftime('%Y-%m-%d %H:%M')}"

# Signals to update Conversation.last_message_timestamp
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=Message)
def update_conversation_last_message_timestamp(sender, instance, created, **kwargs):
    if created:
        conversation = instance.conversation
        conversation.last_message_timestamp = instance.timestamp
        conversation.save(update_fields=['last_message_timestamp'])

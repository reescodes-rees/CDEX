from django.contrib import admin
from .models import Offer, Conversation, Message

@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):
    list_display = ('id', 'listing', 'buyer', 'offer_amount', 'is_public', 'status', 'timestamp')
    list_filter = ('status', 'is_public', 'timestamp')
    search_fields = ('listing__card_for_listing__card_name', 'buyer__username')
    raw_id_fields = ('listing', 'buyer') # For easier selection with many listings/users

class MessageInline(admin.TabularInline): # Or StackedInline
    model = Message
    extra = 0 # Number of empty forms to display
    fields = ('sender', 'content', 'timestamp') # 'content' will be shown as ciphertext in admin unless custom widget
    readonly_fields = ('timestamp',)
    # For EncryptedTextField, admin display might need customization if you want to decrypt in admin (risky).
    # By default, it will show the encrypted string.

@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_participants_display', 'related_listing_info', 'related_offer_info', 'last_message_timestamp', 'created_at')
    list_filter = ('last_message_timestamp', 'created_at')
    search_fields = ('participants__username',) # Search by participant username
    filter_horizontal = ('participants',) # Better widget for ManyToMany
    inlines = [MessageInline]
    raw_id_fields = ('related_listing', 'related_offer')

    def get_participants_display(self, obj):
        return ", ".join([user.username for user in obj.participants.all()])
    get_participants_display.short_description = 'Participants'

    def related_listing_info(self, obj):
        if obj.related_listing:
            return f"Listing ID: {obj.related_listing.pk}"
        return None
    related_listing_info.short_description = 'Related Listing'

    def related_offer_info(self, obj):
        if obj.related_offer:
            return f"Offer ID: {obj.related_offer.pk} (${obj.related_offer.offer_amount})"
        return None
    related_offer_info.short_description = 'Related Offer'


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'conversation_id_display', 'sender', 'timestamp_display', 'content_preview')
    list_filter = ('timestamp', 'sender')
    search_fields = ('sender__username', 'content') # Searching encrypted content might not work as expected
    raw_id_fields = ('conversation', 'sender')
    readonly_fields = ('timestamp',)

    def conversation_id_display(self, obj):
        return obj.conversation.pk
    conversation_id_display.short_description = 'Conversation ID'

    def timestamp_display(self, obj):
        return obj.timestamp.strftime('%Y-%m-%d %H:%M')
    timestamp_display.short_description = 'Timestamp'

    def content_preview(self, obj):
        # Shows encrypted string. Decrypting here is possible but has security implications.
        return str(obj.content)[:50] + "..." if len(str(obj.content)) > 50 else str(obj.content)
    content_preview.short_description = 'Content (Encrypted Preview)'

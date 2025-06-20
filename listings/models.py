from django.db import models
from django.conf import settings # To get AUTH_USER_MODEL
from django.utils.text import slugify
# Consider using django-imagekit for image processing if needed, e.g., thumbnails
# from imagekit.models import ImageSpecField
# from imagekit.processors import ResizeToFill

class Game(models.Model):
    name = models.CharField(max_length=100, unique=True, help_text="e.g., Pokémon TCG, Magic: The Gathering, NBA Basketball Cards")
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    description = models.TextField(blank=True, null=True)
    # icon_image = models.ImageField(upload_to='game_icons/', blank=True, null=True) # Requires Pillow

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class Card(models.Model):
    CONDITION_CHOICES = [
        ('M', 'Mint'), ('NM', 'Near Mint'), ('LP', 'Lightly Played'),
        ('MP', 'Moderately Played'), ('HP', 'Heavily Played'), ('DMG', 'Damaged')
    ]
    GRADER_CHOICES = [
        ('PSA', 'PSA'), ('BGS', 'Beckett (BGS/BCCG)'), ('SGC', 'SGC'),
        ('CGC', 'CGC'), ('CGS', 'Card Grading Service'), ('OTHER', 'Other')
    ]

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='card_collection')
    game = models.ForeignKey(Game, on_delete=models.SET_NULL, null=True, blank=True, related_name='cards')
    card_name = models.CharField(max_length=255, help_text="e.g., Charizard, LeBron James")
    set_name = models.CharField(max_length=255, blank=True, help_text="e.g., Base Set, Prizm")
    year = models.PositiveIntegerField(null=True, blank=True, help_text="e.g., 1999, 2020")
    card_identifier_in_set = models.CharField(max_length=50, blank=True, help_text="e.g., 4/102, #23")

    attributes = models.JSONField(default=dict, blank=True, help_text='Flexible key-value pairs, e.g., {"Holo": true, "Edition": "1st", "Player": "Michael Jordan"}')

    condition = models.CharField(max_length=3, choices=CONDITION_CHOICES, blank=True)
    is_graded = models.BooleanField(default=False)
    grader = models.CharField(max_length=10, choices=GRADER_CHOICES, blank=True, null=True)
    grade = models.CharField(max_length=20, blank=True, null=True, help_text="e.g., 9, 10 Gem Mint, 8.5")
    certification_number = models.CharField(max_length=100, blank=True, null=True)

    purchase_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Optional: Price you paid for this card.")
    public_description = models.TextField(blank=True, help_text="Publicly visible description of the card, its features, or notable aspects.")
    notes = models.TextField(blank=True, help_text="Your private notes about this card instance.")

    image_1 = models.ImageField(upload_to='card_images/', blank=True, null=True, help_text="Primary image of your card.") # Requires Pillow
    image_2 = models.ImageField(upload_to='card_images/', blank=True, null=True, help_text="Optional secondary image.")
    image_3 = models.ImageField(upload_to='card_images/', blank=True, null=True, help_text="Optional tertiary image.")
    # Consider ImageSpecField for thumbnails if using django-imagekit:
    # image_1_thumbnail = ImageSpecField(source='image_1', processors=[ResizeToFill(100, 150)], format='JPEG', options={'quality': 60})


    date_added_to_collection = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

    # master_card_template = models.ForeignKey('CardMaster', on_delete=models.SET_NULL, null=True, blank=True) # Future hook

    def __str__(self):
        return f"{self.card_name} ({self.owner.username if self.owner else 'No owner'})"

class Listing(models.Model):
    LISTING_TYPE_CHOICES = [('SALE', 'For Sale'), ('TRADE', 'For Trade'), ('AUCTION', 'Auction')]
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'), ('SOLD', 'Sold'), ('TRADED', 'Traded'),
        ('EXPIRED', 'Expired'), ('CANCELLED', 'Cancelled'), ('PENDING', 'Pending Review')
    ]

    lister = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='listings')
    card_for_listing = models.ForeignKey(Card, on_delete=models.CASCADE, related_name='listed_as')

    listing_type = models.CharField(max_length=10, choices=LISTING_TYPE_CHOICES)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='ACTIVE')

    price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, help_text="Required if listing_type is 'Sale'.")
    trade_preference_description = models.TextField(blank=True, help_text="Describe what you're looking for in a trade.")

    auction_start_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, help_text="Required if listing_type is 'Auction'.")
    auction_bid_increment = models.DecimalField(max_digits=10, decimal_places=2, default=1.00, help_text="Minimum amount by which a new bid must exceed the current one.")
    auction_end_datetime = models.DateTimeField(null=True, blank=True, help_text="Date and time when the auction ends.")
    current_highest_bid = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    current_high_bidder = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='current_bids_as_high_bidder')

    listing_description = models.TextField(blank=True, help_text="Additional details about this specific listing.")

    seller_location_city = models.CharField(max_length=100, blank=True)
    seller_location_region = models.CharField(max_length=100, blank=True, help_text="e.g., State, Province")
    seller_location_country = models.CharField(max_length=100, blank=True)
    allows_local_pickup = models.BooleanField(default=True)
    shipping_policy_description = models.TextField(blank=True, help_text="Describe shipping terms, costs, regions (e.g., 'Ships to USA via USPS. Buyer pays $5 flat shipping').")

    views_count = models.PositiveIntegerField(default=0)
    date_created = models.DateTimeField(auto_now_add=True)
    expires_on = models.DateTimeField(null=True, blank=True, help_text="Optional: Date when the listing should automatically expire.")
    last_modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.get_listing_type_display()} of {self.card_for_listing.card_name} by {self.lister.username}"

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('listings:listing-detail', kwargs={'pk': self.pk})

class Bid(models.Model):
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='bids')
    bidder = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bids_made')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp'] # Show newest bids first

    def __str__(self):
        return f"Bid of {self.amount} by {self.bidder.username} on {self.listing.card_for_listing.card_name}"

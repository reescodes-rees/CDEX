from django import forms
from .models import Listing, Card, Bid

class ListingCreateEditForm(forms.ModelForm):
    class Meta:
        model = Listing
        fields = [
            'card_for_listing', 'listing_type', 'price', 'trade_preference_description',
            'auction_start_price', 'auction_bid_increment', 'auction_end_datetime',
            'listing_description', 'seller_location_city', 'seller_location_region',
            'seller_location_country', 'allows_local_pickup', 'shipping_policy_description',
            'expires_on' # Add status later if admins/system can change it, user usually just creates active
        ]
        widgets = {
            'auction_end_datetime': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'expires_on': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'listing_description': forms.Textarea(attrs={'rows': 3}),
            'trade_preference_description': forms.Textarea(attrs={'rows': 3}),
            'shipping_policy_description': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None) # Get user from view kwargs
        super().__init__(*args, **kwargs)
        if user:
            self.fields['card_for_listing'].queryset = Card.objects.filter(owner=user)

        # Basic conditional logic for fields based on listing_type (can be enhanced with JS)
        # For example, make price required if SALE, auction fields if AUCTION
        # This is simplified; more robust logic might be needed in clean() or with JS.
        # self.fields['price'].required = self.instance.listing_type == 'SALE' if self.instance else False
        # self.fields['auction_start_price'].required = self.instance.listing_type == 'AUCTION' if self.instance else False


    def clean(self):
        cleaned_data = super().clean()
        listing_type = cleaned_data.get('listing_type')

        if listing_type == 'SALE':
            if not cleaned_data.get('price'):
                self.add_error('price', 'Price is required for sale listings.')
        elif listing_type == 'AUCTION':
            if not cleaned_data.get('auction_start_price'):
                self.add_error('auction_start_price', 'Start price is required for auctions.')
            if not cleaned_data.get('auction_end_datetime'):
                self.add_error('auction_end_datetime', 'End date/time is required for auctions.')
        # Add more validation as needed (e.g., auction end date > now)
        return cleaned_data

class BidForm(forms.ModelForm):
    class Meta:
        model = Bid
        fields = ['amount']
        widgets = {
            'amount': forms.NumberInput(attrs={'step': '0.01'}),
        }

    def __init__(self, *args, **kwargs):
        self.listing = kwargs.pop('listing', None) # Pass listing from view
        self.user = kwargs.pop('user', None) # Pass user from view
        super().__init__(*args, **kwargs)

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if not self.listing:
            raise forms.ValidationError("Listing information is missing.") # Should not happen if form is instantiated correctly

        if self.listing.listing_type != 'AUCTION':
            raise forms.ValidationError("Bids can only be placed on auction listings.")
        if self.listing.status != 'ACTIVE':
            raise forms.ValidationError("Bids can only be placed on active auctions.")
        if self.listing.auction_end_datetime and self.listing.auction_end_datetime < forms.utils.timezone.now():
            raise forms.ValidationError("This auction has ended.")
        if self.listing.lister == self.user:
            raise forms.ValidationError("You cannot bid on your own auction.")

        min_next_bid = self.listing.current_highest_bid + self.listing.auction_bid_increment if self.listing.current_highest_bid else self.listing.auction_start_price
        if amount < min_next_bid:
            raise forms.ValidationError(f"Bid amount must be at least {min_next_bid}.")

        return amount

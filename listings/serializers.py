from rest_framework import serializers
from .models import Game, Card, Listing, Bid
from django.contrib.auth import get_user_model

User = get_user_model()

class GameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Game
        fields = ['id', 'name', 'slug', 'description'] # Removed 'icon_image'
        read_only_fields = ['slug'] # Slug is auto-generated

class CardSerializer(serializers.ModelSerializer):
    owner_username = serializers.CharField(source='owner.username', read_only=True)
    game_name = serializers.CharField(source='game.name', read_only=True, allow_null=True)

    class Meta:
        model = Card
        fields = [
            'id', 'owner', 'owner_username', 'game', 'game_name', 'card_name', 'set_name', 'year',
            'card_identifier_in_set', 'attributes', 'condition', 'is_graded',
            'grader', 'grade', 'certification_number', 'purchase_price', 'notes',
            'image_1', 'image_2', 'image_3',
            'date_added_to_collection', 'last_modified'
        ]
        read_only_fields = ['owner', 'owner_username', 'game_name'] # Owner set automatically

    def validate_owner(self, value):
        # This validation might not be strictly necessary if we set owner in view,
        # but ensures if 'owner' is ever part of input, it's the request user.
        if self.context['request'].user != value:
            raise serializers.ValidationError("You cannot set the owner to another user.")
        return value

class ListingSerializer(serializers.ModelSerializer):
    lister_username = serializers.CharField(source='lister.username', read_only=True)
    # card_for_listing_details = CardSerializer(source='card_for_listing', read_only=True) # To show full card details

    # Allow selecting card by ID from user's collection
    card_for_listing = serializers.PrimaryKeyRelatedField(queryset=Card.objects.none())


    class Meta:
        model = Listing
        fields = [
            'id', 'lister', 'lister_username', 'card_for_listing', # 'card_for_listing_details',
            'listing_type', 'status', 'price', 'trade_preference_description',
            'auction_start_price', 'auction_bid_increment', 'auction_end_datetime',
            'current_highest_bid', 'current_high_bidder', # Consider if high_bidder should be UserSerializer
            'listing_description', 'seller_location_city', 'seller_location_region',
            'seller_location_country', 'allows_local_pickup', 'shipping_policy_description',
            'views_count', 'date_created', 'expires_on', 'last_modified'
        ]
        read_only_fields = ['lister', 'lister_username', 'status', 'current_highest_bid', 'current_high_bidder', 'views_count']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Dynamically set the queryset for card_for_listing based on the current user
        # This ensures users can only list cards they own.
        request = self.context.get('request', None)
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            self.fields['card_for_listing'].queryset = Card.objects.filter(owner=request.user)
        else:
            # For anonymous users or if request is not available (e.g. schema generation),
            # provide an empty queryset or all cards if that's desired for some reason.
             self.fields['card_for_listing'].queryset = Card.objects.none()


class BidSerializer(serializers.ModelSerializer):
    bidder_username = serializers.CharField(source='bidder.username', read_only=True)

    class Meta:
        model = Bid
        fields = ['id', 'listing', 'bidder', 'bidder_username', 'amount', 'timestamp']
        read_only_fields = ['bidder', 'bidder_username', 'timestamp']

    def validate(self, data):
        listing = data.get('listing')
        amount = data.get('amount')
        request_user = self.context['request'].user

        if listing.listing_type != 'AUCTION':
            raise serializers.ValidationError("Bids can only be placed on auction listings.")
        if listing.status != 'ACTIVE':
            raise serializers.ValidationError("Bids can only be placed on active auctions.")
        if listing.auction_end_datetime and listing.auction_end_datetime < serializers.timezone.now():
            raise serializers.ValidationError("This auction has ended.")
        if listing.lister == request_user:
            raise serializers.ValidationError("You cannot bid on your own auction.")

        min_next_bid = listing.current_highest_bid + listing.auction_bid_increment if listing.current_highest_bid else listing.auction_start_price
        if amount < min_next_bid:
            raise serializers.ValidationError(f"Bid amount must be at least {min_next_bid}.")

        return data

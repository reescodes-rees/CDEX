from rest_framework import viewsets, permissions, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend # For filtering
from rest_framework.filters import SearchFilter, OrderingFilter
from django.core.exceptions import PermissionDenied


from .models import Game, Card, Listing, Bid
from .serializers import GameSerializer, CardSerializer, ListingSerializer, BidSerializer
from .permissions import IsOwnerOrReadOnly, IsBidderOrListingOwner

class GameViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint for viewing Games."""
    queryset = Game.objects.all().order_by('name')
    serializer_class = GameSerializer
    permission_classes = [permissions.AllowAny] # Anyone can view games
    lookup_field = 'slug'

class UserCardViewSet(viewsets.ModelViewSet):
    """API endpoint for the authenticated user's cards (their collection)."""
    serializer_class = CardSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['game', 'condition', 'is_graded', 'grader'] # Fields for filtering
    search_fields = ['card_name', 'set_name', 'attributes'] # Fields for text search
    ordering_fields = ['card_name', 'year', 'date_added_to_collection'] # Fields for ordering

    def get_queryset(self):
        return Card.objects.filter(owner=self.request.user).order_by('-date_added_to_collection')

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

class ListingViewSet(viewsets.ModelViewSet):
    """
    API endpoint for Listings.
    Allows filtering by game (e.g., ?game__slug=pokemon-tcg), listing_type, status.
    Allows searching by card_name, set_name in the related card.
    Allows ordering.
    """
    queryset = Listing.objects.filter(status='ACTIVE').select_related('card_for_listing__game', 'lister').order_by('-date_created')
    serializer_class = ListingSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    # To filter on related model fields: 'card_for_listing__game__slug', 'card_for_listing__condition'
    filterset_fields = {
        'listing_type': ['exact'],
        'status': ['exact'],
        'card_for_listing__game__slug': ['exact'], # e.g. ?card_for_listing__game__slug=pokemon-tcg
        'seller_location_country': ['exact'],
        'seller_location_city': ['iexact'], # case-insensitive exact match
        'allows_local_pickup': ['exact'],
        'price': ['gte', 'lte'], # greater/less than or equal to
    }
    search_fields = [
        'card_for_listing__card_name',
        'card_for_listing__set_name',
        'listing_description',
        'card_for_listing__attributes' # Search within JSON attributes
    ]
    ordering_fields = ['price', 'date_created', 'auction_end_datetime', 'views_count']


    def get_serializer_context(self):
        # Pass request to serializer context, useful for dynamic field querysets (like card_for_listing)
        return {'request': self.request, 'format': self.format_kwarg, 'view': self}

    def perform_create(self, serializer):
        # Ensure the card being listed belongs to the user
        card = serializer.validated_data['card_for_listing']
        if card.owner != self.request.user:
            raise PermissionDenied("You can only list cards you own.")
        serializer.save(lister=self.request.user)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def place_bid(self, request, pk=None):
        listing = self.get_object()
        serializer = BidSerializer(data=request.data, context={'request': request, 'listing': listing}) # Pass listing to context

        # Manually add listing to serializer data if not already present for validation
        if 'listing' not in serializer.initial_data:
             serializer.initial_data['listing'] = listing.pk

        if serializer.is_valid():
            # Additional check: Ensure listing is an auction and active
            if listing.listing_type != 'AUCTION' or listing.status != 'ACTIVE':
                return Response({'error': 'Bids can only be placed on active auctions.'}, status=status.HTTP_400_BAD_REQUEST)

            bid = serializer.save(bidder=request.user, listing=listing)

            # Update listing's current_highest_bid and high_bidder
            listing.current_highest_bid = bid.amount
            listing.current_high_bidder = request.user
            listing.save()

            return Response(BidSerializer(bid).data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'], permission_classes=[permissions.IsAuthenticated, IsBidderOrListingOwner]) # Or more specific permission
    def bids(self, request, pk=None):
        listing = self.get_object()
        # Permissions: Lister can see all bids. Bidders might see their own, or this could be admin-only.
        # For now, let's assume lister can see all bids.
        if request.user != listing.lister:
            # Could refine to allow bidders to see their own bids on this listing
            # For simplicity, restricting to lister for now.
            return Response({"detail": "You do not have permission to view all bids for this listing."}, status=status.HTTP_403_FORBIDDEN)

        queryset = Bid.objects.filter(listing=listing).order_by('-timestamp')
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = BidSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)

        serializer = BidSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)

    # Increment view count - could be done more robustly to avoid race conditions / bot views
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.views_count += 1
        instance.save(update_fields=['views_count']) # Only update this field
        return super().retrieve(request, *args, **kwargs)


from django.views.generic import CreateView, ListView, DetailView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy, reverse
from django.shortcuts import redirect, get_object_or_404
from django.http import HttpResponseForbidden
from django.contrib import messages
from .forms import ListingCreateEditForm, BidForm
from .models import Listing # Already imported Game, Card, Bid
from django.db.models import Q # For search
from django.utils import timezone # For comparing dates in BidForm and ListingDetailView

class CreateListingView(LoginRequiredMixin, CreateView):
    model = Listing
    form_class = ListingCreateEditForm
    template_name = 'listings/listing_form.html'
    # success_url = reverse_lazy('listings:listing-list') # Change to detail view of created listing

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user # Pass user to form
        return kwargs

    def form_valid(self, form):
        form.instance.lister = self.request.user
        # Check card owner again, though form queryset should handle it
        if form.cleaned_data['card_for_listing'].owner != self.request.user:
             # This case should ideally be prevented by the form's queryset for card_for_listing
            messages.error(self.request, "You can only list cards you own.")
            return self.form_invalid(form)

        response = super().form_valid(form)
        messages.success(self.request, "Listing created successfully!")
        return redirect(reverse('listings:listing-detail', kwargs={'pk': self.object.pk}))


class EditListingView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Listing
    form_class = ListingCreateEditForm
    template_name = 'listings/listing_form.html'
    # success_url = reverse_lazy('listings:listing-list') # Change to detail view

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user # Pass user to form
        return kwargs

    def test_func(self): # For UserPassesTestMixin
        listing = self.get_object()
        return self.request.user == listing.lister

    def form_valid(self, form):
        messages.success(self.request, "Listing updated successfully!")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('listings:listing-detail', kwargs={'pk': self.object.pk})


class DeleteListingView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Listing
    template_name = 'listings/listing_confirm_delete.html'
    success_url = reverse_lazy('listings:listing-list') # Or user's profile/dashboard

    def test_func(self): # For UserPassesTestMixin
        listing = self.get_object()
        return self.request.user == listing.lister

    def post(self, request, *args, **kwargs):
        # Can change status to 'CANCELLED' instead of deleting, or actual delete.
        # For now, actual delete via DeleteView.
        messages.success(self.request, "Listing deleted successfully.")
        return super().post(request, *args, **kwargs)


class ListingsView(ListView):
    model = Listing
    template_name = 'listings/listing_list.html'
    context_object_name = 'listings'
    paginate_by = 10 # Adjust as needed

    def get_queryset(self):
        # Filter by active status, add more filters as needed (e.g., by game)
        queryset = Listing.objects.filter(status='ACTIVE').select_related('card_for_listing__game', 'lister').order_by('-date_created')

        game_filter = self.request.GET.get('game')
        if game_filter:
            queryset = queryset.filter(card_for_listing__game__slug=game_filter)

        # Add search query
        search_query = self.request.GET.get('q')
        if search_query:
            queryset = queryset.filter(
                Q(card_for_listing__card_name__icontains=search_query) |
                Q(card_for_listing__set_name__icontains=search_query) |
                Q(listing_description__icontains=search_query) |
                Q(card_for_listing__game__name__icontains=search_query)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['games'] = Game.objects.all().order_by('name') # For filter dropdown
        context['current_game_filter'] = self.request.GET.get('game', '')
        context['search_query'] = self.request.GET.get('q', '')
        return context


class ListingDetailView(DetailView):
    model = Listing
    template_name = 'listings/listing_detail.html'
    context_object_name = 'listing'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        listing = self.get_object()

        # Increment view count (simple version)
        listing.views_count += 1
        listing.save(update_fields=['views_count'])

        if listing.listing_type == 'AUCTION' and listing.status == 'ACTIVE':
            context['bid_form'] = BidForm(listing=listing, user=self.request.user if self.request.user.is_authenticated else None)
            context['bids'] = listing.bids.all().order_by('-timestamp')[:10] # Show recent bids
            context['timezone_now'] = timezone.now() # For template comparison
        return context

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return HttpResponseForbidden("You must be logged in to place a bid.")

        self.object = self.get_object() # Sets self.object for get_context_data if needed
        if self.object.listing_type != 'AUCTION' or self.object.status != 'ACTIVE':
            messages.error(request, "Bids can only be placed on active auctions.")
            return redirect(reverse('listings:listing-detail', kwargs={'pk': self.object.pk}))


        form = BidForm(request.POST, listing=self.object, user=request.user)
        if form.is_valid():
            bid = form.save(commit=False)
            bid.bidder = request.user
            bid.listing = self.object
            bid.save()

            # Update listing's current_highest_bid and high_bidder
            self.object.current_highest_bid = bid.amount
            self.object.current_high_bidder = request.user
            self.object.save()

            messages.success(request, f"Bid of ${bid.amount} placed successfully!")
        else:
            # Pass errors to template or display via messages framework
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field.capitalize() if field != '__all__' else ''}: {error}")

        return redirect(reverse('listings:listing-detail', kwargs={'pk': self.object.pk}))

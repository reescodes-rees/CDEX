from django.urls import path
from .views import (
    CreateListingView, EditListingView, DeleteListingView,
    ListingsView, ListingDetailView,
    UserCardListView, UserCardDetailView, UserCardCreateView,
    UserCardUpdateView, UserCardDeleteView
)

app_name = 'listings'

urlpatterns = [
    path('', ListingsView.as_view(), name='listing-list'),
    path('new/', CreateListingView.as_view(), name='listing-create'),
    path('<int:pk>/', ListingDetailView.as_view(), name='listing-detail'),
    path('<int:pk>/edit/', EditListingView.as_view(), name='listing-edit'),
    path('<int:pk>/delete/', DeleteListingView.as_view(), name='listing-delete'),
    # User Card Collection URLs
    path('my-collection/', UserCardListView.as_view(), name='my-card-list'),
    path('my-collection/new-card/', UserCardCreateView.as_view(), name='my-card-create'),
    path('my-collection/card/<int:pk>/', UserCardDetailView.as_view(), name='my-card-detail'),
    path('my-collection/card/<int:pk>/edit/', UserCardUpdateView.as_view(), name='my-card-edit'),
    path('my-collection/card/<int:pk>/delete/', UserCardDeleteView.as_view(), name='my-card-delete')
]

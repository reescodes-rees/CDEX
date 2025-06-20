from django.urls import path
from .views import (
    CreateListingView, EditListingView, DeleteListingView,
    ListingsView, ListingDetailView
)

app_name = 'listings' # Important for namespacing in templates e.g. {% url 'listings:listing-list' %}

urlpatterns = [
    path('', ListingsView.as_view(), name='listing-list'),
    path('new/', CreateListingView.as_view(), name='listing-create'),
    path('<int:pk>/', ListingDetailView.as_view(), name='listing-detail'),
    path('<int:pk>/edit/', EditListingView.as_view(), name='listing-edit'),
    path('<int:pk>/delete/', DeleteListingView.as_view(), name='listing-delete'),
]

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import GameViewSet, UserCardViewSet, ListingViewSet

router = DefaultRouter()
router.register(r'games', GameViewSet, basename='game')
router.register(r'my-cards', UserCardViewSet, basename='usercard') # For user's own collection
router.register(r'listings', ListingViewSet, basename='listing')
# Bids are handled as an action within ListingViewSet for now

urlpatterns = [
    path('', include(router.urls)),
]

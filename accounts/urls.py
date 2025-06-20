from django.urls import path
from .views import UserProfileDetailView, ProfilePageView # Added ProfilePageView

urlpatterns = [
    path('profile/', UserProfileDetailView.as_view(), name='user-profile-detail'), # API endpoint
    path('profile-ui/', ProfilePageView.as_view(), name='user-profile-ui'),   # Web page for profile
]

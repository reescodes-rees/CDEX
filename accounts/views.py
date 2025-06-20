from rest_framework import generics, permissions
from .models import UserProfile
from .serializers import UserProfileSerializer

class UserProfileDetailView(generics.RetrieveUpdateAPIView):
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        profile, created = UserProfile.objects.get_or_create(user=self.request.user)
        return profile

from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin

class ProfilePageView(LoginRequiredMixin, TemplateView):
    template_name = 'account/profile_page.html' # Or 'profiles/profile_page.html' if you prefer

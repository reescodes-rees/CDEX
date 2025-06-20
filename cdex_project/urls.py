from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')), # Allauth UIs for web flow

    # API Authentication URLs from dj-rest-auth
    path('api/auth/', include('dj_rest_auth.urls')),
    path('api/auth/registration/', include('dj_rest_auth.registration.urls')),

    # Include your new accounts API URLs (for profile)
    path('api/accounts/', include('accounts.urls')), # Added line for profile API
]

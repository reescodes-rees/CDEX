from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView # For home page example

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')), # Allauth UIs

    # API URLs
    path('api/auth/', include('dj_rest_auth.urls')),
    path('api/auth/registration/', include('dj_rest_auth.registration.urls')),
    path('api/accounts/', include('accounts.urls')), # Profile API
    path('api/', include('listings.urls')), # Listings App API URLs (games, my-cards, listings)

    # Web Application URLs for Listings (non-API)
    path('listings/', include('listings.urls_web', namespace='listings')), # New include for web views

    # TODO: Add a home page URL:
    path('', TemplateView.as_view(template_name='pages/home.html'), name='home'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

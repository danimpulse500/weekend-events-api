from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from apps.events.views import dashboard_view

admin.site.site_header = "Weekend Events Dashboard"
admin.site.site_title = "Weekend Events"
admin.site.index_title = "Event Management"

urlpatterns = [
    path('admin/', admin.site.urls),
    path('dashboard/', dashboard_view, name='dashboard'),

    # API
    path('api/', include([
        path('', include('apps.events.urls')),
        path('', include('apps.tickets.urls')),
        path('', include('apps.webhooks.urls')),
        path('', include('apps.health.urls')),
    ])),

    # Swagger UI
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

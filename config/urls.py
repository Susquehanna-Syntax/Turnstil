from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve as static_serve

urlpatterns = [
    # PWA files served from root scope
    path('sw.js', static_serve, {'document_root': settings.BASE_DIR / 'static', 'path': 'sw.js'}, name='sw'),
    path('manifest.json', static_serve, {'document_root': settings.BASE_DIR / 'static', 'path': 'manifest.json'}, name='manifest'),
    path('admin/', admin.site.urls),
    path('api/', include('core.api_urls')),
    path('', include('core.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

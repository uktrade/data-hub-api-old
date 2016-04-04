from django.conf.urls import include, url
from django.contrib import admin

urlpatterns = [
    url(r'^organisation/', include('organisation.urls', namespace='organisation')),
    url(r'^admin/', admin.site.urls),
]

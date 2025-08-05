"""
URL configuration for keralasellers project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path,include
from django.conf import settings
from django.conf.urls.static import static
from store.views import PublicStoreView, PublicStoreListView
from users.views import BuyerProfileView

urlpatterns = [
    path('admin/', admin.site.urls),
    path("user/", include("users.urls")),
    path('api/subscriptions/', include('subscriptions.urls')), # <-- Add this line
    path('api/buyer/profile/', BuyerProfileView.as_view(), name='buyer-profile'),

    path('api/chat/', include('chat.urls')),
    path('shop/<str:seller_phone>/', PublicStoreView.as_view(), name='public-store-view'),

    path('shops/', PublicStoreListView.as_view(), name='public-store-list'),


]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
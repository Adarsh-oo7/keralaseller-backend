from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import OrderViewSet, GenerateBillView, CreateLocalOrderView

router = DefaultRouter()
router.register(r'', OrderViewSet, basename='order')

urlpatterns = [
    # ✅ Specific paths MUST come BEFORE the general router
    path('create-local-order/', CreateLocalOrderView.as_view(), name='create-local-order'),
    path('<int:pk>/generate-bill/', GenerateBillView.as_view(), name='generate-bill'),
    
    # The router handles all other general paths like / and /<id>/
    path('', include(router.urls)),
]
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import OrderViewSet, GenerateBillView, CreateOrderView, BuyerOrderHistoryView # ✅ Make sure it's imported

router = DefaultRouter()
router.register(r'', OrderViewSet, basename='order')

urlpatterns = [
    path('create-order/', CreateOrderView.as_view(), name='create-order'),
    path('<int:pk>/generate-bill/', GenerateBillView.as_view(), name='generate-bill'),
    
    # ✅ This path should now work correctly
    path('history/', BuyerOrderHistoryView.as_view(), name='buyer-order-history'),
    
    path('', include(router.urls)),
]
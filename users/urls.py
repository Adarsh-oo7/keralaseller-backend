from django.urls import path
from .views import SendOTP, RegisterSeller, LoginSeller,seller_dashboard
from . import views
urlpatterns = [
    path('send-otp/', views.SendOTP.as_view(), name='send_otp'),
    path('register/', views.RegisterSeller.as_view(), name='register_seller'),
    path('login/', views.LoginSeller.as_view(), name='login_seller'),
    path('login-direct/', views.LoginSellerDirect.as_view(), name='login_seller_direct'),  # ✅ Debug endpoint
    path('dashboard/', views.seller_dashboard, name='seller_dashboard'),
    path('check-seller/<str:phone>/', views.check_seller_exists, name='check_seller_exists'),  # ✅ Debug endpoint
    path('list-sellers/', views.list_all_sellers, name='list_all_sellers'),  # ✅ Debug endpoint
]
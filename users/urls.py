from django.urls import path,include
from .views import SendOTP, RegisterSeller, LoginSeller,GoogleLoginView, VerifyBuyerOTP, SendBuyerOTP
from . import views
urlpatterns = [
    path('send-otp/', views.SendOTP.as_view(), name='send_otp'),
    path('register/', views.RegisterSeller.as_view(), name='register_seller'),
    path('login/', views.LoginSeller.as_view(), name='login_seller'),
    path('store/', include('store.urls')),

    path('dashboard/', views.seller_dashboard, name='seller_dashboard'),
    path('buyer/login/google/', GoogleLoginView.as_view(), name='buyer-google-login'),

    path('orders/', include('orders.urls')),
    path('buyer/send-otp/', SendBuyerOTP.as_view(), name='send-buyer-otp'),
    path('buyer/verify-otp/', VerifyBuyerOTP.as_view(), name='verify-buyer-otp'),


]
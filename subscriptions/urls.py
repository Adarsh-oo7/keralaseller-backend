from django.urls import path
from .views import PlanListView, CreateSubscriptionOrderView, VerifySubscriptionView

urlpatterns = [
    path('plans/', PlanListView.as_view(), name='plan-list'),
    path('create-order/', CreateSubscriptionOrderView.as_view(), name='create-subscription-order'),
    path('verify-payment/', VerifySubscriptionView.as_view(), name='verify-subscription-payment'),
]
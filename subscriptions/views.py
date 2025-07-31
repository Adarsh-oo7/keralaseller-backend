from django.conf import settings
from django.utils import timezone
import datetime
import razorpay
from rest_framework import status, permissions
from rest_framework.generics import ListAPIView
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Plan, Subscription
from .serializers import PlanSerializer, SubscriptionSerializer

# Initialize Razorpay client
razorpay_client = razorpay.Client(
    auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
)

class PlanListView(ListAPIView):
    queryset = Plan.objects.all().order_by('price')
    serializer_class = PlanSerializer
    permission_classes = [permissions.IsAuthenticated]

class CreateSubscriptionOrderView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        plan_id = request.data.get('plan_id')
        try:
            plan = Plan.objects.get(id=plan_id)
        except Plan.DoesNotExist:
            return Response({'error': 'Plan not found'}, status=status.HTTP_404_NOT_FOUND)

        order_amount = int(plan.price * 100) # Amount in paise
        order_currency = 'INR'
        
        order = razorpay_client.order.create({
            'amount': order_amount,
            'currency': order_currency,
            'payment_capture': '1'
        })
        
        return Response({'order_id': order['id'], 'amount': order['amount']}, status=status.HTTP_200_OK)

class VerifySubscriptionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        payment_id = request.data.get('razorpay_payment_id')
        order_id = request.data.get('razorpay_order_id')
        signature = request.data.get('razorpay_signature')
        plan_id = request.data.get('plan_id')
        
        params_dict = {
            'razorpay_order_id': order_id,
            'razorpay_payment_id': payment_id,
            'razorpay_signature': signature
        }

        try:
            razorpay_client.utility.verify_payment_signature(params_dict)
            plan = Plan.objects.get(id=plan_id)
            seller = request.user
            
            # Get or create a subscription object for the seller
            subscription, created = Subscription.objects.get_or_create(seller=seller)
            
            # Update the subscription details
            subscription.plan = plan
            subscription.start_date = timezone.now()
            subscription.end_date = timezone.now() + datetime.timedelta(days=plan.duration_days)
            subscription.razorpay_order_id = order_id
            subscription.razorpay_payment_id = payment_id
            subscription.razorpay_signature = signature
            subscription.save()
            
            return Response({'status': 'Payment successful, subscription activated.'}, status=status.HTTP_200_OK)
            
        except razorpay.errors.SignatureVerificationError:
            return Response({'error': 'Payment verification failed'}, status=status.HTTP_400_BAD_REQUEST)
        except Plan.DoesNotExist:
            return Response({'error': 'Plan not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
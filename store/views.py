# In store/views.py

from rest_framework import viewsets, permissions
from .models import Product
from .serializers import ProductSerializer, StoreProfileSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import razorpay # Import the razorpay library
from razorpay.errors import BadRequestError, ServerError   



class ProductViewSet(viewsets.ModelViewSet):
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Return only products owned by the currently logged-in seller
        # This assumes you have a signal or logic to create a StoreProfile on seller registration
        return Product.objects.filter(store__seller=self.request.user)

    def perform_create(self, serializer):
        # Automatically assign the seller's store when creating a new product
        serializer.save(store=self.request.user.store_profile)






class StoreProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        store_profile = request.user.store_profile
        serializer = StoreProfileSerializer(store_profile, context={'request': request})
        return Response(serializer.data)

    def patch(self, request):
        store_profile = request.user.store_profile
        
        key_id = request.data.get('razorpay_key_id')
        key_secret = request.data.get('razorpay_key_secret')

        if request.data.get('payment_method') == 'RAZORPAY' and key_id and key_secret:
            try:
                client = razorpay.Client(auth=(key_id, key_secret))
                client.payment.all({'count': 1})
                print("✅ Razorpay keys are valid.")
            except Exception as e:
                # This general catch is more robust. We check the error text.
                error_message = str(e).lower()
                if 'authentication failed' in error_message or 'bad credentials' in error_message:
                    print("❌ Invalid Razorpay keys detected.")
                    return Response(
                        {"error": "Invalid Razorpay Key ID or Key Secret. Please check again."},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                else:
                    # It was a different kind of error (e.g., network issue)
                    print(f"An unexpected error occurred during Razorpay verification: {e}")
                    return Response(
                        {"error": "Could not verify Razorpay keys. Please try again later."},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
        
        serializer = StoreProfileSerializer(
            store_profile, data=request.data, partial=True, context={'request': request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

from django.http import HttpResponse
from django.template.loader import render_to_string
from django.db import transaction, models
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from .models import Order, OrderItem
from .serializers import OrderSerializer
from store.models import Product
from users.models import Seller, Buyer
from users.views import IsBuyer # Assuming IsBuyer is in users/views.p
# ==============================================================================
# SELLER-FACING ORDER MANAGEMENT
# ==============================================================================
class OrderViewSet(viewsets.ReadOnlyModelViewSet):
    """
    A viewset for sellers to view and manage their orders.
    """
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(store__seller=self.request.user).order_by('-created_at')

    @action(detail=True, methods=['patch'])
    def update_status(self, request, pk=None):
        order = self.get_object()
        new_status = request.data.get('status')
        shipping_provider = request.data.get('shipping_provider')
        tracking_id = request.data.get('tracking_id')

        valid_statuses = [choice[0] for choice in Order.OrderStatus.choices]
        if new_status not in valid_statuses:
            return Response({'error': 'Invalid status provided.'}, status=status.HTTP_400_BAD_REQUEST)
            
        order.status = new_status
        if new_status == 'SHIPPED':
            order.shipping_provider = shipping_provider
            order.tracking_id = tracking_id
        
        order.save()
        return Response(self.get_serializer(order).data)

# ==============================================================================
# BUYER-FACING ORDER HISTORY
# ==============================================================================
class BuyerOrderHistoryView(ListAPIView):
    """
    Provides a list of all orders placed by the authenticated buyer.
    """
    serializer_class = OrderSerializer
    permission_classes = [IsBuyer]

    def get_queryset(self):
        # Filters orders based on the direct link to the buyer
        return Order.objects.filter(buyer=self.request.user).order_by('-created_at')

# ==============================================================================
# SHARED BILLING & ORDER CREATION
# ==============================================================================
class GenerateBillView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk=None):
        try:
            # Allows the seller of the order OR the buyer who placed it to view the bill.
            order = Order.objects.get(
                models.Q(pk=pk),
                models.Q(store__seller=request.user) | models.Q(buyer=request.user)
            )
            context = {'order': order, 'store': order.store}
            html_string = render_to_string('bill_template.html', context)
            return HttpResponse(html_string)
        except Order.DoesNotExist:
            return HttpResponse("Order not found or permission denied.", status=404)

class CreateOrderView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        user = request.user
        items_data = request.data.get('items')
        
        if not items_data:
            return Response({'error': 'No items provided.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                # Determine store, customer details, and initial status based on user type
                if isinstance(user, Seller):
                    store_profile = user.store_profile
                    customer_name = request.data.get('customer_name', 'Local Customer')
                    customer_phone = request.data.get('customer_phone', 'N/A')
                    shipping_address = "In-store Purchase"
                    initial_status = Order.OrderStatus.DELIVERED
                    buyer_instance = None
                elif isinstance(user, Buyer):
                    product_id = items_data[0]['id']
                    store_profile = Product.objects.get(id=product_id).store
                    customer_name = request.data.get('customer_name', user.full_name)
                    customer_phone = request.data.get('customer_phone', user.phone_number)
                    shipping_address = request.data.get('shipping_address')
                    initial_status = Order.OrderStatus.PENDING
                    buyer_instance = user
                else:
                    return Response({'error': 'Invalid user type.'}, status=status.HTTP_403_FORBIDDEN)

                # Create the Order instance
                new_order = Order.objects.create(
                    store=store_profile,
                    buyer=buyer_instance,
                    customer_name=customer_name,
                    customer_phone=customer_phone,
                    shipping_address=shipping_address,
                    total_amount=0, # Placeholder
                    status=initial_status
                )

                total_amount = 0
                order_items_to_create = []
                for item in items_data:
                    product = Product.objects.get(id=item['id'], store=store_profile)
                    quantity = int(item['quantity'])

                    # Stock validation
                    if product.total_stock < quantity:
                        raise Exception(f"Not enough total stock for {product.name}.")
                    if isinstance(user, Buyer) and product.online_stock < quantity:
                        raise Exception(f"Not enough online stock for {product.name}.")

                    # Deduct stock
                    product.total_stock -= quantity
                    if isinstance(user, Buyer):
                        product.online_stock -= quantity
                    
                    product._current_user = user
                    product._stock_change_note = f"Sale for Order #{new_order.id}"
                    product.save()

                    item_total = product.price * quantity
                    total_amount += item_total
                    order_items_to_create.append(
                        OrderItem(order=new_order, product=product, quantity=quantity, price=product.price)
                    )
                
                OrderItem.objects.bulk_create(order_items_to_create)
                new_order.total_amount = total_amount
                new_order.save()

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({'order_id': new_order.id}, status=status.HTTP_201_CREATED)



import razorpay
from django.conf import settings

# Initialize Razorpay client at the top of the file
razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

class CreatePaymentOrderView(APIView):
    """
    Creates a Razorpay order for the checkout amount.
    """
    permission_classes = [permissions.IsAuthenticated] # Should be IsBuyer

    def post(self, request):
        amount = request.data.get('amount')
        if not amount:
            return Response({'error': 'Amount is required.'}, status=400)

        try:
            order_amount = int(float(amount) * 100) # Amount in paise
            order_currency = 'INR'
            
            razorpay_order = razorpay_client.order.create({
                'amount': order_amount,
                'currency': order_currency,
                'payment_capture': '0' # ✅ 0 = Authorize only, 1 = Capture immediately
            })
            
            return Response({
                'order_id': razorpay_order['id'],
                'amount': razorpay_order['amount']
            })
        except Exception as e:
            return Response({'error': str(e)}, status=500)

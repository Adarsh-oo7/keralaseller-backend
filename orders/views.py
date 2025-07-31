from django.http import HttpResponse
from django.template.loader import render_to_string
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Order
from .serializers import OrderSerializer

class OrderViewSet(viewsets.ReadOnlyModelViewSet):
    """
    A viewset for sellers to view and manage their orders.
    Sellers can view orders and update their status and tracking info.
    """
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Ensures sellers can only see orders belonging to their own store.
        """
        return Order.objects.filter(store__seller=self.request.user).order_by('-created_at')

    @action(detail=True, methods=['patch'])
    def update_status(self, request, pk=None):
        """
        Updates the status of an order. If the new status is 'SHIPPED',
        it also saves the shipping provider and tracking ID.
        """
        order = self.get_object()
        new_status = request.data.get('status')
        shipping_provider = request.data.get('shipping_provider')
        tracking_id = request.data.get('tracking_id')

        # Validate the new status
        valid_statuses = [choice[0] for choice in Order.OrderStatus.choices]
        if new_status not in valid_statuses:
            return Response({'error': 'Invalid status provided.'}, status=status.HTTP_400_BAD_REQUEST)
            
        order.status = new_status
        
        # If the order is marked as SHIPPED, save the tracking information
        if new_status == 'SHIPPED':
            order.shipping_provider = shipping_provider
            order.tracking_id = tracking_id
        
        order.save()
        return Response(self.get_serializer(order).data)


class GenerateBillView(APIView):
    """
    Generates a simple HTML invoice for a given order.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk=None):
        try:
            # Ensure the seller can only generate bills for their own orders
            order = Order.objects.get(pk=pk, store__seller=request.user)
            
            # Data to be passed to the HTML template
            context = {
                'order': order,
                'store': order.store,
                'seller': order.store.seller
            }
            
            # Render the template to an HTML string
            html_string = render_to_string('bill_template.html', context)
            
            # Return the HTML as a response that the browser can display
            return HttpResponse(html_string)
            
        except Order.DoesNotExist:
            return HttpResponse("Order not found or you do not have permission to view this bill.", status=404)
        

# In orders/views.py
from store.models import Product
from django.db import transaction
from .models import Order, OrderItem
# ... (your existing imports and views)

class CreateLocalOrderView(APIView):
    """
    Creates an order record and returns a bill for a local (offline) sale.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        seller = request.user
        store_profile = seller.store_profile
        
        items_data = request.data.get('items')
        customer_name = request.data.get('customer_name', 'Local Customer')
        customer_phone = request.data.get('customer_phone', 'N/A')

        if not items_data:
            return Response({'error': 'No items in the bill.'}, status=status.HTTP_400_BAD_REQUEST)
        
        total_amount = 0
        order_items_to_create = []

        with transaction.atomic():
            # Create the main order record first
            new_order = Order.objects.create(
                store=store_profile,
                customer_name=customer_name,
                customer_phone=customer_phone,
                shipping_address="In-store Purchase",
                total_amount=0, # We'll calculate and update this
                status=Order.OrderStatus.DELIVERED # Local sales are instantly delivered
            )

            for item in items_data:
                try:
                    product = Product.objects.get(id=item['id'], store=store_profile)
                    quantity = int(item['quantity'])

                    if product.total_stock < quantity:
                         # Roll back the transaction
                        raise Exception(f"Not enough stock for {product.name}. Available: {product.total_stock}, Requested: {quantity}")

                    price = product.price # Use the current product price
                    item_total = price * quantity
                    total_amount += item_total
                    
                    # Deduct from stock
                    product.total_stock -= quantity
                    product.online_stock = min(product.online_stock, product.total_stock)
                    product.save()

                    order_items_to_create.append(
                        OrderItem(order=new_order, product=product, quantity=quantity, price=price)
                    )
                except Product.DoesNotExist:
                    raise Exception(f"Product with ID {item['id']} not found.")
                except Exception as e:
                     return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

            # Create all items and update the order's final price
            OrderItem.objects.bulk_create(order_items_to_create)
            new_order.total_amount = total_amount
            new_order.save()

        # Return the ID of the newly created order
        return Response({'order_id': new_order.id}, status=status.HTTP_201_CREATED)
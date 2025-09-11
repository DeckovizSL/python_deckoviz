from common.apps.payments.models import Transaction
from rest_framework import serializers
from common.apps.carts.models import Cart
from .models import Order,OrderDetail
from django.db import transaction

 
     
class OrderSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Order
        fields = [
            'id',
            'user',
            'billing_address',
            'shipping_address',
            'created_at',
            'updated_at',
        ]
    
    def to_representation(self, instance):
        data = super().to_representation(instance)
        return data
      
class OrderCreateSerializer(serializers.ModelSerializer):
    txn_id = serializers.CharField(write_only=True)
    ref_id = serializers.CharField(required=True, write_only=True)
    signature = serializers.CharField(required=True, write_only=True)

    class Meta:
        model = Order
        fields = [
            'id',
            'user',
            'txn_id',
            'ref_id',
            'signature',
            'billing_address',
            'shipping_address',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id', 
            'user', 
            'created_at', 
            'updated_at'
        ]
        extra_kwargs = {
            'txn_id': {'write_only': True},
            'ref_id': {'write_only': True},
            'signature': {'write_only': True},
        }
  
         
    def get_user(self, obj):
        return obj.user.username
    
    def validate(self,data):
        user = self.context['request'].user
        
        # Validate payment data together
        txn_id = data.get('txn_id')
        cart_total = sum(
            (item.price.final_price * item.quantity) 
            for item in Cart.objects.filter(user=user)
        )
        ref_id = data.get('ref_id')
        signature = data.get('signature')
        
        if not all([txn_id, ref_id, signature]):
            raise serializers.ValidationError(
                "Payment is required to place order. 'txn_id', 'ref_id' and 'signature' must be provided."
            )
            
        try:
            self.transaction_obj = Transaction.objects.get(id=txn_id) 
            if self.transaction_obj.amount - cart_total != 0:
                raise serializers.ValidationError("Transaction amount does not match cart total amount.")
            if self.transaction_obj.user != user:
                raise serializers.ValidationError("Transaction ID does not match user.")
            if self.transaction_obj.status == 'completed':
                raise serializers.ValidationError("Transaction ID already used.")
        except Transaction.DoesNotExist:
            raise serializers.ValidationError("Transaction ID does not exist.")
            
        return data
    
    def create(self, validated_data):
        user = self.context['request'].user

        billing_address = validated_data.get('billing_address',None)
        shipping_address = validated_data.get('shipping_address',None)

        # Extract payment fields from validated data
        ref_id = validated_data.pop('ref_id')
        signature = validated_data.pop('signature')

        self.transaction_obj.ref_id = ref_id
        self.transaction_obj.signature = signature
        self.transaction_obj.status = 'completed'
        self.transaction_obj.save()

        with transaction.atomic():
            order = Order.objects.create(
                user=user,
                total_amount=self.transaction_obj.amount,
                billing_address=billing_address,
                shipping_address=shipping_address,
            )
            self.transaction_obj.order = order
            self.transaction_obj.save()
            
            cart_items = Cart.objects.filter(user=user)
            for item in cart_items:
                OrderDetail.objects.create(
                    order=order,
                    image=item.image,
                    price=item.price.final_price,
                    quantity=item.quantity,
                    status=1
                )
            cart_items.delete()
            return order

    def to_representation(self, instance):
        # Delegate to OrderSerializer to avoid payment fields
        return OrderSerializer(instance, context=self.context).data



class OrderDetailSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(source='image.file')
    
    class Meta:
        model = OrderDetail
        fields = [
            'id',
            'order',
            'image',
            'price',
            'quantity',
            'status',
        ]
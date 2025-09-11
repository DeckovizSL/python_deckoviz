from rest_framework import serializers
from django.db import IntegrityError
from .models import Cart
from common.apps.gallery.serializers import ImageSerializer
from common.apps.marketplace.serializers import PriceSerializer

class CartSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()
    price = serializers.SerializerMethodField()
    
    def get_image(self, obj):
        print(obj.image.file)
        return obj.image.file.url
    
    def get_price(self, obj):
        return obj.price.final_price
    
    class Meta:
        model = Cart
        fields = [
            "id",
            "image",
            "price",
            "shipping_cost",
            "quantity",
            "created_at",
            "updated_at",
        ]
        


class CartCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Cart
        fields = [
            "id",
            "image",
            "price",
            "quantity",
        ]

    def validate(self, attrs):
        user = self.context['request'].user
        image = attrs['image'] if 'image' in attrs else None
        quantity = attrs['quantity'] if 'quantity' in attrs else None

        if image and image.uploaded_by != user and image.view != 'public' :
            raise serializers.ValidationError("Cannot add private image to cart.")

        if quantity < 1:
            raise serializers.ValidationError("Quantity must be greater than 0")
        
        if Cart.objects.filter(user=user, image=image).exists():
            raise serializers.ValidationError("Image already exists in cart.")
        
        return attrs    
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)

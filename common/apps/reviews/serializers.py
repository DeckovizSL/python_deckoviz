from common.apps.authentication.models import UserProfile
from common.apps.authentication.serializers import UserProfileSerializer
from rest_framework import serializers
from .models import Review
from django.contrib.auth import get_user_model


User = get_user_model()
 

class ReviewSerializer(serializers.ModelSerializer): 
    class Meta:
        model = Review 
        fields = [
            'id', 
            'customer',
            'customer_rating',
            'created_at', 
            'is_active',
            'comment',
        ]
        read_only_fields = [
            'created_at',
            'customer', 
        ]
    
    def create(self,validated_data):
        request = self.context['request']
        
        validated_data['customer'] = request.user
        return super().create(validated_data)  
          
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        
        if hasattr(instance,'customer') and instance.customer: 
            user_profile = UserProfile.objects.get(user__tenant=instance.customer)
            representation['customer'] = UserProfileSerializer(user_profile).data
            
        return representation
         
from common.apps.products.models import SKU, Product
from apps.reviews.filters import ReviewFilter
from common.apps.services.models import Service
from rest_framework import mixins,viewsets
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.exceptions import PermissionDenied 
from rest_framework.permissions import IsAuthenticated,AllowAny
from apps.reviews.models import (
    Review,
    )
from apps.reviews.serializers import (
    ReviewSerializer, 
    )
  
class ReviewListView(
    mixins.ListModelMixin, 
    viewsets.GenericViewSet,
    ):
    
    queryset = Review.objects.all().order_by('-created_at')
    serializer_class = ReviewSerializer
    permission_classes = [AllowAny,]
    pagination_class = LimitOffsetPagination
    filterset_class = ReviewFilter
    

class CustomerReviewView(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
    ):
    
    queryset = Review.objects.all().order_by('-created_at')
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated,]
    pagination_class = LimitOffsetPagination
    filterset_class = ReviewFilter
     
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db.models import Q
from django.utils import timezone

# Optional django-filter import
try:
    from django_filters.rest_framework import DjangoFilterBackend
    HAS_DJANGO_FILTER = True
except ImportError:
    HAS_DJANGO_FILTER = False

from .models import Holiday
from .serializers import HolidaySerializer, HolidayListSerializer


class HolidayViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Holiday management
    
    list: Get all holidays (with filtering and search) - All authenticated users
    retrieve: Get single holiday details - All authenticated users
    create: Create new holiday (Admin/Manager/HR only)
    update: Update holiday (Admin/Manager/HR only)
    destroy: Delete holiday (Admin/Manager/HR only)
    """
    queryset = Holiday.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    if HAS_DJANGO_FILTER:
        filter_backends.insert(0, DjangoFilterBackend)
    filterset_fields = [
        'country', 'region', 'holiday_type', 'is_active'
    ] if HAS_DJANGO_FILTER else []
    search_fields = ['name', 'description', 'country', 'region']
    ordering_fields = ['date', 'name', 'country', 'created_at']
    ordering = ['date', 'name']
    
    def get_permissions(self):
        """Set permissions based on action"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsAdminUser()]
        return [IsAuthenticated()]
    
    def get_serializer_class(self):
        """Use different serializers for list and detail"""
        if self.action == 'list':
            return HolidayListSerializer
        return HolidaySerializer
    
    def get_queryset(self):
        """Filter queryset based on user permissions and query parameters"""
        queryset = super().get_queryset()
        
        # Show only active holidays for non-admin users
        if not self.request.user.is_staff:
            queryset = queryset.filter(is_active=True)
        
        # Filter by year if provided
        year = self.request.query_params.get('year', None)
        if year:
            try:
                year_int = int(year)
                queryset = queryset.filter(
                    date__year=year_int
                )
            except ValueError:
                pass
        
        # Filter by date range if provided
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        if start_date:
            try:
                queryset = queryset.filter(date__gte=start_date)
            except ValueError:
                pass
        if end_date:
            try:
                queryset = queryset.filter(date__lte=end_date)
            except ValueError:
                pass
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """Get upcoming holidays"""
        today = timezone.now().date()
        holidays = self.get_queryset().filter(
            date__gte=today,
            is_active=True
        ).order_by('date')[:10]  # Next 10 holidays
        
        serializer = self.get_serializer(holidays, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_year(self, request):
        """Get holidays grouped by year"""
        year = request.query_params.get('year', None)
        if not year:
            return Response(
                {'error': 'year parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            year_int = int(year)
            holidays = self.get_queryset().filter(date__year=year_int)
            serializer = self.get_serializer(holidays, many=True)
            return Response(serializer.data)
        except ValueError:
            return Response(
                {'error': 'Invalid year format'},
                status=status.HTTP_400_BAD_REQUEST
            )


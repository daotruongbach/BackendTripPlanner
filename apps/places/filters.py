import django_filters as filters
from .models import Place

class PlaceFilter(filters.FilterSet):
    name = filters.CharFilter(field_name='name', lookup_expr='icontains')
    category = filters.CharFilter(field_name='category', lookup_expr='iexact')

    class Meta:
        model = Place
        fields = ['name', 'category']
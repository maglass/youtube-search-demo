from django.urls import path
from . import standard
from . import nori_dict
from . import expansion_indices
from . import ranking

urlpatterns = [
    path(r'', standard.search, name='search')
]

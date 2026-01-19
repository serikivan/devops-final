# project/urls.py

from django.urls import path
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from channel import views

schema_view = get_schema_view(
   openapi.Info(
      title="Channel Layer API",
      default_version='v1',
      description="API канального уровня: кодирование, передача, декодирование сегментов",
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('processSegment', views.process_segment, name='process_segment'),
    path('processAck', views.process_ack, name='process_ack'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
]

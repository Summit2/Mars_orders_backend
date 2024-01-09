from .models import Cargo
from .models import DeliveryOrders
from rest_framework import serializers
#  для преобразования в json и обратно

class CargoSerializer(serializers.ModelSerializer):
    class Meta:
        # Модель, которую мы сериализуем
        model = Cargo
        # Поля, которые мы сериализуем
        fields = ["pk", "title", "image_url", "weight", "description", 'is_deleted','image_binary'] # 

class OrdersSerializer(serializers.ModelSerializer):
    class Meta:
        # Модель, которую мы сериализуем
        model = DeliveryOrders
        # Поля, которые мы сериализуем
        fields = ["pk", "id_order", "id_user", "id_moderator", "order_status", 'date_create','date_accept', 'date_finish', 'is_delivered']
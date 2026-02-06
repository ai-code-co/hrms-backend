from rest_framework import serializers
from .models import Document

class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = '__all__'
        read_only_fields = ('isapplied', 'created_at', 'updated_at')

class DocumentApplySerializer(serializers.Serializer):
    # Used for documentation in swagger for the apply/unapply actions
    message = serializers.CharField(read_only=True)
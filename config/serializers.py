# config/serializers.py
from rest_framework import serializers

def dynamic_model_serializer(model):
    """
    Create a safe, JSON-serializable ModelSerializer dynamically.
    """

    # Only DB-backed fields (NO @property)
    field_names = [
        f.name for f in model._meta.concrete_fields
        if f.name not in {"password"}  # basic safety
    ]

    class _DynamicSerializer(serializers.ModelSerializer):
        class Meta:
            fields = field_names

    # ✅ Assign model AFTER class creation (Python rule)
    _DynamicSerializer.Meta.model = model

    return _DynamicSerializer

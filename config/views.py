# config/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status

from .table_registry import TABLE_REGISTRY
from .serializers import dynamic_model_serializer


class TableDataView(APIView):
    permission_classes = [AllowAny]  # LOCAL TESTING ONLY

    def get(self, request):
        table = request.query_params.get("table")

        if not table:
            return Response(
                {"error": "table parameter required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        model = TABLE_REGISTRY.get(table)
        if not model:
            return Response(
                {"error": "Table not allowed"},
                status=status.HTTP_400_BAD_REQUEST
            )

        qs = model.objects.all()

        SerializerClass = dynamic_model_serializer(model)
        serializer = SerializerClass(qs, many=True)

        return Response({
            "table": table,
            "count": qs.count(),
            "data": serializer.data
        })

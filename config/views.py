# config/views.py
from django.http import HttpResponse
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

def welcome_view(request):
    html = """
    <html>
        <head><title>HRMS API</title></head>
        <body style="font-family: sans-serif; display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100vh; background-color: #f0f2f5;">
            <div style="background: white; padding: 2rem; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); text-align: center;">
                <h1 style="color: #1a73e8;">HRMS Backend Live 🚀</h1>
                <p>The API is up and running.</p>
                <div style="margin-top: 1.5rem;">
                    <a href="/admin/" style="text-decoration: none; background: #1a73e8; color: white; padding: 0.5rem 1rem; border-radius: 4px; margin-right: 0.5rem;">Admin Dashboard</a>
                    <a href="/swagger/" style="text-decoration: none; background: #34a853; color: white; padding: 0.5rem 1rem; border-radius: 4px;">API Docs (Swagger)</a>
                </div>
            </div>
        </body>
    </html>
    """
    return HttpResponse(html)

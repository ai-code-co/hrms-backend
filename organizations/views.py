from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.permissions import IsAdminUser

from .models import Document
from .serializers import DocumentSerializer

class DocumentViewSet(viewsets.ModelViewSet):
    queryset = Document.objects.all().order_by('-created_at')
    serializer_class = DocumentSerializer
    permission_classes = [IsAdminUser]

    def get_permissions(self):
        # You can add custom permission logic here 
        # (e.g., only staff can create/delete)
        return super().get_permissions()

    @swagger_auto_schema(
        operation_description="Create a new policy document",
        responses={201: DocumentSerializer()}
    )
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"error": 0, "data": serializer.data}, status=status.HTTP_201_CREATED)
        return Response({"error": 1, "message": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_description="Get list of all policy documents",
        responses={200: DocumentSerializer(many=True)}
    )
    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return Response({"error": 0, "data": response.data})

    @swagger_auto_schema(
        operation_description="Apply a policy document",
        responses={200: openapi.Response("Policy applied successfully")}
    )
    @action(detail=True, methods=['post'], url_path='apply')
    def apply_policy(self, request, pk=None):
        document = self.get_object()
        document.isapplied = True
        document.save()
        return Response({
            "error": 0, 
            "message": f"Document '{document.documentname}' has been applied.",
            "data": DocumentSerializer(document).data
        })

    @swagger_auto_schema(
        operation_description="Unapply a policy document",
        responses={200: openapi.Response("Policy unapplied successfully")}
    )
    @action(detail=True, methods=['post'], url_path='unapply')
    def unapply_policy(self, request, pk=None):
        document = self.get_object()
        document.isapplied = False
        document.save()
        return Response({
            "error": 0, 
            "message": f"Document '{document.documentname}' has been unapplied.",
            "data": DocumentSerializer(document).data
        })

    @swagger_auto_schema(
        operation_description="Delete a policy document",
        responses={204: openapi.Response("Deleted")}
    )
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({"error": 0, "message": "Document deleted successfully"}, status=status.HTTP_200_OK)
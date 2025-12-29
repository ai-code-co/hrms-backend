from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.parsers import MultiPartParser, FormParser
from django.core.files.storage import default_storage
from django.conf import settings
import os
import uuid
from datetime import datetime


class ImageUploadView(APIView):
    """
    Generic image upload endpoint.
    POST /auth/upload-image/
    
    Upload any image and get a public URL.
    
    Request: multipart/form-data with 'image' field
    Response: { "success": true, "url": "...", "filename": "..." }
    """
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    def post(self, request):
        """Upload image and return URL"""
        image = request.FILES.get('image')
        
        if not image:
            return Response(
                {
                    "success": False,
                    "error": "No image file provided"
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate file type
        allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp', 'image/gif']
        if image.content_type not in allowed_types:
            return Response(
                {
                    "success": False,
                    "error": "Invalid file type. Allowed: JPEG, PNG, WebP, GIF"
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate file size (max 10MB)
        max_size = 10 * 1024 * 1024  # 10MB
        if image.size > max_size:
            return Response(
                {
                    "success": False,
                    "error": "File too large. Maximum size is 10MB"
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Generate unique filename
        ext = os.path.splitext(image.name)[1]  # Get file extension
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_id = uuid.uuid4().hex[:8]
        filename = f"{timestamp}_{unique_id}{ext}"
        
        # Save to uploads directory
        file_path = f'uploads/{filename}'
        saved_path = default_storage.save(file_path, image)
        
        # Generate full URL
        file_url = request.build_absolute_uri(settings.MEDIA_URL + saved_path)
        
        return Response({
            "success": True,
            "message": "Image uploaded successfully",
            "url": file_url,
            "filename": filename,
            "size": image.size,
            "content_type": image.content_type
        }, status=status.HTTP_200_OK)

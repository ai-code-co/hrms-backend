from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.parsers import MultiPartParser, FormParser
import cloudinary
import cloudinary.uploader
from django.conf import settings
import os


class ImageUploadView(APIView):
    """
    Generic image upload endpoint using Cloudinary.
    POST /auth/upload-image/
    
    Upload any image and get a permanent public URL from Cloudinary.
    
    Request: multipart/form-data with 'image' field
    Response: { "success": true, "url": "https://res.cloudinary.com/...", "filename": "..." }
    """
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    def post(self, request):
        """Upload image to Cloudinary and return permanent URL"""
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
        
        try:
            # Configure Cloudinary
            cloudinary.config(
                cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME', 'dhlyvqdoi'),
                api_key=os.getenv('CLOUDINARY_API_KEY', '857684152783841'),
                api_secret=os.getenv('CLOUDINARY_API_SECRET', 'dcrgV5kMzlR42aoh9I6h1qzIG00')
            )
            
            # Upload to Cloudinary
            upload_result = cloudinary.uploader.upload(
                image,
                folder="hrms/uploads",  # Organize in folder
                resource_type="image",
                format=image.name.split('.')[-1] if '.' in image.name else 'jpg'
            )
            
            # Get the secure URL
            file_url = upload_result.get('secure_url')
            public_id = upload_result.get('public_id')
            
            return Response({
                "success": True,
                "message": "Image uploaded successfully to Cloudinary",
                "url": file_url,
                "public_id": public_id,
                "filename": os.path.basename(public_id),
                "size": image.size,
                "content_type": image.content_type
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                "success": False,
                "error": f"Upload failed: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class FileUploadView(APIView):
    """
    Generic file upload endpoint using Cloudinary.
    POST /auth/upload-file/
    
    Upload any file (image, PDF, docx) and get a permanent public URL.
    
    Request: multipart/form-data with 'file' field
    Response: { "success": true, "url": "...", "public_id": "...", "resource_type": "..." }
    """
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    def post(self, request):
        """Upload file to Cloudinary and return permanent URL"""
        file_obj = request.FILES.get('file')
        
        if not file_obj:
            return Response(
                {"success": False, "error": "No file provided"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate file size (max 20MB for docs)
        max_size = 20 * 1024 * 1024
        if file_obj.size > max_size:
            return Response(
                {"success": False, "error": "File too large. Maximum size is 20MB"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Determine resource type
        content_type = file_obj.content_type
        resource_type = "image" if content_type.startswith('image/') else "raw"
        
        try:
            # Configure Cloudinary
            cloudinary.config(
                cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME', 'dhlyvqdoi'),
                api_key=os.getenv('CLOUDINARY_API_KEY', '857684152783841'),
                api_secret=os.getenv('CLOUDINARY_API_SECRET', 'dcrgV5kMzlR42aoh9I6h1qzIG00')
            )
            
            # Upload to Cloudinary
            upload_result = cloudinary.uploader.upload(
                file_obj,
                folder="hrms/documents",
                resource_type=resource_type,
                original_filename=True
            )
            
            return Response({
                "success": True,
                "message": "File uploaded successfully",
                "url": upload_result.get('secure_url'),
                "public_id": upload_result.get('public_id'),
                "resource_type": resource_type,
                "filename": file_obj.name,
                "size": file_obj.size,
                "content_type": content_type
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                "success": False,
                "error": f"Upload failed: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

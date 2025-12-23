import json
import threading
import logging
import requests
from django.http import JsonResponse, HttpResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.parsers import JSONParser, FormParser, MultiPartParser
from leaves.models import Leave
# Note: Timesheet import removed as the attendance app was deleted.
# We will skip timesheet actions in the check.

import datetime
from django.utils import timezone

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name="dispatch")
class SlackInteractionsView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    parser_classes = [FormParser, JSONParser, MultiPartParser]

    def get(self, request, *args, **kwargs):
        return HttpResponse("🚀 Slack Interaction Endpoint is Active! Path: " + request.path)

    def post(self, request, *args, **kwargs):
        log_entry = f"\n--- {timezone.now()} ---\nPath: {request.path}\nData: {request.data}\n"
        print("🔥 SLACK HIT THIS ENDPOINT 🔥")
        try:
            with open("slack_debug.log", "a") as f:
                f.write(log_entry)
        except:
            pass
        # 🔐 URL verification
        if request.data.get("type") == "url_verification":
            return JsonResponse({"challenge": request.data.get("challenge")})

        payload_str = request.data.get("payload")

        # 🔥 ACK SLACK IMMEDIATELY (CRITICAL)
        response = HttpResponse("OK")

        if not payload_str:
            return response  # still ACK

        payload = json.loads(payload_str)

        # Process async (Slack-safe)
        threading.Thread(
            target=self.process_action,
            args=(payload,),
            daemon=True
        ).start()

        return response

    def process_action(self, payload):
        try:
            actions = payload.get("actions", [])
            if not actions:
                return

            action = actions[0]
            action_id = action.get("action_id")
            value = action.get("value")
            response_url = payload.get("response_url")
            user_name = payload.get("user", {}).get("name", "Admin")

            if action_id == "approve_leave":
                leave_id = value.replace("approve_leave_", "")
                leave = Leave.objects.get(id=leave_id)
                leave.status = Leave.Status.APPROVED
                leave.save(update_fields=["status"])
                message = f"✅ Leave approved by @{user_name}"

            elif action_id == "reject_leave":
                leave_id = value.replace("reject_leave_", "")
                leave = Leave.objects.get(id=leave_id)
                leave.status = Leave.Status.REJECTED
                leave.save(update_fields=["status"])
                message = f"❌ Leave rejected by @{user_name}"

            elif action_id == "approve_timesheet" or action_id == "reject_timesheet":
                # Attendance app was deleted, so we can't process these yet.
                message = "⌛ Timesheet processing is currently disabled (Attendance app missing)."

            else:
                return

            if response_url:
                requests.post(
                    response_url,
                    json={"text": message, "replace_original": True},
                    timeout=2
                )

        except Exception as e:
            logger.error(f"Slack interaction error: {e}")

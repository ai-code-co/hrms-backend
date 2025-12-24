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
        log_entry = f"\n--- {timezone.now()} ---\nPath: {request.path}\nMethod: {request.method}\nData: {request.data}\nHeaders: {dict(request.headers)}\n"
        print(f"🔥 SLACK HIT: {request.path}")
        try:
            with open("slack_debug.log", "a") as f:
                f.write(log_entry)
        except Exception as e:
            print(f"Logging error: {e}")
        if request.data.get("type") == "url_verification":
            return JsonResponse({"challenge": request.data.get("challenge")})

        # 🔥 ACK SLACK IMMEDIATELY (CRITICAL)
        response = HttpResponse("OK")

        # Slack sends events directly in request.data
        # Slack sends interactive payloads (buttons) in a 'payload' form field
        payload_str = request.data.get("payload")
        
        if payload_str:
            payload = json.loads(payload_str)
            target_method = self.process_action
        else:
            payload = request.data
            target_method = self.process_event

        if not payload:
            return response

        # Process async (Slack-safe)
        threading.Thread(
            target=target_method,
            args=(payload,),
            daemon=True
        ).start()

        return response

    def process_event(self, payload):
        """ Handles Slack Event API (e.g. messages) """
        try:
            event_type = payload.get("type")
            if event_type != "event_callback":
                return
            
            event = payload.get("event", {})
            msg_type = event.get("type")
            
            if msg_type == "message":
                text = event.get("text", "")
                slack_user_id = event.get("user")
                ts = float(event.get("ts", 0))
                
                if not text or not slack_user_id:
                    return
                
                # Check for keywords
                field_map = {
                    "#standup": "standup_time",
                    "#report": "report_time",
                    "#lunchstart": "lunch_start_time",
                    "#lunchend": "lunch_end_time"
                }
                
                target_field = None
                for keyword, field in field_map.items():
                    if keyword in text.lower():
                        target_field = field
                        break
                
                if target_field:
                    from employees.models import Employee
                    from attendance.models import Attendance
                    from datetime import datetime, timezone as dt_timezone
                    
                    employee = Employee.objects.filter(slack_user_id=slack_user_id).first()
                    if employee:
                        event_dt = datetime.fromtimestamp(ts, tz=dt_timezone.utc)
                        attendance, created = Attendance.objects.get_or_create(
                            employee=employee,
                            date=event_dt.date()
                        )
                        setattr(attendance, target_field, event_dt)
                        attendance.save()
                        logger.info(f"Updated {target_field} for {employee.get_full_name()} via Slack.")
                    else:
                        logger.warning(f"No employee found with Slack ID: {slack_user_id}. Please link the Slack ID in the Employee profile.")

        except Exception as e:
            logger.error(f"Slack event processing error: {e}")

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

            elif action_id in ["approve_manual", "reject_manual", "approve_less_manual"]:
                from attendance.models import ManualAttendanceRequest, Attendance
                from datetime import datetime, timedelta

                req_id = value.split("_")[-1]
                req = ManualAttendanceRequest.objects.get(id=req_id)
                
                if action_id == "reject_manual":
                    req.status = 'rejected'
                    req.save(update_fields=['status'])
                    message = f"❌ Manual request rejected by @{user_name}"
                else:
                    req.status = 'approved'
                    req.save(update_fields=['status'])
                    
                    # Sync with Attendance model
                    # Combine date and time to aware datetime
                    entry_dt = timezone.make_aware(datetime.combine(req.date, req.entry_time))
                    exit_dt = timezone.make_aware(datetime.combine(req.date, req.exit_time))
                    
                    if action_id == "approve_less_manual":
                        # Subtract 15 minutes from exit time
                        exit_dt = exit_dt - timedelta(minutes=15)
                        message = f"✅ Manual request approved with 15 mins less by @{user_name}"
                    else:
                        message = f"✅ Manual request approved by @{user_name}"

                    # Update or Create Attendance
                    attendance, created = Attendance.objects.get_or_create(
                        employee=req.employee,
                        date=req.date
                    )
                    attendance.office_in_time = entry_dt
                    attendance.office_out_time = exit_dt
                    attendance.day_type = 'WORKING_DAY'
                    attendance.text = f"Manual adjustment: {req.reason}"
                    attendance.save()

            elif action_id == "approve_timesheet":
                from attendance.models import Timesheet
                ts_id = value.replace("approve_timesheet_", "")
                ts = Timesheet.objects.get(id=ts_id)
                ts.status = 'approved'
                ts.save(update_fields=['status'])
                message = f"✅ Timesheet approved by @{user_name}"

            elif action_id == "reject_timesheet":
                from attendance.models import Timesheet
                ts_id = value.replace("reject_timesheet_", "")
                ts = Timesheet.objects.get(id=ts_id)
                ts.status = 'rejected'
                ts.save(update_fields=['status'])
                message = f"❌ Timesheet rejected by @{user_name}"

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

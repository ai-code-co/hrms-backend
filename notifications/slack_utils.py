import os
import logging
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from django.conf import settings
from employees.models import Employee

logger = logging.getLogger(__name__)

class SlackNotificationService:
    def __init__(self):
        self.client = WebClient(token=os.environ.get('SLACK_BOT_TOKEN'))
        self.management_channel = os.environ.get('SLACK_MANAGEMENT_CHANNEL_ID')

    def get_management_channel_id(self):
        return self.management_channel

    def get_slack_id_by_email(self, email):
        """
        Looks up a Slack User ID by their email address.
        """
        try:
            response = self.client.users_lookupByEmail(email=email)
            if response["ok"]:
                return response["user"]["id"]
        except SlackApiError as e:
            logger.error(f"Error looking up Slack user by email {email}: {e.response['error']}")
        return None

    def get_or_set_slack_id(self, employee):
        """
        Gets the slack_user_id from the employee model or fetches and saves it if missing.
        """
        if employee.slack_user_id:
            return employee.slack_user_id
        
        slack_id = self.get_slack_id_by_email(employee.email)
        if slack_id:
            employee.slack_user_id = slack_id
            employee.save(update_fields=['slack_user_id'])
            return slack_id
        return None

    def send_message(self, employee_or_channel, message_text, blocks=None):
        """
        Sends a message to an employee (DM) or a specific channel ID.
        Supports rich text blocks for interactive components.
        """
        if isinstance(employee_or_channel, str):
            target_id = employee_or_channel
        else:
            target_id = self.get_or_set_slack_id(employee_or_channel)

        if not target_id:
            logger.warning(f"No target ID found for message.")
            return False

        try:
            self.client.chat_postMessage(
                channel=target_id,
                text=message_text,
                blocks=blocks
            )
            return True
        except SlackApiError as e:
            logger.error(f"Error sending Slack message: {e.response['error']}")
            return False

    def notify_management(self, message_text, blocks=None):
        """ Sends a message to the pre-configured management channel. """
        if not self.management_channel:
            logger.warning("SLACK_MANAGEMENT_CHANNEL_ID not configured.")
            return False
        return self.send_message(self.management_channel, message_text, blocks=blocks)

    @staticmethod
    def notify_attendance_approval(employee, date, status="Approved"):
        """ Hi @Name, Your timesheet entry for Date has been status """
        service = SlackNotificationService()
        message = f"Hi {employee.first_name}\n Your timesheet entry for {date} has been {status}"
        return service.send_message(employee, message)

    @staticmethod
    def notify_leave_applied(employee, leave_obj):
        """ Hi @Name !! You just had applied for X days of leave from Start to End ... """
        service = SlackNotificationService()
        message = (
            f"Hi {employee.first_name} !!\n"
            f" You just had applied for {leave_obj.no_of_days} days of leave from {leave_obj.from_date} to {leave_obj.to_date} .\n"
            f" Reason mentioned : {leave_obj.reason}\n"
            f" Alert : N/A\n"
            f" Late Reason: {getattr(leave_obj, 'late_reason', 'N/A') or 'N/A'}\n"
            f" Document: {'Available' if leave_obj.doc_link else 'N/A'}"
        )
        return service.send_message(employee, message)

    @staticmethod
    def notify_leave_status(employee, leave_obj, status_msg="Approved"):
        """ Hi @Name !! Your leave has been Approved . """
        service = SlackNotificationService()
        message = (
            f"Hi {employee.first_name} !!\n"
            f" Your leave has been {status_msg} .\n"
            f" Leave Details :\n"
            f" From:  {leave_obj.from_date}\n"
            f" To:  {leave_obj.to_date} .\n"
            f" No. of days: {leave_obj.no_of_days}\n"
            f" Applied on: {leave_obj.created_at.date()}\n"
            f" Reason: {leave_obj.reason}\n"
            f" Message from Admin: {getattr(leave_obj, 'rejection_reason', 'N/A') or 'N/A'}"
        )
        return service.send_message(employee, message)

    @staticmethod
    def notify_payslip_generated(employee, month_name):
        """ Hi @Name, Your salary slip is generated for month of Month . """
        service = SlackNotificationService()
        message = (
            f"Hi {employee.first_name}\n"
            f" Your salary slip is generated for month of {month_name} .\n"
            f" Please check your office email for salary details."
        )
        return service.send_message(employee, message)

    @staticmethod
    def notify_attendance_update(employee, date, entry_time, exit_time, reason="N/A"):
        """ Hi @Name, Your timings are updated for date Date ... """
        service = SlackNotificationService()
        message = (
            f"Hi {employee.first_name}\n"
            f" Your timings are updated for date {date}\n"
            f" Entry Time - {entry_time}\n"
            f" Exit Time - {exit_time}\n"
            f" Reason: {reason}"
        )
        return service.send_message(employee, message)

    @staticmethod
    def notify_daily_attendance(employee, prev_entry, prev_exit, today_entry):
        """ Hi @Name, Your Previous working day Entry Time: ... """
        service = SlackNotificationService()
        message = (
            f"Hi {employee.first_name}\n"
            f"Your Previous working day Entry Time: {prev_entry}\n"
            f"Your Previous working day Exit Time: {prev_exit}\n"
            f"Today's Entry Time {today_entry} ."
        )
        return service.send_message(employee, message)

    @staticmethod
    def notify_missing_attendance(employee, date=None):
        """ Hi @Name, You have not entered time Today . """
        service = SlackNotificationService()
        if date:
            message = f"Hi {employee.first_name}\nYou didn't put your Entry/Exit Time on {date}\nYou have not entered time Today ."
        else:
            message = f"Hi {employee.first_name}\nYou have not entered time Today ."
        return service.send_message(employee, message)

    @staticmethod
    def notify_management_leave_request(leave_obj):
        """ Sends interactive leave request to management channel. """
        service = SlackNotificationService()
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        f"🚨 *New Leave Request*\n"
                        f"*Employee:* {leave_obj.employee.get_full_name()}\n"
                        f"*Dates:* {leave_obj.from_date} to {leave_obj.to_date} ({leave_obj.no_of_days} days)\n"
                        f"*Reason:* {leave_obj.reason}"
                    )
                }
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Approve ✅"},
                        "style": "primary",
                        "value": f"approve_leave_{leave_obj.id}",
                        "action_id": "approve_leave"
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Reject ❌"},
                        "style": "danger",
                        "value": f"reject_leave_{leave_obj.id}",
                        "action_id": "reject_leave"
                    }
                ]
            }
        ]
        return service.notify_management("New Leave Request Received", blocks=blocks)

    @staticmethod
    def notify_management_timesheet_request(timesheet_obj):
        """ Sends interactive timesheet request to management channel. """
        service = SlackNotificationService()
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        f"📋 *New Timesheet Submission*\n"
                        f"*Employee:* {timesheet_obj.employee.get_full_name()}\n"
                        f"*Date:* {timesheet_obj.date}\n"
                        f"*Hours:* {timesheet_obj.hours}\n"
                        f"*Description:* {timesheet_obj.description}"
                    )
                }
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Approve ✅"},
                        "style": "primary",
                        "value": f"approve_timesheet_{timesheet_obj.id}",
                        "action_id": "approve_timesheet"
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Reject ❌"},
                        "style": "danger",
                        "value": f"reject_timesheet_{timesheet_obj.id}",
                        "action_id": "reject_timesheet"
                    }
                ]
            }
        ]
        return service.notify_management("New Timesheet Submitted", blocks=blocks)

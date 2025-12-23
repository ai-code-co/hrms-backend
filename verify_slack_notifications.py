import os
import django
import logging
from decimal import Decimal
from datetime import date, timedelta

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from employees.models import Employee
from leaves.models import Leave
from notifications.slack_utils import SlackNotificationService

# Configure logging to be clean
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class SlackIntegrationTester:
    def __init__(self, email):
        self.email = email
        self.employee = None
        self.notification_service = SlackNotificationService()

    def setup(self):
        """Verify employee exists and Slack token is present."""
        print("\n--- 🛠️  Phase 1: Environment Check ---")
        
        # Check Slack Token
        token = os.environ.get('SLACK_BOT_TOKEN')
        if not token:
            print("❌ Error: SLACK_BOT_TOKEN is missing from .env")
            return False
        print("✅ Slack Bot Token: Found")

        # Find Employee
        self.employee = Employee.objects.filter(email=self.email).first()
        if not self.employee:
            print(f"❌ Error: No employee found with email: {self.email}")
            return False
        print(f"✅ Target User: {self.employee.get_full_name()} ({self.email})")
        return True

    def test_leave_application(self):
        """Tests the triggers for applying a new leave."""
        print("\n--- 📝 Phase 2: Leave Application (Employee -> Boss) ---")
        
        # Create a test leave
        try:
            leave = Leave.objects.create(
                employee=self.employee,
                leave_type=Leave.LeaveType.CASUAL_LEAVE,
                from_date=date.today() + timedelta(days=10),
                to_date=date.today() + timedelta(days=12),
                no_of_days=Decimal('3.0'),
                reason="Auto-generated test for Slack Notification",
                status=Leave.Status.PENDING
            )
            print(f"✅ Leave Applied (ID: {leave.id})")
            print("📬 Logic: Signals should have sent:")
            print("   1. Private DM to you (@medhavi)")
            print("   2. Interactive Alert (with Buttons) to Management Channel")
            return leave
        except Exception as e:
            print(f"❌ Failed to create leave: {e}")
            return None

    def test_leave_approval(self, leave):
        """Simulates an approval action to test the student notification."""
        print("\n--- ✅ Phase 3: Leave Approval (Boss -> Employee) ---")
        
        try:
            leave.status = Leave.Status.APPROVED
            # update_fields is important to trigger the specific signal check
            leave.save(update_fields=['status'])
            print(f"✅ Leave Status updated to: {leave.status}")
            print("📬 Logic: Signal should have sent a DM to you confirming approval.")
            return True
        except Exception as e:
            print(f"❌ Failed to update leave status: {e}")
            return False

def run_test():
    tester = SlackIntegrationTester('medhavisharma11apr@gmail.com')
    
    if not tester.setup():
        return

    # Trigger Leave Applied notification
    test_leave = tester.test_leave_application()
    
    if test_leave:
        # Trigger Leave Approved notification
        input("\nPress Enter to simulate Boss Approving this leave...")
        tester.test_leave_approval(test_leave)
        
    print("\n--- ✨ Test Complete ---")
    print("If you didn't receive messages, please check:")
    print("1. Is the Bot invited to the Management Channel?")
    print("2. Is your Slack Email exactly 'medhavisharma11apr@gmail.com'?")

if __name__ == "__main__":
    run_test()

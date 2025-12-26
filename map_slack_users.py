import os
import django
import logging

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from employees.models import Employee
from notifications.models import SlackConfiguration
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def map_users():
    configs = SlackConfiguration.objects.all()
    if not configs.exists():
        logger.warning("No Slack configurations found in database.")
        return

    for config in configs:
        logger.info(f"Processing company: {config.company.name} (Team ID: {config.slack_team_id})")
        client = WebClient(token=config.bot_token)
        
        try:
            # Method 2: Lookup each employee by email (requires users:read.email scope)
            employees = Employee.objects.filter(company=config.company)
            updated_count = 0
            for emp in employees:
                if not emp.email:
                    logger.warning(f"⏩ Skipping {emp.get_full_name()} (No email)")
                    continue
                
                try:
                    result = client.users_lookupByEmail(email=emp.email)
                    slack_id = result['user']['id']
                    if emp.slack_user_id != slack_id:
                        emp.slack_user_id = slack_id
                        emp.save(update_fields=['slack_user_id'])
                        logger.info(f"✅ Mapped {emp.get_full_name()} -> {slack_id}")
                        updated_count += 1
                    else:
                        logger.info(f"ℹ️ Already mapped {emp.get_full_name()} -> {slack_id}")
                except SlackApiError as e:
                    if e.response['error'] == 'users_not_found':
                        logger.warning(f"❌ No Slack user found for {emp.get_full_name()} ({emp.email})")
                    else:
                        logger.error(f"Error for {emp.get_full_name()}: {e.response['error']}")
            
            logger.info(f"Done for {config.company.name}: Updated {updated_count} employees.")

        except SlackApiError as e:
            logger.error(f"Error fetching users for {config.company.name}: {e.response['error']}")

if __name__ == "__main__":
    map_users()

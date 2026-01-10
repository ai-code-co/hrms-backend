
from datetime import timedelta
from holidays.models import Holiday

def calculate_working_days(from_date, to_date):
    """
    Calculates the number of working days between two dates, 
    excluding weekends (Saturday and Sunday) and active holidays.
    """
    if not from_date or not to_date:
        return 0
        
    if from_date > to_date:
        return 0
        
    # Fetch holidays in range
    holidays_in_range = Holiday.objects.filter(
        date__range=[from_date, to_date], 
        is_active=True
    ).values_list('date', flat=True)
    
    current_date = from_date
    working_days = 0
    
    while current_date <= to_date:
        # Check for Weekend (Sat=5, Sun=6)
        is_weekend = current_date.weekday() in [5, 6]
        is_holiday = current_date in holidays_in_range
        
        if not is_weekend and not is_holiday:
            working_days += 1
            
        current_date += timedelta(days=1)
        
    return working_days

from django.test import TestCase
from django.utils import timezone
from .models import Holiday


class HolidayModelTest(TestCase):
    """Test cases for Holiday model"""
    
    def setUp(self):
        """Set up test data"""
        self.holiday = Holiday.objects.create(
            name="Test Holiday",
            date=timezone.now().date(),
            country="India",
            holiday_type="national"
        )
    
    def test_holiday_creation(self):
        """Test holiday creation"""
        self.assertEqual(self.holiday.name, "Test Holiday")
        self.assertEqual(self.holiday.country, "India")
        self.assertTrue(self.holiday.is_active)
    
    def test_holiday_str(self):
        """Test holiday string representation"""
        expected = f"{self.holiday.name} ({self.holiday.date})"
        self.assertEqual(str(self.holiday), expected)



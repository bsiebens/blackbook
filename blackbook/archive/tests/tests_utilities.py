from django.test import TestCase

from datetime import date

from .. import utilities


class CalculatePeriodTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.start_date = date(2020, 8, 15)

    def test_day_period(self):
        dates = utilities.calculate_period("day", start_date=self.start_date)

        self.assertEqual(dates["start_date"], self.start_date)
        self.assertEqual(dates["end_date"], self.start_date)

    def test_week_period(self):
        dates = utilities.calculate_period("week", start_date=self.start_date)

        self.assertEqual(dates["start_date"], date(2020, 8, 10))
        self.assertEqual(dates["end_date"], date(2020, 8, 16))

    def test_month_period(self):
        dates = utilities.calculate_period("month", start_date=self.start_date)

        self.assertEqual(dates["start_date"], date(2020, 8, 1))
        self.assertEqual(dates["end_date"], date(2020, 8, 31))

    def test_quarter_period(self):
        dates = utilities.calculate_period("quarter", start_date=self.start_date)

        self.assertEqual(dates["start_date"], date(2020, 7, 1))
        self.assertEqual(dates["end_date"], date(2020, 9, 30))

    def test_half_year_period(self):
        dates = utilities.calculate_period("half_year", start_date=self.start_date)

        self.assertEqual(dates["start_date"], date(2020, 7, 1))
        self.assertEqual(dates["end_date"], date(2020, 12, 31))

    def test_year_period(self):
        dates = utilities.calculate_period("year", start_date=self.start_date)

        self.assertEqual(dates["start_date"], date(2020, 1, 1))
        self.assertEqual(dates["end_date"], date(2020, 12, 31))


class FormatIBANFieldTest(TestCase):
    def test_iban_formatting(self):
        value = "BE12345678901234"

        self.assertEqual(utilities.format_iban(value), "BE12 3456 7890 1234")
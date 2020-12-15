from django.test import TestCase
from django.contrib.auth import get_user_model
from django.conf import settings
from django.utils import timezone

from djmoney.money import Money
from djmoney.contrib.exchange.models import convert_money

from datetime import timedelta

from .. import models
from ..utilities import calculate_period


class BaseUtilitiesTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user("Test User", "test@siebens.org", "ThisIsATestUser88")

        cls.user.userprofile.default_currency = "SEK"
        cls.user.userprofile.save()

    def test_get_default_value_no_user(self):
        self.assertEqual(models.get_default_value("default_currency", "DKK"), getattr(settings, "DEFAULT_CURRENCY"))
        self.assertEqual(models.get_default_value("default_something", "I don't know"), "I don't know")
        self.assertEqual(models.get_default_value("default_something"), None)

    def test_get_default_value_for_user(self):
        self.assertEqual(models.get_default_value("default_currency", "DKK", user=self.user), "SEK")
        self.assertEqual(models.get_default_value("default_something", "I don't know", user=self.user), "I don't know")
        self.assertEqual(models.get_default_value("default_something", user=self.user), None)


class UserProfileTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user("Test User", "test@siebens.org", "ThisIsATestUser88")

    def test_userprofile_created(self):
        self.assertIsInstance(self.user.userprofile, models.UserProfile)

    def test_user_save(self):
        timestamp_pre = self.user.userprofile.modified
        self.user.save()

        self.assertEqual(self.user.userprofile.modified, timestamp_pre)


class BudgetTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user("Test User", "test@siebens.org", "ThisIsATestUser88")

    def test_period_created(self):
        budget = models.Budget.objects.create(name="Test Budget", amount=Money(20, "EUR"), user=self.user)
        self.assertEqual(budget.current_period, None)

        budget = models.Budget.objects.create(
            name="Test Budget With Period", auto_budget=models.Budget.AutoBudget.ADD, auto_budget_period=models.Budget.Period.WEEK, user=self.user
        )
        self.assertIsInstance(budget.current_period, models.BudgetPeriod)
        self.assertEqual(budget.current_period.amount, budget.amount)

    def test_period_after_save(self):
        budget = models.Budget.objects.create(
            name="Test Budget With Period", auto_budget=models.Budget.AutoBudget.ADD, auto_budget_period=models.Budget.Period.WEEK, user=self.user
        )

        pre_timestamp = budget.current_period.modified
        budget.save()

        self.assertEqual(budget.current_period.modified, pre_timestamp)

    def test_period_change_amount(self):
        budget = models.Budget.objects.create(
            name="Test Budget With Period", auto_budget=models.Budget.AutoBudget.ADD, auto_budget_period=models.Budget.Period.WEEK, user=self.user
        )

        budget.amount = Money(100, "EUR")
        budget.save()
        self.assertEqual(budget.current_period.amount, Money(100, "EUR"))

    def test_period_change_period(self):
        budget = models.Budget.objects.create(
            name="Test Budget With Period", auto_budget=models.Budget.AutoBudget.ADD, auto_budget_period=models.Budget.Period.WEEK, user=self.user
        )

        period = calculate_period(periodicity=models.Budget.Period.MONTH)
        budget.auto_budget_period = models.Budget.Period.MONTH
        budget.save()

        self.assertEqual(budget.current_period.start_date, period["start_date"])
        self.assertEqual(budget.current_period.end_date, period["end_date"])
        self.assertEqual(budget.current_period.amount, budget.amount)

        self.assertEqual(budget.get_periods().count(), 2)


class AccountBudgetCategoryTransactionTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user("Test User", "test@siebens.org", "ThisIsATestUser88")

        from djmoney.contrib.exchange.backends import OpenExchangeRatesBackend

        OpenExchangeRatesBackend().update_rates()

        cls.account = models.Account.objects.create(
            name="Account 1", account_type=models.AccountType.objects.all().first(), currency="EUR", user=cls.user
        )
        cls.budget_EUR = models.Budget.objects.create(
            name="Budget 1",
            amount=Money(200, "EUR"),
            auto_budget=models.Budget.AutoBudget.ADD,
            auto_budget_period=models.Budget.Period.WEEK,
            user=cls.user,
        )
        cls.budget_DKK = models.Budget.objects.create(
            name="Budget 2",
            amount=Money(2000, "DKK"),
            auto_budget=models.Budget.AutoBudget.ADD,
            auto_budget_period=models.Budget.Period.WEEK,
            user=cls.user,
        )
        cls.budget_no = models.Budget.objects.create(
            name="Budget 3", amount=Money(200, "EUR"), auto_budget=models.Budget.AutoBudget.NO, user=cls.user
        )
        cls.category = models.Category.objects.create(name="Category 1", user=cls.user)

        models.TransactionJournalEntry.create_transaction(
            amount=Money(10, "EUR"),
            description="Transaction 1",
            transaction_type=models.TransactionJournalEntry.TransactionType.WITHDRAWAL,
            category=cls.category,
            budget=cls.budget_EUR,
            from_account=cls.account,
            user=cls.user,
        )
        models.TransactionJournalEntry.create_transaction(
            amount=Money(10, "EUR"),
            description="Transaction 2",
            transaction_type=models.TransactionJournalEntry.TransactionType.WITHDRAWAL,
            category=cls.category,
            budget=cls.budget_DKK,
            from_account=cls.account,
            user=cls.user,
        )
        models.TransactionJournalEntry.create_transaction(
            amount=Money(10, "EUR"),
            description="Transaction 3",
            transaction_type=models.TransactionJournalEntry.TransactionType.WITHDRAWAL,
            category=cls.category,
            budget=cls.budget_EUR,
            from_account=cls.account,
            user=cls.user,
        )
        models.TransactionJournalEntry.create_transaction(
            amount=Money(15, "EUR"),
            description="Transaction 4",
            transaction_type=models.TransactionJournalEntry.TransactionType.DEPOSIT,
            budget=cls.budget_EUR,
            to_account=cls.account,
            user=cls.user,
        )
        models.TransactionJournalEntry.create_transaction(
            amount=Money(50, "EUR"),
            description="Transaction 5",
            transaction_type=models.TransactionJournalEntry.TransactionType.WITHDRAWAL,
            date=timezone.now() - timedelta(days=10),
            budget=cls.budget_EUR,
            from_account=cls.account,
            user=cls.user,
        )
        cls.tag_transaction_1 = models.TransactionJournalEntry.create_transaction(
            amount=Money(50, "EUR"),
            description="Transaction 6",
            transaction_type=models.TransactionJournalEntry.TransactionType.WITHDRAWAL,
            budget=cls.budget_no,
            from_account=cls.account,
            tags="tag 1, tag 2",
            user=cls.user,
        )
        cls.tag_transaction_2 = models.TransactionJournalEntry.create_transaction(
            amount=Money(50, "EUR"),
            description="Transaction 7",
            transaction_type=models.TransactionJournalEntry.TransactionType.DEPOSIT,
            budget=cls.budget_no,
            to_account=cls.account,
            tags=["tag 1", "tag 2"],
            user=cls.user,
        )

    def category_test_total(self):
        self.assertEqual(self.category.total, Money(-30, models.get_default_currency()))

    def category_test_total_in_currency(self):
        self.assertEqual(self.category.total_in_currency("DKK"), convert_money(Money(-30, models.get_default_currency())))

    def test_tags(self):
        self.assertListEqual(["tag 1", "tag 2"], [tag.name for tag in self.tag_transaction_1.tags.all().order_by("name")])
        self.assertListEqual(["tag 1", "tag 2"], [tag.name for tag in self.tag_transaction_2.tags.all().order_by("name")])

    def test_budget_used(self):
        self.assertEqual(self.budget_EUR.used, Money(20, "EUR"))
        self.assertEqual(self.budget_DKK.used, convert_money(Money(10, "EUR"), "DKK"))
        self.assertEqual(self.budget_no.used, Money(50, "EUR"))

    def test_budget_available(self):
        self.assertEqual(self.budget_EUR.available, Money(180, "EUR"))
        self.assertEqual(self.budget_DKK.available, Money(2000, "DKK") - convert_money(Money(10, "EUR"), "DKK"))
        self.assertEqual(self.budget_no.available, Money(150, "EUR"))

    def test_account_balance(self):
        self.assertEqual(self.account.balance, Money(-65, "EUR"))

        date = timezone.now() - timedelta(days=2)
        self.assertEqual(self.account.balance_until_date(date=date), Money(-50, "EUR"))

    def test_total_in_for_period(self):
        self.assertEqual(self.account.total_in_for_period(period="week"), Money(65, "EUR"))

    def test_total_out_for_period(self):
        self.assertEqual(self.account.total_out_for_period(period="week"), Money(-80, "EUR"))

    def test_total_balance_for_period(self):
        self.assertEqual(self.account.balance_for_period(period="week"), Money(-15, "EUR"))

    def test_journal_entries_for_period(self):
        self.assertEqual(self.account.journal_entries_for_period(period="week").count(), 6)

    def test_to_and_from_account(self):
        account_1 = models.Account.objects.create(
            name="Account 1", account_type=models.AccountType.objects.all().first(), currency="EUR", user=self.user
        )
        account_2 = models.Account.objects.create(
            name="Account 2", account_type=models.AccountType.objects.all().first(), currency="EUR", user=self.user
        )

        transaction_1 = models.TransactionJournalEntry.create_transaction(
            amount=Money(10, "EUR"),
            description="Transaction 1",
            transaction_type=models.TransactionJournalEntry.TransactionType.WITHDRAWAL,
            from_account=account_1,
            to_account=account_2,
            user=self.user,
        )
        transaction_2 = models.TransactionJournalEntry.create_transaction(
            amount=Money(10, "EUR"),
            description="Transaction 2",
            transaction_type=models.TransactionJournalEntry.TransactionType.DEPOSIT,
            to_account=account_2,
            from_account=account_1,
            user=self.user,
        )
        transaction_3 = models.TransactionJournalEntry.create_transaction(
            amount=Money(10, "EUR"),
            description="Transaction 3",
            transaction_type=models.TransactionJournalEntry.TransactionType.TRANSFER,
            from_account=account_1,
            to_account=account_2,
            user=self.user,
        )

        self.assertEqual(transaction_1.from_account, account_1)
        self.assertEqual(transaction_1.to_account, account_2)
        self.assertEqual(transaction_2.to_account, account_2)
        self.assertEqual(transaction_2.from_account, account_1)
        self.assertEqual(transaction_3.from_account, account_1)
        self.assertEqual(transaction_3.to_account, account_2)

        with self.assertRaisesMessage(AttributeError, "from_account should be specified for transaction type withdrawal"):
            models.TransactionJournalEntry.create_transaction(
                amount=Money(10, "EUR"),
                description="Transaction 1",
                transaction_type=models.TransactionJournalEntry.TransactionType.WITHDRAWAL,
                user=self.user,
            )

        with self.assertRaisesMessage(AttributeError, "to_account should be specified for transaction type deposit"):
            models.TransactionJournalEntry.create_transaction(
                amount=Money(10, "EUR"),
                description="Transaction 1",
                transaction_type=models.TransactionJournalEntry.TransactionType.DEPOSIT,
                user=self.user,
            )
        with self.assertRaisesMessage(AttributeError, "to_account and from_account should be specified for transaction type transfer"):
            models.TransactionJournalEntry.create_transaction(
                amount=Money(10, "EUR"),
                description="Transaction 1",
                transaction_type=models.TransactionJournalEntry.TransactionType.TRANSFER,
                user=self.user,
            )

    def test_update_transaction(self):
        account_1 = models.Account.objects.create(
            name="Account 1", account_type=models.AccountType.objects.all().first(), currency="EUR", user=self.user
        )
        account_2 = models.Account.objects.create(
            name="Account 2", account_type=models.AccountType.objects.all().first(), currency="EUR", user=self.user
        )

        transaction = models.TransactionJournalEntry.create_transaction(
            amount=Money(10, "EUR"),
            description="Transaction 1",
            transaction_type=models.TransactionJournalEntry.TransactionType.WITHDRAWAL,
            from_account=account_1,
            to_account=account_2,
            user=self.user,
        )

        modified = transaction.modified
        transaction.update(
            amount=transaction.amount,
            transaction_type=transaction.transaction_type,
            date=transaction.date,
            description="Transaction 1 updated",
            from_account=account_1,
            to_account=account_2,
        )
        self.assertNotEqual(transaction.modified, modified)
        self.assertFalse(transaction.tracker.has_changed("amount"))
        self.assertEqual(transaction.to_account, account_2)
        self.assertEqual(transaction.from_account, account_1)

        transaction.update(
            amount=Money(20, "EUR"),
            transaction_type=transaction.transaction_type,
            date=transaction.date,
            description=transaction.description,
            from_account=account_1,
            to_account=account_2,
        )
        self.assertEqual(transaction.transactions.get(negative=True).amount, Money(-20, "EUR"))
        self.assertEqual(transaction.transactions.get(negative=False).amount, Money(20, "EUR"))

        transaction.update(
            from_account=account_1,
            amount=transaction.amount,
            transaction_type=transaction.transaction_type,
            date=transaction.date,
            description=transaction.description,
        )
        self.assertEqual(transaction.from_account, account_1)

    def test_transaction_different_currency(self):
        account = models.Account.objects.create(
            name="Account 1", account_type=models.AccountType.objects.all().first(), currency="EUR", user=self.user
        )

        transaction = models.TransactionJournalEntry.create_transaction(
            amount=Money(10, "DKK"),
            description="Transaction 1",
            transaction_type=models.TransactionJournalEntry.TransactionType.WITHDRAWAL,
            from_account=account,
            user=self.user,
        )

        self.assertEqual(str(transaction.transactions.get(negative=True).amount.currency), "EUR")
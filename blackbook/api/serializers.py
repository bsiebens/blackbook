from django.contrib.auth.models import User
from django.utils import timezone

from taggit_serializer.serializers import TagListSerializerField, TaggitSerializer
from rest_framework import serializers
from djmoney.contrib.django_rest_framework import MoneyField

from ..models import (
    get_currency_choices,
    get_default_currency,
    Account,
    Budget,
    BudgetPeriod,
    AccountType,
    TransactionJournalEntry,
    UserProfile,
    Category,
)


class AccountTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccountType
        fields = ["id", "name", "icon"]
        read_only_fields = fields


class CategorySerializer(serializers.ModelSerializer):
    owner = serializers.HiddenField(source="user", default=serializers.CurrentUserDefault())

    class Meta:
        model = Category
        fields = ["id", "name", "created", "modified", "owner"]
        read_only_fields = ["total"]


class AccountSerializer(serializers.ModelSerializer):
    account_type_name = serializers.ReadOnlyField(source="account_type.name")
    account_type_icon = serializers.ReadOnlyField(source="account_type.icon")
    balance = MoneyField(max_digits=15, decimal_places=2)
    owner = serializers.HiddenField(source="user", default=serializers.CurrentUserDefault())

    class Meta:
        model = Account
        fields = [
            "id",
            "owner",
            "name",
            "account_type",
            "account_type_name",
            "account_type_icon",
            "active",
            "include_in_net_worth",
            "iban",
            "currency",
            "virtual_balance",
            "balance",
            "created",
            "modified",
        ]
        read_only_fields = ["user"]


class UserSerializer(serializers.ModelSerializer):
    default_currency = serializers.ChoiceField(source="userprofile.default_currency", choices=get_currency_choices(), default=get_default_currency())
    default_period = serializers.ChoiceField(source="userprofile.default_period", choices=Budget.Period.choices, default=Budget.Period.MONTH)

    class Meta:
        model = User
        fields = ["id", "username", "first_name", "last_name", "default_currency", "default_period"]

    def update(self, instance, validated_data):
        instance.first_name = validated_data.get("first_name", instance.first_name)
        instance.last_name = validated_data.get("last_name", instance.last_name)
        instance.save()

        instance.userprofile.default_currency = validated_data.get("userprofile", {}).get("default_currency", instance.userprofile.default_currency)
        instance.userprofile.default_period = validated_data.get("userprofile", {}).get("default_period", instance.userprofile.default_period)
        instance.userprofile.save()

        return instance


class ProfileSerializer(serializers.ModelSerializer):
    default_currency = serializers.ChoiceField(source="userprofile.default_currency", choices=get_currency_choices(), default=get_default_currency())
    default_period = serializers.ChoiceField(source="userprofile.default_period", choices=Budget.Period.choices, default=Budget.Period.MONTH)
    owner = serializers.HiddenField(source="user", default=serializers.CurrentUserDefault())

    class Meta:
        model = UserProfile
        fields = ["id", "default_currency", "default_period", "owner"]


class JournalEntrySerializer(serializers.ModelSerializer):
    tags = TagListSerializerField(required=False)
    to_account = serializers.PrimaryKeyRelatedField(allow_null=True, required=False, queryset=Account.objects.all())
    from_account = serializers.PrimaryKeyRelatedField(allow_null=True, required=False, queryset=Account.objects.all())
    owner = serializers.HiddenField(source="user", default=serializers.CurrentUserDefault())
    date = serializers.DateField(allow_null=True, required=False, default=timezone.now().date())
    category_name = serializers.ReadOnlyField(source="category.name")
    budget_name = serializers.ReadOnlyField(source="budget.name")
    to_account_name = serializers.ReadOnlyField(source="to_account.name")
    from_account_name = serializers.ReadOnlyField(source="from_account.name")

    class Meta:
        model = TransactionJournalEntry
        fields = [
            "id",
            "date",
            "description",
            "transaction_type",
            "owner",
            "amount",
            "amount_currency",
            "category",
            "category_name",
            "budget",
            "budget_name",
            "tags",
            "user",
            "to_account",
            "to_account_name",
            "from_account",
            "from_account_name",
            "created",
            "modified",
        ]
        read_only_fields = ["user"]

    def __init__(self, *args, **kwargs):
        super(JournalEntrySerializer, self).__init__(*args, **kwargs)

        request = self.context.get("request")

        if request and hasattr(request, "user"):
            self.fields["to_account"].queryset = Account.objects.filter(user=request.user)
            self.fields["from_account"].queryset = Account.objects.filter(user=request.user)
            self.fields["amount"].default_currency = get_default_currency(user=request.user)

    def create(self, validated_data):
        serializers.raise_errors_on_nested_writes("create", self, validated_data)

        ModelClass = self.Meta.model

        user = validated_data.get("user")
        amount = validated_data.get("amount")
        description = validated_data.get("description")
        transaction_type = validated_data.get("transaction_type")
        date = validated_data.get("date")
        category = validated_data.get("category", None)
        budget = validated_data.get("budget", None)
        from_account = validated_data.get("from_account", None)
        to_account = validated_data.get("to_account", None)
        tags = validated_data.get("tags", [])

        instance = ModelClass.create_transaction(
            amount=amount,
            description=description,
            transaction_type=transaction_type,
            user=user,
            date=date,
            category=category,
            budget=budget,
            tags=tags,
            from_account=from_account,
            to_account=to_account,
        )

        return instance

    def update(self, instance, validated_data):
        serializers.raise_errors_on_nested_writes("update", self, validated_data)

        amount = validated_data.get("amount", instance.amount)
        description = validated_data.get("description", instance.description)
        transaction_type = validated_data.get("transaction_type", instance.transaction_type)
        date = validated_data.get("date", instance.date)
        category = validated_data.get("category", instance.category)
        budget = validated_data.get("budget", instance.budget)
        from_account = validated_data.get("from_account", instance.from_account)
        to_account = validated_data.get("to_account", instance.to_account)
        tags = validated_data.get("tags", [tag.name for tag in instance.tags.all()])

        instance.update(
            amount=amount,
            description=description,
            transaction_type=transaction_type,
            date=date,
            category=category,
            budget=budget,
            tags=tags,
            from_account=from_account,
            to_account=to_account,
        )

        return instance

    def validate(self, data):
        transaction_type = data.get("transaction_type")
        to_account = data.get("to_account", None)
        from_account = data.get("from_account", None)

        if transaction_type in [
            TransactionJournalEntry.TransactionType.DEPOSIT,
            TransactionJournalEntry.TransactionType.RECONCILIATION,
            TransactionJournalEntry.TransactionType.START,
        ]:
            if to_account is None:
                raise serializers.ValidationError("to_account should be set for transaction_type %s" % transaction_type)

        elif transaction_type == TransactionJournalEntry.TransactionType.WITHDRAWAL:
            if from_account is None:
                raise serializers.ValidationError("from_account should be set for transaction_type %s" % transaction_type)

        else:
            if from_account is None or to_account is None:
                raise serializers.ValidationError("to_account and from_account should be set for transaction type %s" % transaction_type)

        return data


class BudgetPeriodSerializer(serializers.ModelSerializer):
    budget_name = serializers.ReadOnlyField(source="budget.name")
    used = MoneyField(max_digits=15, decimal_places=2)
    available = MoneyField(max_digits=15, decimal_places=2)

    class Meta:
        model = BudgetPeriod
        fields = ["id", "budget", "budget_name", "start_date", "end_date", "amount", "amount_currency", "used", "available", "created", "modified"]
        read_only_fields = fields


class BudgetSerializer(serializers.ModelSerializer):
    owner = serializers.HiddenField(source="user", default=serializers.CurrentUserDefault())
    current_period = BudgetPeriodSerializer(required=False)
    used = MoneyField(max_digits=15, decimal_places=2)
    available = MoneyField(max_digits=15, decimal_places=2)

    class Meta:
        model = Budget
        fields = [
            "id",
            "name",
            "active",
            "amount",
            "amount_currency",
            "auto_budget",
            "auto_budget_period",
            "owner",
            "current_period",
            "used",
            "available",
            "created",
            "modified",
        ]
        read_only_fields = ["current_period", "used", "available"]
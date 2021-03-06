# Generated by Django 3.1.4 on 2020-12-15 21:08

from decimal import Decimal
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import djmoney.models.fields


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('blackbook', '0004_create_accounttypes'),
    ]

    operations = [
        migrations.CreateModel(
            name='Budget',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=250)),
                ('active', models.BooleanField(default=True, verbose_name='active?')),
                ('amount_currency', djmoney.models.fields.CurrencyField(choices=[('AMD', 'Armenian Dram'), ('AZN', 'Azerbaijanian Manat'), ('BYN', 'Belarussian Ruble'), ('BGN', 'Bulgarian Lev'), ('BAM', 'Convertible Marks'), ('HRK', 'Croatian Kuna'), ('CZK', 'Czech Koruna'), ('DKK', 'Danish Krone'), ('MKD', 'Denar'), ('EUR', 'Euro'), ('HUF', 'Forint'), ('UAH', 'Hryvnia'), ('ISK', 'Iceland Krona'), ('GEL', 'Lari'), ('ALL', 'Lek'), ('MDL', 'Moldovan Leu'), ('RON', 'New Leu'), ('NOK', 'Norwegian Krone'), ('GBP', 'Pound Sterling'), ('RUB', 'Russian Ruble'), ('RSD', 'Serbian Dinar'), ('SEK', 'Swedish Krona'), ('CHF', 'Swiss Franc'), ('TRY', 'Turkish Lira'), ('PLN', 'Zloty')], default='EUR', editable=False, max_length=3)),
                ('amount', djmoney.models.fields.MoneyField(decimal_places=2, default=Decimal('0'), max_digits=15)),
                ('auto_budget', models.CharField(choices=[('no', 'No auto-budget'), ('add', 'Add an amount each period'), ('fixed', 'Set a fixed amount each period')], default='no', max_length=30, verbose_name='auto-budget')),
                ('auto_budget_period', models.CharField(blank=True, choices=[('day', 'Daily'), ('week', 'Weekly'), ('month', 'Monthly'), ('quarter', 'Quarterly'), ('half_year', 'Every 6 months'), ('year', 'Yearly')], default='week', max_length=30, null=True, verbose_name='auto-budget period')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='budgets', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['name'],
                'permissions': [('budget_owner', 'Budget owner'), ('budget_viewer', 'Budget viewer')],
            },
        ),
        migrations.CreateModel(
            name='BudgetPeriod',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start_date', models.DateField()),
                ('end_date', models.DateField()),
                ('amount_currency', djmoney.models.fields.CurrencyField(choices=[('AMD', 'Armenian Dram'), ('AZN', 'Azerbaijanian Manat'), ('BYN', 'Belarussian Ruble'), ('BGN', 'Bulgarian Lev'), ('BAM', 'Convertible Marks'), ('HRK', 'Croatian Kuna'), ('CZK', 'Czech Koruna'), ('DKK', 'Danish Krone'), ('MKD', 'Denar'), ('EUR', 'Euro'), ('HUF', 'Forint'), ('UAH', 'Hryvnia'), ('ISK', 'Iceland Krona'), ('GEL', 'Lari'), ('ALL', 'Lek'), ('MDL', 'Moldovan Leu'), ('RON', 'New Leu'), ('NOK', 'Norwegian Krone'), ('GBP', 'Pound Sterling'), ('RUB', 'Russian Ruble'), ('RSD', 'Serbian Dinar'), ('SEK', 'Swedish Krona'), ('CHF', 'Swiss Franc'), ('TRY', 'Turkish Lira'), ('PLN', 'Zloty')], default='EUR', editable=False, max_length=3)),
                ('amount', djmoney.models.fields.MoneyField(decimal_places=2, max_digits=15)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('budget', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='periods', to='blackbook.budget')),
            ],
            options={
                'ordering': ['budget', 'start_date'],
                'get_latest_by': 'start_date',
            },
        ),
    ]

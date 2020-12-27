from django.db.models import Sum

from djmoney.money import Money
from djmoney.contrib.exchange.models import convert_money
from datetime import timedelta

import json

from .models import get_default_currency, TransactionJournalEntry
from .utilities import get_currency


def get_color_code(i):
    color_codes = ["98, 181, 229", "134, 188, 37", "152, 38, 73", "124, 132, 131", "213, 216, 135", "247, 174, 248"]
    color = (i - 1) % len(color_codes)

    return color_codes[color]


class Chart:
    def __init__(self, data):
        self.data = data

    def generate_json(self):
        chart_data = self._generate_chart_data()
        chart_options = self._generate_chart_options()

        chart_data["options"] = chart_options

        json_output = json.dumps(chart_data)
        json_output = json_output.replace('"<<', "").replace('>>"', "")

        return json_output

    def _generate_chart_data(self):
        raise NotImplementedError

    def _generate_chart_options(self):
        return self._get_default_options()

    def _get_default_options(self):
        return {
            "maintainAspectRatio": False,
            "legend": {
                "display": False,
            },
            "animation": {"duration": 0},
            "responsive": True,
            "tooltips": {
                "backgroundColor": "#f5f5f5",
                "titleFontColor": "#333",
                "bodyFontColor": "#666",
                "bodySpacing": 4,
                "xPadding": 12,
                "mode": "nearest",
                "intersect": 0,
                "position": "nearest",
            },
            "scales": {
                "yAxes": [
                    {
                        "barPercentage": 1.6,
                        "gridLines": {"drawBorder": False, "color": "rgba(29,140,248,0.0)", "zeroLineColor": "transparent"},
                        "ticks": {"padding": 20, "fontColor": "#9a9a9a"},
                    }
                ],
                "xAxes": [
                    {
                        "type": "time",
                        "time": {"unit": "day"},
                        "barPercentage": 1.6,
                        "gridLines": {"drawBorder": False, "color": "rgba(225,78,202,0.1)", "zeroLineColor": "transparent"},
                        "ticks": {"padding": 20, "fontColor": "#9a9a9a"},
                    }
                ],
            },
        }


class TransactionChart(Chart):
    def __init__(self, data, user=None, income=False, expenses_budget=False, expenses_category=False, *args, **kwargs):
        self.income = income
        self.expenses_budget = expenses_budget
        self.expenses_category = expenses_category
        self.user = user
        self.currency = get_default_currency(user=self.user)

        super().__init__(data=data, *args, **kwargs)

    def _generate_chart_options(self):
        options = self._get_default_options()

        options["scales"] = {}
        options["legend"] = {"position": "right"}

        return options

    def _generate_chart_data(self):
        data = {"type": "pie", "data": {"labels": [], "datasets": [{"data": [], "borderWidth": [], "backgroundColor": [], "borderColor": []}]}}

        amounts = {}
        account_names = {}

        if self.income:
            self.data = [item for item in self.data if not item["negative"]]
        else:
            self.data = [item for item in self.data if item["negative"]]

        for transaction in self.data:
            account_name = "External account (untracked)"
            if self.income:
                if transaction["journal_entry__transaction_type"] == TransactionJournalEntry.TransactionType.START:
                    account_name = "Starting balance"

                else:
                    from_account_name = account_names.get(
                        transaction["journal_entry"], TransactionJournalEntry.objects.get(id=transaction["journal_entry"]).from_account
                    )

                    if from_account_name is not None:
                        account_name = from_account_name.name
                        account_names[transaction["journal_entry"]] = from_account_name.name
                    else:
                        account_names[transaction["journal_entry"]] = None

            if not self.income:
                if self.expenses_budget and transaction["journal_entry__budget__budget__name"] is not None:
                    account_name = transaction["journal_entry__budget__budget__name"]

                if self.expenses_category and transaction["journal_entry__category__name"] is not None:
                    account_name = transaction["journal_entry__category__name"]

            amount = amounts.get(account_name, 0.0)
            amount += float(transaction["total"]) * -1 if transaction["negative"] else float(transaction["total"])
            amounts[account_name] = amount

        counter = 1
        for account, amount in amounts.items():
            color = get_color_code(counter)
            counter += 1

            data["data"]["labels"].append(account)
            data["data"]["datasets"][0]["data"].append(round(amount, 2))
            data["data"]["datasets"][0]["borderWidth"].append(2)
            data["data"]["datasets"][0]["backgroundColor"].append("rgba({color}, 1.0)".format(color=color))
            data["data"]["datasets"][0]["borderColor"].append("rgba(255, 255, 255, 1.0)".format(color=color))

        return data


class AccountChart(Chart):
    def __init__(self, data, start_date, end_date, user=None, *args, **kwargs):
        self.start_date = start_date
        self.end_date = end_date
        self.user = user
        self.currency = get_default_currency(user=self.user)

        super().__init__(data=data, *args, **kwargs)

    def _generate_chart_options(self):
        options = self._get_default_options()

        options["tooltips"]["callbacks"] = {
            "label": "<<function(tooltipItems, data) { return data.datasets[tooltipItems.datasetIndex].label +': ' + tooltipItems.yLabel + ' (%s)'; }>>"
            % get_currency(self.currency, self.user)
        }

        if abs((self.end_date - self.start_date).days) > 150:
            options["scales"]["xAxes"][0]["time"]["unit"] = "week"

        return options

    def _generate_chart_data(self):
        dates = []

        for days_to_add in range(abs((self.end_date - self.start_date).days) + 1):
            day = self.start_date + timedelta(days=days_to_add)
            dates.append(day)

        data = {"type": "line", "data": {"labels": [date.strftime("%d %b %Y") for date in dates], "datasets": []}}

        accounts = {}
        accounts_virtual_balance = {}
        for item in self.data:
            if item["account__name"] in accounts.keys():
                date_entry = accounts[item["account__name"]].get(item["journal_entry__date"], Money(0, self.currency))
                date_entry += convert_money(Money(item["total"], item["amount_currency"]), self.currency)

                accounts[item["account__name"]][item["journal_entry__date"]] = date_entry

            else:
                accounts[item["account__name"]] = {
                    item["journal_entry__date"]: convert_money(Money(item["total"], item["amount_currency"]), self.currency)
                }
                accounts_virtual_balance[item["account__name"]] = item["account__virtual_balance"]

        counter = 1
        for account, date_entries in accounts.items():
            color = get_color_code(counter)

            account_data = {
                "label": account,
                "fill": "!1",
                "borderColor": "rgba({color}, 1.0)".format(color=color),
                "borderWidth": 2,
                "borderDash": [],
                "borderDash0ffset": 0,
                "pointBackgroundColor": "rgba({color}, 1.0)".format(color=color),
                "pointBorderColor": "rgba(255,255,255,0)",
                "pointHoverBackgroundColor": "rgba({color}, 1.0)".format(color=color),
                "pointBorderWidth": 20,
                "pointHoverRadius": 4,
                "pointHoverBorderWidth": 15,
                "pointRadius": 4,
                "data": [],
            }

            if abs((self.end_date - self.start_date).days) > 150:
                account_data["pointRadius"] = 0

            counter += 1

            for date_index in range(len(dates)):
                date = dates[date_index]

                value = 0
                if date_index == 0:
                    amounts = dict(filter(lambda elem: elem[0] <= date, date_entries.items()))
                    value = float(sum([item.amount for item in amounts.values()])) - float(accounts_virtual_balance[account])

                else:
                    value = account_data["data"][date_index - 1]

                    if date in date_entries.keys():
                        value += float(date_entries[date].amount)

                account_data["data"].append(round(value, 2))
            data["data"]["datasets"].append(account_data)

        return data

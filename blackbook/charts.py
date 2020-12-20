from django.db.models import Sum

from djmoney.money import Money
from djmoney.contrib.exchange.models import convert_money
from datetime import timedelta

import json

from .models import get_default_currency
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


class AccountChart(Chart):
    def __init__(self, data, start_date, end_date, user=None, *args, **kwargs):
        self.start_date = start_date
        self.end_date = end_date
        self.user = user

        super().__init__(data=data, *args, **kwargs)

    def _generate_chart_options(self):
        options = self._get_default_options()

        options["tooltips"]["callbacks"] = {
            "label": "<<function(tooltipItems, data) { return data.datasets[tooltipItems.datasetIndex].label +': ' + tooltipItems.yLabel + ' (%s)'; }>>"
            % get_currency(get_default_currency(self.user), self.user)
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

        counter = 1
        for account in self.data:
            color = get_color_code(counter)

            account_data = {
                "label": account.name,
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

            start_balance = account.balance_until_date(date=dates[0] - timedelta(days=1))
            amounts_per_day = (
                account.transactions.filter(journal_entry__date__range=(dates[0], dates[-1]))
                .values("journal_entry__date", "amount_currency")
                .annotate(amount=Sum("amount"))
            )
            amounts_for_chart = []

            for day in range(len(dates)):
                date = dates[day]

                value = (
                    account_data["data"][day - 1]
                    if day > 0
                    else round(float(convert_money(start_balance, get_default_currency(user=self.user)).amount), 2)
                )
                for amount in amounts_per_day:
                    if amount["journal_entry__date"] == date:
                        value += float(convert_money(Money(amount["amount"], amount["amount_currency"]), get_default_currency(user=self.user)).amount)
                        break

                account_data["data"].append(round(float(value), 2))
            data["data"]["datasets"].append(account_data)

        return data

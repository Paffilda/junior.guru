import math
import functools
from datetime import date

from peewee import CharField, DateField, IntegerField

from juniorguru.models.base import BaseModel


class Transaction(BaseModel):
    happened_on = DateField(index=True)
    category = CharField()
    amount = IntegerField()

    @classmethod
    def listing(cls, today=None):
        today = today or date.today()
        try:
            year_ago = today.replace(year=today.year - 1)
        except ValueError:  # 29th February
            year_ago = today.replace(year=today.year - 1, day=today.day - 1)

        return cls.select() \
            .where(cls.happened_on >= year_ago, cls.happened_on <= today) \
            .order_by(cls.happened_on.desc())

    @classmethod
    def incomes(cls, today=None):
        return cls.listing(today) \
            .where(cls.amount >= 0, cls.category != 'tax')

    @classmethod
    def incomes_breakdown(cls, today=None):
        return sum_by_category(cls.incomes(today))

    @classmethod
    def expenses(cls, today=None):
        return cls.listing(today) \
            .where(((cls.amount < 0) & (cls.category != 'salary')) |
                   (cls.category == 'tax'))

    @classmethod
    def expenses_breakdown(cls, today=None):
        return {category: abs(value) for category, value
                in sum_by_category(cls.expenses(today)).items()}

    @classmethod
    def profit_monthly(cls, today=None):
        incomes_total = sum(transaction.amount for transaction in cls.incomes(today))
        expenses_total = sum(transaction.amount for transaction in cls.expenses(today))
        return math.ceil((incomes_total + expenses_total) / 12.0)


def sum_by_category(transactions):
    def reduce_step(mapping, transaction):
        mapping.setdefault(transaction.category, 0)
        mapping[transaction.category] += transaction.amount
        return mapping
    return functools.reduce(reduce_step, transactions, {})

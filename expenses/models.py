from __future__ import annotations   # for forward references (nice typing support)

from decimal import Decimal
from typing import Optional

from django.db import models
from django.utils import timezone
from django.db.models import Sum


class Brand(models.Model):
    """A brand has top-level budgets that all its campaigns share."""

    # Brand name (unique so you don’t accidentally create duplicates)
    name = models.CharField(max_length=100, unique=True)

    # Budget limits
    daily_budget = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    monthly_budget = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))

    def __str__(self) -> str:
        """Human-readable representation in the admin panel."""
        return self.name

    # ---------- Spend aggregation helpers ----------
    def spent_today(self) -> Decimal:
        """Sum all expenses across all campaigns for *today*."""
        today = timezone.localdate()
        total = Expense.objects.filter(
            campaign__brand=self,
            date=today,
        ).aggregate(s=Sum("amount"))["s"]
        return total or Decimal("0.00")

    def spent_this_month(self) -> Decimal:
        """Sum all expenses across all campaigns for *this month*."""
        today = timezone.localdate()
        month_start = today.replace(day=1)   # 1st day of month
        total = Expense.objects.filter(
            campaign__brand=self,
            date__gte=month_start,
            date__lte=today,
        ).aggregate(s=Sum("amount"))["s"]
        return total or Decimal("0.00")


class Campaign(models.Model):
    """A campaign under a brand that can be toggled on/off."""

    # Each campaign belongs to exactly one brand
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, related_name="campaigns")
    name = models.CharField(max_length=100)

    # Optional per-campaign budgets (if 0.00 → only brand budget applies)
    daily_budget = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    monthly_budget = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))

    # Whether this campaign is currently active
    active = models.BooleanField(default=True)

    # Optional start/end window
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)

    def __str__(self) -> str:
        """Readable name, also shows its brand in admin panel."""
        return f"{self.name} ({self.brand.name})"

    # ---------- Spend aggregation ----------
    def spent_today(self) -> Decimal:
        """Sum of today’s expenses for this campaign."""
        today = timezone.localdate()
        total = self.expenses.filter(date=today).aggregate(s=Sum("amount"))["s"]
        return total or Decimal("0.00")

    def spent_this_month(self) -> Decimal:
        """Sum of this month’s expenses for this campaign."""
        today = timezone.localdate()
        month_start = today.replace(day=1)
        total = self.expenses.filter(date__gte=month_start, date__lte=today).aggregate(s=Sum("amount"))["s"]
        return total or Decimal("0.00")

    def within_date_window(self) -> bool:
        """True if today is within start_date/end_date (if set)."""
        today = timezone.localdate()
        if self.start_date and today < self.start_date:
            return False
        if self.end_date and today > self.end_date:
            return False
        return True


class Schedule(models.Model):
    """Dayparting: restrict a campaign to specific hours."""

    # One campaign has one schedule
    campaign = models.OneToOneField(Campaign, on_delete=models.CASCADE, related_name="schedule")

    # Hours are stored as integers (0–23). Example: start=9, end=17 means 9AM–5PM.
    start_hour = models.PositiveSmallIntegerField(default=0)
    end_hour = models.PositiveSmallIntegerField(default=24)   # 24 means "end of day"

    def __str__(self) -> str:
        return f"Schedule for {self.campaign.name}: {self.start_hour:02d}:00–{self.end_hour:02d}:00"


class Expense(models.Model):
    """Money spent against a campaign on a specific date."""

    # Which campaign this expense belongs to
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name="expenses")

    # How much was spent
    amount = models.DecimalField(max_digits=12, decimal_places=2)

    # On which date the spend occurred
    date = models.DateField()

    # Optional notes (for admin or reporting)
    notes = models.TextField(blank=True, null=True)

    def __str__(self) -> str:
        return f"{self.campaign.name} - {self.amount} on {self.date}"

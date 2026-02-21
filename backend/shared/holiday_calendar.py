"""
Static Holiday Calendar — Sprint 356

Generates US federal holiday dates for any year. Used by JE testing engine
(JT-19: Holiday Posting Detection) to flag entries posted on public holidays
as an ISA 240.A40 fraud risk indicator.

Pure computation — no external API calls, no persistent storage.
"""

from datetime import date, timedelta


def _nth_weekday(year: int, month: int, weekday: int, n: int) -> date:
    """Get the nth occurrence of a weekday in a month.

    Args:
        year: Calendar year
        month: Month (1-12)
        weekday: Day of week (0=Monday, 6=Sunday)
        n: Occurrence (1=first, 2=second, etc.)

    Returns:
        Date of the nth weekday in the given month.
    """
    first_day = date(year, month, 1)
    # Days until the target weekday from the 1st
    days_ahead = weekday - first_day.weekday()
    if days_ahead < 0:
        days_ahead += 7
    first_occurrence = first_day + timedelta(days=days_ahead)
    return first_occurrence + timedelta(weeks=n - 1)


def _last_weekday(year: int, month: int, weekday: int) -> date:
    """Get the last occurrence of a weekday in a month."""
    # Start from last day of month
    if month == 12:
        last_day = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        last_day = date(year, month + 1, 1) - timedelta(days=1)
    days_back = last_day.weekday() - weekday
    if days_back < 0:
        days_back += 7
    return last_day - timedelta(days=days_back)


def _observed_date(d: date) -> date:
    """Apply US federal observance rules for fixed-date holidays.

    If the holiday falls on Saturday, the observed date is Friday.
    If the holiday falls on Sunday, the observed date is Monday.
    """
    if d.weekday() == 5:  # Saturday
        return d - timedelta(days=1)
    if d.weekday() == 6:  # Sunday
        return d + timedelta(days=1)
    return d


def get_us_federal_holidays(year: int) -> dict[date, str]:
    """Generate US federal holidays for a given year.

    Returns a dict mapping date -> holiday name. Includes both the
    actual date and the observed date (if different) for fixed-date holidays.

    Covers all 11 US federal holidays:
    - New Year's Day (Jan 1)
    - Martin Luther King Jr. Day (3rd Monday, Jan)
    - Presidents' Day (3rd Monday, Feb)
    - Memorial Day (last Monday, May)
    - Juneteenth (Jun 19)
    - Independence Day (Jul 4)
    - Labor Day (1st Monday, Sep)
    - Columbus Day (2nd Monday, Oct)
    - Veterans Day (Nov 11)
    - Thanksgiving (4th Thursday, Nov)
    - Christmas Day (Dec 25)
    """
    holidays: dict[date, str] = {}

    # Fixed-date holidays (with observance rules)
    fixed = [
        (date(year, 1, 1), "New Year's Day"),
        (date(year, 6, 19), "Juneteenth"),
        (date(year, 7, 4), "Independence Day"),
        (date(year, 11, 11), "Veterans Day"),
        (date(year, 12, 25), "Christmas Day"),
    ]
    for d, name in fixed:
        holidays[d] = name
        observed = _observed_date(d)
        if observed != d:
            holidays[observed] = f"{name} (Observed)"

    # Floating holidays
    holidays[_nth_weekday(year, 1, 0, 3)] = "Martin Luther King Jr. Day"
    holidays[_nth_weekday(year, 2, 0, 3)] = "Presidents' Day"
    holidays[_last_weekday(year, 5, 0)] = "Memorial Day"
    holidays[_nth_weekday(year, 9, 0, 1)] = "Labor Day"
    holidays[_nth_weekday(year, 10, 0, 2)] = "Columbus Day"
    holidays[_nth_weekday(year, 11, 3, 4)] = "Thanksgiving"

    return holidays


def get_holiday_dates(years: set[int]) -> dict[date, str]:
    """Get all US federal holidays for a set of years.

    Args:
        years: Set of calendar years to generate holidays for.

    Returns:
        Combined dict mapping date -> holiday name across all years.
    """
    all_holidays: dict[date, str] = {}
    for year in years:
        all_holidays.update(get_us_federal_holidays(year))
    return all_holidays

"""Deterministic illustrative fixed-rate EMI schedule (not a loan servicing ledger)."""
from decimal import Decimal, ROUND_HALF_UP

CENT = Decimal('0.01')

def repayment_schedule(principal, annual_rate, months):
    principal = Decimal(str(principal))
    annual_rate = Decimal(str(annual_rate))
    months = int(months)
    if not principal.is_finite() or principal <= 0 or not annual_rate.is_finite() or annual_rate < 0 or not 1 <= months <= 600:
        raise ValueError('Invalid loan terms')
    rate = annual_rate / Decimal('1200')
    payment = principal / months if rate == 0 else principal * rate * (1 + rate) ** months / ((1 + rate) ** months - 1)
    payment = payment.quantize(CENT, rounding=ROUND_HALF_UP)
    balance = principal
    rows = []
    for number in range(1, months + 1):
        interest = (balance * rate).quantize(CENT, rounding=ROUND_HALF_UP)
        due = min(balance + interest, payment) if number < months else balance + interest
        principal_paid = due - interest
        balance = max(Decimal('0'), balance - principal_paid)
        rows.append({'installment': number, 'payment': str(due), 'principal': str(principal_paid), 'interest': str(interest), 'remaining_balance': str(balance)})
    return rows

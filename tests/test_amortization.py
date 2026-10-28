from decimal import Decimal
import pytest
from apps.loans.amortization import repayment_schedule

def test_zero_interest_schedule_reconciles():
    rows = repayment_schedule('1200', '0', 12)
    assert len(rows) == 12
    assert sum(Decimal(r['principal']) for r in rows) == Decimal('1200')
    assert rows[-1]['remaining_balance'] == '0'

def test_interest_schedule_reconciles():
    rows = repayment_schedule('10000', '12', 12)
    assert sum(Decimal(r['principal']) for r in rows) == Decimal('10000')
    assert rows[-1]['remaining_balance'] == '0'

@pytest.mark.parametrize('principal,rate,months', [('0','10',12),('100','-1',12),('100','1',0)])
def test_invalid_terms(principal,rate,months):
    with pytest.raises(ValueError): repayment_schedule(principal,rate,months)

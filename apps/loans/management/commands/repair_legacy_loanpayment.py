"""Repair the one confirmed legacy missing table without touching existing rows.

Older Docker images generated migrations dynamically. Their 0001_initial could be
marked applied before LoanPayment was added, so a new 0001_initial file alone
cannot create the missing table in an existing database.
"""
from django.core.management.base import BaseCommand, CommandError
from django.db import connection
from apps.loans.models import Loan, LoanPayment

class Command(BaseCommand):
    help = 'Create missing loans_loanpayment table in legacy databases, preserving existing loans.'

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            existing = set(connection.introspection.table_names(cursor))
        loan_table = Loan._meta.db_table
        payment_table = LoanPayment._meta.db_table
        if payment_table in existing:
            self.stdout.write(f'{payment_table} already exists; no changes made')
            return
        if loan_table not in existing:
            raise CommandError('Loan table missing; refusing to repair partial/unmigrated database')
        with connection.schema_editor() as editor:
            editor.create_model(LoanPayment)
        self.stdout.write(self.style.SUCCESS(f'Created missing {payment_table} without deleting data'))

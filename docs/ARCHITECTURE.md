# Architecture and invariants

Modular Django monolith: identity, accounts, transfers, ledger, risk, audit, notifications, loans, cards, billing, investments, operations. PostgreSQL is authoritative for financial data. Redis/Celery are auxiliary.

## Transfer invariants
- Source and destination account rows locked in canonical UUID order.
- Same-user transfers serialized using user row locks.
- Idempotency key unique per initiator and compared to original payload.
- Account balances guarded by a nonnegative constraint and F-expression update.
- Each completed transfer creates exactly two equal debit/credit ledger entries in the same DB transaction.
- Rejections for insufficient funds/limits are persisted; malformed/unauthorized requests return API errors without creating records.
- Outbox record inserted in same transaction; external notification dispatch is not implemented.

## Known accounting limitation
Ledger model uses transfer-specific debit/credit semantics and does not yet model a general chart of accounts, system suspense accounts, external settlement accounts, interest or fees. Balance caches are not derived automatically from the ledger. Ledger entry immutability is not enforced at database permissions/trigger level. This is NOT a bank-grade accounting system.

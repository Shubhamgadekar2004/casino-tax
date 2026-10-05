-- Casino Individual Tax & Accounting Demo — Database Schema
-- All data is synthetic / for demonstration purposes only.

PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

-- ──────────────────────────────────────────────
-- 1. Casinos
-- ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS casinos (
    casino_id       TEXT PRIMARY KEY,
    name            TEXT NOT NULL,
    location        TEXT,
    license_number  TEXT,
    status          TEXT DEFAULT 'ACTIVE',
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ──────────────────────────────────────────────
-- 2. Individuals
-- ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS individuals (
    individual_id   TEXT PRIMARY KEY,
    pan             TEXT NOT NULL UNIQUE,
    first_name      TEXT NOT NULL,
    last_name       TEXT NOT NULL,
    email           TEXT,
    mobile          TEXT,
    date_of_birth   DATE,
    kyc_status      TEXT DEFAULT 'PENDING',
    kyc_date        DATE,
    registration_date DATE NOT NULL,
    risk_score      INTEGER DEFAULT 0,
    status          TEXT DEFAULT 'ACTIVE',
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_individuals_pan ON individuals(pan);

-- ──────────────────────────────────────────────
-- 3. Casino Accounts
-- ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS casino_accounts (
    account_id      TEXT PRIMARY KEY,
    individual_id   TEXT NOT NULL,
    casino_id       TEXT NOT NULL,
    account_number  TEXT NOT NULL,
    balance         REAL DEFAULT 0.0,
    status          TEXT DEFAULT 'ACTIVE',
    opened_date     DATE NOT NULL,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (individual_id) REFERENCES individuals(individual_id),
    FOREIGN KEY (casino_id) REFERENCES casinos(casino_id)
);

-- ──────────────────────────────────────────────
-- 4. Games
-- ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS games (
    game_id             TEXT PRIMARY KEY,
    casino_id           TEXT NOT NULL,
    game_type           TEXT NOT NULL,
    game_date           DATE NOT NULL,
    start_time          TIMESTAMP,
    end_time            TIMESTAMP,
    prize_pool          REAL NOT NULL CHECK(prize_pool >= 0),
    num_participants    INTEGER DEFAULT 0,
    num_winners         INTEGER DEFAULT 0,
    allocation_method   TEXT NOT NULL,
    status              TEXT DEFAULT 'SCHEDULED',
    description         TEXT,
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (casino_id) REFERENCES casinos(casino_id)
);
CREATE INDEX IF NOT EXISTS idx_games_date ON games(game_date);
CREATE INDEX IF NOT EXISTS idx_games_type ON games(game_type);

-- ──────────────────────────────────────────────
-- 5. Game Participants (many-to-many)
-- ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS game_participants (
    participant_id  TEXT PRIMARY KEY,
    game_id         TEXT NOT NULL,
    individual_id   TEXT NOT NULL,
    buy_in_amount   REAL DEFAULT 0.0,
    entry_time      TIMESTAMP,
    exit_time       TIMESTAMP,
    is_winner       INTEGER DEFAULT 0,
    position        INTEGER,
    status          TEXT DEFAULT 'ACTIVE',
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (game_id) REFERENCES games(game_id),
    FOREIGN KEY (individual_id) REFERENCES individuals(individual_id),
    UNIQUE(game_id, individual_id)
);
CREATE INDEX IF NOT EXISTS idx_participants_game ON game_participants(game_id);
CREATE INDEX IF NOT EXISTS idx_participants_individual ON game_participants(individual_id);

-- ──────────────────────────────────────────────
-- 6. Winning Allocations
-- ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS winning_allocations (
    allocation_id       TEXT PRIMARY KEY,
    game_id             TEXT NOT NULL,
    individual_id       TEXT NOT NULL,
    gross_winning       REAL NOT NULL CHECK(gross_winning >= 0),
    allocation_method   TEXT NOT NULL,
    share_percentage    REAL,
    net_winning         REAL,
    status              TEXT DEFAULT 'ALLOCATED',
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (game_id) REFERENCES games(game_id),
    FOREIGN KEY (individual_id) REFERENCES individuals(individual_id)
);

-- ──────────────────────────────────────────────
-- 7. Transactions (immutable ledger)
-- ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS transactions (
    transaction_id      TEXT PRIMARY KEY,
    pan                 TEXT NOT NULL,
    game_id             TEXT,
    transaction_date    TIMESTAMP NOT NULL,
    transaction_type    TEXT NOT NULL,
    amount              REAL NOT NULL CHECK(amount >= 0),
    credit_debit        TEXT NOT NULL CHECK(credit_debit IN ('CREDIT', 'DEBIT')),
    payment_method      TEXT,
    reference_number    TEXT,
    description         TEXT,
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (pan) REFERENCES individuals(pan),
    FOREIGN KEY (game_id) REFERENCES games(game_id)
);
CREATE INDEX IF NOT EXISTS idx_txn_pan ON transactions(pan);
CREATE INDEX IF NOT EXISTS idx_txn_game ON transactions(game_id);
CREATE INDEX IF NOT EXISTS idx_txn_date ON transactions(transaction_date);
CREATE INDEX IF NOT EXISTS idx_txn_type ON transactions(transaction_type);

-- ──────────────────────────────────────────────
-- 8. Tax Configuration
-- ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS tax_configurations (
    config_id       TEXT PRIMARY KEY,
    tax_rate        REAL NOT NULL,
    cess_rate       REAL NOT NULL,
    surcharge_rate  REAL DEFAULT 0.0,
    tds_rate        REAL NOT NULL,
    effective_date  DATE NOT NULL,
    income_category TEXT,
    description     TEXT,
    is_active       INTEGER DEFAULT 1,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ──────────────────────────────────────────────
-- 9. Tax Calculations
-- ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS tax_calculations (
    calculation_id      TEXT PRIMARY KEY,
    individual_id       TEXT NOT NULL,
    pan                 TEXT NOT NULL,
    assessment_year     TEXT NOT NULL,
    gross_winnings      REAL NOT NULL,
    taxable_winnings    REAL NOT NULL,
    tax_amount          REAL NOT NULL,
    cess_amount         REAL NOT NULL,
    surcharge_amount    REAL DEFAULT 0.0,
    total_tax           REAL NOT NULL,
    tds_deducted        REAL DEFAULT 0.0,
    balance_payable     REAL DEFAULT 0.0,
    config_id           TEXT,
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (individual_id) REFERENCES individuals(individual_id),
    FOREIGN KEY (config_id) REFERENCES tax_configurations(config_id)
);

-- ──────────────────────────────────────────────
-- 10. TDS Records
-- ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS tds_records (
    tds_id          TEXT PRIMARY KEY,
    pan             TEXT NOT NULL,
    game_id         TEXT NOT NULL,
    gross_amount    REAL NOT NULL,
    tds_rate        REAL NOT NULL,
    tds_amount      REAL NOT NULL,
    deduction_date  DATE NOT NULL,
    status          TEXT DEFAULT 'DEDUCTED',
    reference       TEXT,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (pan) REFERENCES individuals(pan),
    FOREIGN KEY (game_id) REFERENCES games(game_id)
);
CREATE INDEX IF NOT EXISTS idx_tds_pan ON tds_records(pan);

-- ──────────────────────────────────────────────
-- 11. ITR Records
-- ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS itr_records (
    itr_id              TEXT PRIMARY KEY,
    individual_id       TEXT NOT NULL,
    pan                 TEXT NOT NULL,
    assessment_year     TEXT NOT NULL,
    filing_date         DATE,
    total_income        REAL DEFAULT 0.0,
    casino_winnings_declared REAL DEFAULT 0.0,
    tax_paid            REAL DEFAULT 0.0,
    tds_claimed         REAL DEFAULT 0.0,
    refund_claimed      REAL DEFAULT 0.0,
    itr_form            TEXT DEFAULT 'ITR-1',
    verification_status TEXT DEFAULT 'PENDING',
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (individual_id) REFERENCES individuals(individual_id)
);
CREATE INDEX IF NOT EXISTS idx_itr_pan ON itr_records(pan);

-- ──────────────────────────────────────────────
-- 12. Reconciliations
-- ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS reconciliations (
    reconciliation_id       TEXT PRIMARY KEY,
    individual_id           TEXT NOT NULL,
    pan                     TEXT NOT NULL,
    assessment_year         TEXT NOT NULL,
    casino_winnings         REAL DEFAULT 0.0,
    itr_declared_winnings   REAL DEFAULT 0.0,
    difference              REAL DEFAULT 0.0,
    tds_deducted            REAL DEFAULT 0.0,
    expected_tax            REAL DEFAULT 0.0,
    reported_tax            REAL DEFAULT 0.0,
    status                  TEXT NOT NULL,
    remarks                 TEXT,
    reconciled_date         DATE,
    created_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (individual_id) REFERENCES individuals(individual_id)
);

-- ──────────────────────────────────────────────
-- 13. Risk Scores
-- ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS risk_scores (
    risk_id         TEXT PRIMARY KEY,
    individual_id   TEXT NOT NULL,
    pan             TEXT NOT NULL,
    score           INTEGER NOT NULL CHECK(score >= 0 AND score <= 100),
    risk_level      TEXT NOT NULL,
    factors         TEXT,          -- JSON list of contributing factors
    assessment_date DATE NOT NULL,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (individual_id) REFERENCES individuals(individual_id)
);

-- ──────────────────────────────────────────────
-- 14. Audit Logs
-- ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS audit_logs (
    audit_id        TEXT PRIMARY KEY,
    timestamp       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_id         TEXT NOT NULL,
    action          TEXT NOT NULL,
    entity          TEXT NOT NULL,
    entity_id       TEXT,
    old_value       TEXT,
    new_value       TEXT,
    ip_address      TEXT DEFAULT 'DEMO',
    description     TEXT,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_audit_entity ON audit_logs(entity);

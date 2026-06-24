-- ============================================================
-- Fintech Transaction Analytics Pipeline — PostgreSQL Schema
-- ============================================================

CREATE TABLE IF NOT EXISTS users (
    user_id     VARCHAR(50)  PRIMARY KEY,
    user_name   VARCHAR(150),
    created_at  TIMESTAMP    NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS merchants (
    merchant_id     VARCHAR(50)  PRIMARY KEY,
    merchant_name   VARCHAR(150),
    category        VARCHAR(100),
    created_at      TIMESTAMP    NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS transactions (
    transaction_id      VARCHAR(50)     PRIMARY KEY,
    user_id              VARCHAR(50)     NOT NULL REFERENCES users(user_id),
    merchant_id          VARCHAR(50)     NOT NULL REFERENCES merchants(merchant_id),
    amount               NUMERIC(14, 2)  NOT NULL CHECK (amount >= 0),
    payment_method       VARCHAR(50)     NOT NULL,
    transaction_status   VARCHAR(20)     NOT NULL,
    is_suspicious        BOOLEAN         NOT NULL DEFAULT FALSE,
    suspicious_reason    VARCHAR(255),
    timestamp            TIMESTAMP       NOT NULL,
    created_at           TIMESTAMP       NOT NULL DEFAULT NOW()
);

-- Indexes for the analytics queries the dashboard/API rely on.
CREATE INDEX IF NOT EXISTS idx_transactions_user_id        ON transactions(user_id);
CREATE INDEX IF NOT EXISTS idx_transactions_merchant_id    ON transactions(merchant_id);
CREATE INDEX IF NOT EXISTS idx_transactions_timestamp      ON transactions(timestamp);
CREATE INDEX IF NOT EXISTS idx_transactions_status         ON transactions(transaction_status);
CREATE INDEX IF NOT EXISTS idx_transactions_payment_method ON transactions(payment_method);
CREATE INDEX IF NOT EXISTS idx_transactions_suspicious     ON transactions(is_suspicious);

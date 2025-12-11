-- Migration: seed default roles
INSERT INTO role (id,name)
VALUES
    (1,'ADMIN'),
    (2,'OWNER'),
    (3,'CAPTAIN'),
    (4,'MARITIME_EXPERT'),
    (5,'FINANCIAL_ANALYST')
ON CONFLICT (name) DO NOTHING;

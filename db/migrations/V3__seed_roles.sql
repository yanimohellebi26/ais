-- Migration: seed default roles
INSERT INTO roles (name, description)
VALUES
    ('admin', 'Full administrative access to the platform'),
    ('owner', 'Owns vessels and manages their information'),
    ('captain', 'Operates vessels and reports voyages'),
    ('maritime_expert', 'Provides maritime expertise and analytics'),
    ('financial_analyst', 'Analyzes financial performance related to maritime operations')
ON CONFLICT (name) DO NOTHING;

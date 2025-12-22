INSERT INTO
    additional_services (
        service_id,
        service_name,
        category,
        services,
        applicable_to,
        is_active
    )
VALUES

-- =======================
-- MAINTENANCE
-- =======================
(
    'SRV001',
    'Painting',
    'MAINTENANCE',
    NULL,
    ARRAY['FLAT', 'PLOT'],
    TRUE
),
(
    'SRV002',
    'Pest Control & Termite Treatment',
    'MAINTENANCE',
    NULL,
    ARRAY['FLAT', 'PLOT'],
    TRUE
),
(
    'SRV003',
    'Interior Design & Modular Kitchen',
    'MAINTENANCE',
    NULL,
    ARRAY['FLAT'],
    TRUE
),
(
    'SRV004',
    'Fencing',
    'MAINTENANCE',
    NULL,
    ARRAY['PLOT'],
    TRUE
),

-- =======================
-- SECURITY
-- =======================
(
    'SRV005',
    'Security Guard Management',
    'SECURITY',
    NULL,
    ARRAY['FLAT', 'PLOT'],
    TRUE
),

-- =======================
-- CLEANING
-- =======================
(
    'SRV006',
    'Deep Cleaning',
    'CLEANING',
    NULL,
    ARRAY['FLAT'],
    TRUE
),
(
    'SRV007',
    'Post Construction Clean Up',
    'CLEANING',
    NULL,
    ARRAY['FLAT'],
    TRUE
),

-- =======================
-- LANDSCAPING
-- =======================
(
    'SRV008',
    'Landscaping and Lawn Care',
    'LANDSCAPING',
    NULL,
    ARRAY['PLOT'],
    TRUE
),

-- =======================
-- INSPECTION
-- =======================
(
    'SRV009',
    'Surveying',
    'INSPECTION',
    NULL,
    ARRAY['FLAT', 'PLOT'],
    TRUE
),
(
    'SRV010',
    'Legal Opinion',
    'INSPECTION',
    NULL,
    ARRAY['FLAT', 'PLOT'],
    TRUE
);
-- BASIC - FLAT
INSERT INTO
    "PropCare".subscriptions_plans (
        sub_id,
        sub_type,
        category,
        services,
        durations,
        rental_percentages,
        comments,
        created_by,
        is_active,
        created_at,
        updated_at
    )
VALUES (
        'VPC_SUB_001',
        'BASIC',
        'FLAT',
        ARRAY[
            'Rental services',
            'Tenant management',
            'Agreement with tenant and rental collection',
            'Tenant verification',
            'Vacating the tenant (pre-in, post)',
            'Quarterly physical inspections',
            'Preliminary report'
        ],
        '{"3": 3999, "6": 6499, "12": 10999}'::jsonb,
        '{"3": 7, "6": 7, "12": 7}'::jsonb,
        'Basic plan covering essential flat management and tenant coordination.',
        'admin_001',
        TRUE,
        NOW(),
        NOW()
    );

-- GOLD - FLAT
INSERT INTO
    "PropCare".subscriptions_plans (
        sub_id,
        sub_type,
        category,
        services,
        durations,
        rental_percentages,
        comments,
        created_by,
        is_active,
        created_at,
        updated_at
    )
VALUES (
        'VPC_SUB_002',
        'GOLD',
        'FLAT',
        ARRAY[
            'Rental services',
            'Tenant management',
            'Agreement with tenant and rental collection',
            'Tenant verification',
            'Vacating the tenant (pre-in, post)',
            'Quarterly physical inspections',
            'Preliminary report',
            'Quarterly walkthrough',
            'Utility and maintenance coordination',
            'Dedicated property manager'
        ],
        '{"3": 4999, "6": 7999, "12": 12999}'::jsonb,
        '{"3": 9, "6": 9, "12": 9}'::jsonb,
        'Gold plan with extended tenant and maintenance management features.',
        'admin_001',
        TRUE,
        NOW(),
        NOW()
    );

-- PLATINUM - FLAT
INSERT INTO
    "PropCare".subscriptions_plans (
        sub_id,
        sub_type,
        category,
        services,
        durations,
        rental_percentages,
        comments,
        created_by,
        is_active,
        created_at,
        updated_at
    )
VALUES (
        'VPC_SUB_003',
        'PLATINUM',
        'FLAT',
        ARRAY[
            'Encumbrance Certificate',
            'Physical verification',
            'Preliminary report',
            '15 days photos',
            'Monthly videos',
            'Agreements & lease',
            'Realtime updates',
            'Cost feasibility and analysis report',
            'Priority support',
            'Dedicated property manager',
            'Asset upkeep (cleaning, maintenance)',
            'Analysis & revenue on property'
        ],
        '{"3": "Custom Quote", "6": "Custom Quote", "12": "Custom Quote"}'::jsonb,
        '{"3": "Custom Quote", "6": "Custom Quote", "12": "Custom Quote"}'::jsonb,
        'Platinum plan — full-scale property management with upkeep, dedicated manager, and revenue analysis.',
        'admin_001',
        TRUE,
        NOW(),
        NOW()
    );

-- BASIC - PLOT
INSERT INTO
    "PropCare".subscriptions_plans (
        sub_id,
        sub_type,
        category,
        services,
        durations,
        rental_percentages,
        comments,
        created_by,
        is_active,
        created_at,
        updated_at
    )
VALUES (
        'VPC_SUB_004',
        'BASIC',
        'PLOT',
        ARRAY[
            'Monthly Photos',
            'Encumbrance Certificate',
            'Physical verification',
            'Preliminary report',
            'Bi-monthly videos'
        ],
        '{"3": 3999, "6": 6499, "12": 10999}'::jsonb,
        '{"3": 25, "6": 25, "12": 25}'::jsonb,
        'Basic plot management package with regular visual updates and verifications.',
        'admin_001',
        TRUE,
        NOW(),
        NOW()
    );

-- GOLD - PLOT
INSERT INTO
    "PropCare".subscriptions_plans (
        sub_id,
        sub_type,
        category,
        services,
        durations,
        rental_percentages,
        comments,
        created_by,
        is_active,
        created_at,
        updated_at
    )
VALUES (
        'VPC_SUB_005',
        'GOLD',
        'PLOT',
        ARRAY[
            'Encumbrance Certificate',
            '15 days photos',
            'Physical verification',
            'Preliminary report',
            'Monthly videos',
            'Agreements & lease',
            'Realtime updates',
            'Cost feasibility and analysis report',
            'Priority support'
        ],
        '{"3": 4999, "6": 7999, "12": 12999}'::jsonb,
        '{"3": 25, "6": 25, "12": 25}'::jsonb,
        'Gold package — detailed plot management with agreements and real-time updates.',
        'admin_001',
        TRUE,
        NOW(),
        NOW()
    );

-- PLATINUM - PLOT
INSERT INTO
    "PropCare".subscriptions_plans (
        sub_id,
        sub_type,
        category,
        services,
        durations,
        rental_percentages,
        comments,
        created_by,
        is_active,
        created_at,
        updated_at
    )
VALUES (
        'VPC_SUB_006',
        'PLATINUM',
        'PLOT',
        ARRAY[
            'Encumbrance Certificate',
            '15 days photos',
            'Physical verification',
            'Preliminary report',
            'Monthly videos',
            'Agreements & lease',
            'Realtime updates',
            'Cost feasibility and analysis report',
            'Priority support',
            'Dedicated property manager',
            'Asset upkeep (cleaning, maintenance)',
            'Analysis & revenue on property'
        ],
        '{"3": "Custom Quote", "6": "Custom Quote", "12": "Custom Quote"}'::jsonb,
        '{"3": "Custom Quote", "6": "Custom Quote", "12": "Custom Quote"}'::jsonb,
        'Platinum package — complete property lifecycle management with dedicated manager and analysis.',
        'admin_001',
        TRUE,
        NOW(),
        NOW()
    );

python - m celery - A background_task.celery_app.celery_app worker --loglevel=info
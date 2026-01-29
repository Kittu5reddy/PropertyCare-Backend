INSERT INTO
    subscriptions_plans (
        sub_id,
        sub_type,
        category,
        services,
        durations,
        rental_percentages,
        comments,
        created_by,
        is_active
    )
VALUES (
        'BASIC_001',
        'Basic',
        'Flats',
        ARRAY[
            'Rental services',
            'Tenant management',
            'Agreement with tenant',
            'Tenant verification',
            'Quarterly physical inspections',
            'Preliminary report'
        ],
        '{"3": "3999", "6": "6499", "12": "10999"}',
        7,
        'Basic rental management plan',
        'ADMIN001',
        TRUE
    ),
    (
        'GOLD_001',
        'Gold',
        'Flats',
        ARRAY[
            'Rental services',
            'Tenant management',
            'Agreement with tenant',
            'Tenant verification',
            'Quarterly inspections',
            'Quarterly walkthrough',
            'Utility coordination',
            'Dedicated property manager'
        ],
        '{"3": "4999", "6": "7999", "12": "12999"}',
        9,
        'Most popular gold plan',
        'ADMIN001',
        TRUE
    ),
    (
        'PLOTS_BASIC_001',
        'Basic',
        'Plots',
        ARRAY[
            'Monthly photos',
            'Encumbrance Certificate',
            'Physical verification',
            'Preliminary report',
            'Bi-monthly videos'
        ],
        '{"3": "3999","6":"6499","10999":"12"}',
        0,
        'Basic plots monitoring plan (400 sq yards)',
        'ADMIN001',
        TRUE
    ),
    (
        'PLOTS_GOLD_001',
        'Gold',
        'Plots',
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
            'Dedicated property manager'
        ],
        '{"3": "4999","6":"7999","12":"12999"}',
        0,
        'Gold plots monitoring plan (400 sq yards)',
        'ADMIN001',
        TRUE
    );
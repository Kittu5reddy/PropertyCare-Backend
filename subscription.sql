/
/
plots / / BASIC

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
        is_active
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
        '{"3": "3999", "6": 6499, "12": "10999"}',
        "7",
        'ntg',
        'admin_001',
        TRUE
    );

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
        is_active
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
        '{"3": "4999", "6": "7999", "12": "12999"}',
        "9",
        'ntg',
        'admin_001',
        TRUE
    );

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
        is_active
    )
VALUES (
        'VPC_SUB_003',
        'Platinum',
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
        '{"3": "Custom Quote", "6": "Custom Quote", "12": "Custom Quote"}',
        "Custom Quote",
        'Platinum plan offers full-scale property management with upkeep, dedicated manager, and revenue analysis.',
        'admin_001',
        TRUE
    );

/
/
flats

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
        is_active
    )
VALUES (
        'VPC_SUB_004',
        'BASIC',
        'PLOT',
        ARRAY[
            'Monthly Photos',
            'Encumbrance Certificate',
            'Physical verification',
            'Perminary report',
            'Bi-monthly videos',
        ],
        '{"3": 3999, "6": 6499, "12": 10999}',
        25,
        'BASIC PACKAGE',
        'admin_001',
        TRUE
    );

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
        is_active
    )
VALUES (
        'VPC_SUB_005',
        'GOLD',
        'PLOT',
        ARRAY[
            'Encumbrance Certificate',
            '15 days photos',
            'Physical verification',
            'Perminary report',
            'Monthly videos',
            'Agreements & lease',
            'Realtime updates',
            'Cost feasibility and analysis report',
            'Priority support',
        ],
        '{"3": 4999, "6": 7999, "12": 12999}',
        25,
        'BASIC PACKAGE',
        'admin_001',
        TRUE
    );

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
        is_active
    )
VALUES (
        'VPC_SUB_006',
        'GOLD',
        'PLOT',
        ARRAY[
            'Encumbrance Certificate',
            '15 days photos',
            'Physical verification',
            'Perminary report',
            'Monthly videos',
            'Agreements & lease',
            'Realtime updates',
            'Cost feasibility and analysis report',
            'Priority support',
            'Dedicated property manager',
            'Asset upkeep (cleaning, maintenance)',
            'Analysis & revenue on property',
        ],
        '{"3": "Custom Quote", "6": "Custom Quote", "12": "Custom Quote"}',
        "Custom Quote",
        'BASIC PACKAGE',
        'admin_001',
        TRUE
    );
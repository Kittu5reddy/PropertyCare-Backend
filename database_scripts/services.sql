INSERT INTO services (
    service_id,
    service_name,
    category,
    services,
    starting_price,
    applicable_to,
    comments,
    short_comments,
    is_active
)
VALUES
(
    'SERV001',
    'Deep Cleaning',
    'Cleaning',
    ARRAY[
        'Seasonal Cleaning',
        'Move-in Cleaning'
    ],
    1800,
    ARRAY['PLOT', 'FLAT'],
    'Experience 10× deep cleaning with eco-friendly solutions and industrial-grade tools, removing stains, dust, and allergens for a spotless and healthy environment.',
    'Seasonal & move-in deep cleaning service.',
    TRUE
),
(
    'SERV002',
    'Painting',
    'Painting',
    ARRAY[
        'Interior Painting',
        'Exterior Painting'
    ],
    2500,
    ARRAY['FLAT'],
    'Interior and exterior painting using high-grade, weather-resistant paints delivered with a smooth, professional finish.',
    'Interior & exterior painting services.',
    TRUE
),
(
    'SERV003',
    'Pest Control & Termite Treatment',
    'Pest Control',
    ARRAY[
        'Termite Treatment',
        'Cockroach Control',
        'Rodent Control',
        'Mosquito Control'
    ],
    1800,
    ARRAY['FLAT'],
    'Odour-free pest control and anti-termite treatment using certified, eco-friendly chemicals and advanced spray systems.',
    'Odour-free pest & termite treatment.',
    TRUE
),
(
    'SERV004',
    'Security Guard Management',
    'Security & Surveillance',
    ARRAY[
        '24x7 Security',
        'Visitor Management',
        'On-site Protection'
    ],
    3500,
    ARRAY['FLAT', 'PLOT'],
    'Trained and background-verified security guards providing 24×7 protection with professional supervision and visitor management.',
    '24×7 trained security guards.',
    TRUE
),
(
    'SERV005',
    'CCTV Installation & Maintenance',
    'Security & Surveillance',
    ARRAY[
        'IP Cameras',
        'DVR/NVR Setup',
        'Remote Monitoring',
        'Annual Maintenance'
    ],
    3500,
    ARRAY['FLAT'],
    'Installation of high-definition CCTV cameras, DVRs, and smart monitoring systems with periodic maintenance and remote access setup.',
    'HD CCTV installation & AMC.',
    TRUE
),
(
    'SERV006',
    'Post Construction Cleanup',
    'Cleaning',
    ARRAY[
        'Dust Removal',
        'Debris Removal',
        'Paint Mark Removal'
    ],
    2500,
    ARRAY['FLAT'],
    'Professional post-construction cleanup removing cement dust, paint marks, and debris for handover-ready spaces.',
    'Post-construction property cleanup.',
    TRUE
),
(
    'SERV007',
    'Interior Design & Modular Kitchen',
    'Interiors',
    ARRAY[
        '3D Design',
        'Modular Kitchen',
        'Turnkey Interiors'
    ],
    5000,
    ARRAY['FLAT'],
    'Custom interior design and modular kitchen solutions blending functionality with modern aesthetics.',
    'Turnkey interior & modular kitchen.',
    TRUE
),
(
    'SERV008',
    'Move-in & Move-out Logistics',
    'Logistics',
    ARRAY[
        'Packing',
        'Loading',
        'Transport',
        'Unpacking'
    ],
    3000,
    ARRAY['FLAT'],
    'End-to-end relocation service including packing, transport, and unpacking with insured professionals.',
    'End-to-end relocation support.',
    TRUE
),
(
    'SERV009',
    'Fencing',
    'Infrastructure',
    ARRAY[
        'Barbed Wire',
        'Chain-link',
        'Concrete Fencing'
    ],
    4200,
    ARRAY['PLOT'],
    'High-quality fencing solutions with layout marking, material procurement, and installation.',
    'Secure durable fencing solutions.',
    TRUE
),
(
    'SERV010',
    'Surveying',
    'Surveying',
    ARRAY[
        'GPS Survey',
        'Total Station Survey',
        'Boundary Check'
    ],
    1500,
    ARRAY['PLOT'],
    'Accurate land surveying using GPS and total-station equipment with detailed site maps.',
    'GPS & total-station land surveying.',
    TRUE
),
(
    'SERV011',
    'Landscaping & Lawn Care',
    'Landscaping',
    ARRAY[
        'Garden Design',
        'Lawn Care',
        'Drip Irrigation'
    ],
    2200,
    ARRAY['PLOT'],
    'Professional landscaping with seasonal lawn care, irrigation systems, and decorative gardening.',
    'Landscaping & lawn-care services.',
    TRUE
);

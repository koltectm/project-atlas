-- =============================================================================
-- PROJECT ATLAS — Phase 1, Deliverable 2
-- Seed Data: Nigerian Oil & Gas Supply Chain
-- PostgreSQL 15+ / Supabase
-- All UUIDs are hardcoded for consistent FK cross-references
-- Reference: Nigeria crude production ~1.3–1.5M bpd (2023-2024)
-- =============================================================================

BEGIN;

-- =============================================================================
-- SECTION A: SUPPLY CHAIN NODES (40 nodes)
-- =============================================================================

INSERT INTO supply_chain_nodes (
  node_id, node_name, node_code, node_type, stage,
  latitude, longitude, state_location, geopolitical_zone,
  address_description, operator, operator_type,
  capacity_bpd, current_utilization_pct,
  annual_throughput_barrels,
  status, redundancy_score, criticality_score,
  mean_time_between_failures_days, mean_time_to_repair_days,
  daily_operating_cost_usd, replacement_cost_usd, metadata
) VALUES

-- -------------------------------------------------------------------------
-- UPSTREAM: Wellheads / Oil Fields (8 nodes)
-- -------------------------------------------------------------------------
(
  'a1000000-0000-0000-0000-000000000001',
  'Bonny Oil Field', 'BONNY-WH-001', 'wellhead', 'upstream',
  4.4392, 7.1614, 'Rivers State', 'SS',
  'Bonny Island, Rivers State — onshore/shallow offshore producing area',
  'Shell Petroleum Development Company (SPDC)', 'IOC',
  200000, 0.72, 52560000,
  'operational', 0.45, 0.82,
  210.0, 14.0, 850000, 2800000000,
  '{"oml_number": "OML 11/18/27/28", "discovery_year": 1956, "field_type": "onshore_offshore", "crude_grade": "Bonny Light", "api_gravity": 32.9, "sulfur_pct": 0.14}'
),
(
  'a1000000-0000-0000-0000-000000000002',
  'Forcados Oil Field', 'FORC-WH-001', 'wellhead', 'upstream',
  5.3522, 5.5019, 'Delta State', 'SS',
  'Forcados River Delta, Delta State',
  'Shell Petroleum Development Company (SPDC)', 'IOC',
  150000, 0.65, 35587500,
  'operational', 0.40, 0.78,
  180.0, 12.0, 680000, 2200000000,
  '{"oml_number": "OML 25/26/61/62", "discovery_year": 1964, "field_type": "onshore_swamp", "crude_grade": "Forcados Blend", "api_gravity": 29.5, "sulfur_pct": 0.18}'
),
(
  'a1000000-0000-0000-0000-000000000003',
  'Escravos Oil Field', 'ESCR-WH-001', 'wellhead', 'upstream',
  5.5959, 5.2024, 'Delta State', 'SS',
  'Escravos River area, Delta State',
  'Chevron Nigeria Limited (CNL)', 'IOC',
  180000, 0.60, 39420000,
  'operational', 0.35, 0.80,
  195.0, 10.0, 750000, 2500000000,
  '{"oml_number": "OML 49/53/55", "discovery_year": 1958, "field_type": "onshore_swamp", "crude_grade": "Escravos Light", "api_gravity": 36.5, "sulfur_pct": 0.12}'
),
(
  'a1000000-0000-0000-0000-000000000004',
  'Brass Oil Field', 'BRASS-WH-001', 'wellhead', 'upstream',
  4.3127, 6.2405, 'Bayelsa State', 'SS',
  'Brass River area, Bayelsa State',
  'Nigerian Agip Oil Company (NAOC)', 'IOC',
  120000, 0.55, 24090000,
  'operational', 0.40, 0.70,
  200.0, 11.0, 520000, 1800000000,
  '{"oml_number": "OML 60/61/62/63", "discovery_year": 1961, "field_type": "onshore_swamp", "crude_grade": "Brass Blend", "api_gravity": 30.1, "sulfur_pct": 0.21}'
),
(
  'a1000000-0000-0000-0000-000000000005',
  'Qua Iboe Oil Field', 'QUAI-WH-001', 'wellhead', 'upstream',
  4.5241, 7.9821, 'Akwa Ibom State', 'SS',
  'Qua Iboe River, Akwa Ibom State',
  'ExxonMobil Producing Nigeria', 'IOC',
  220000, 0.68, 54604000,
  'operational', 0.50, 0.85,
  220.0, 9.0, 920000, 3100000000,
  '{"oml_number": "OML 67/68/70/104", "discovery_year": 1971, "field_type": "offshore_shallow", "crude_grade": "Qua Iboe Light", "api_gravity": 35.8, "sulfur_pct": 0.07}'
),
(
  'a1000000-0000-0000-0000-000000000006',
  'Agbami Deep Water Field', 'AGBA-WH-001', 'wellhead', 'upstream',
  3.8421, 5.2817, 'Offshore', 'SS',
  'OML 127/128, deep water offshore Niger Delta, ~110km from coast',
  'Chevron Nigeria Limited (CNL)', 'IOC',
  235000, 0.82, 70177500,
  'operational', 0.60, 0.88,
  300.0, 21.0, 1100000, 4500000000,
  '{"oml_number": "OML 127/128", "water_depth_m": 1500, "discovery_year": 1998, "field_type": "deepwater", "crude_grade": "Agbami", "api_gravity": 47.5, "sulfur_pct": 0.04}'
),
(
  'a1000000-0000-0000-0000-000000000007',
  'Egina Deep Water Field', 'EGIN-WH-001', 'wellhead', 'upstream',
  3.5180, 5.5921, 'Offshore', 'SS',
  'OML 130, deep water offshore Niger Delta, ~150km from coast, FPSO-based',
  'TotalEnergies EP Nigeria', 'IOC',
  200000, 0.78, 56940000,
  'operational', 0.65, 0.86,
  280.0, 18.0, 950000, 4200000000,
  '{"oml_number": "OML 130", "water_depth_m": 1750, "discovery_year": 2003, "field_type": "deepwater_fpso", "crude_grade": "Egina", "api_gravity": 28.9, "sulfur_pct": 0.33, "fpso_name": "Egina FPSO"}'
),
(
  'a1000000-0000-0000-0000-000000000008',
  'Erha Deep Water Field', 'ERHA-WH-001', 'wellhead', 'upstream',
  3.7200, 5.0300, 'Offshore', 'SS',
  'OML 133, deep water offshore, FPSO-operated by ExxonMobil',
  'ExxonMobil Producing Nigeria', 'IOC',
  150000, 0.70, 38325000,
  'operational', 0.62, 0.80,
  310.0, 22.0, 750000, 3800000000,
  '{"oml_number": "OML 133", "water_depth_m": 1200, "discovery_year": 1999, "field_type": "deepwater_fpso", "crude_grade": "Erha", "api_gravity": 33.5, "sulfur_pct": 0.08}'
),

-- -------------------------------------------------------------------------
-- MIDSTREAM: Export Terminals (6 nodes)
-- -------------------------------------------------------------------------
(
  'a2000000-0000-0000-0000-000000000001',
  'Bonny Export Terminal', 'BOND-ET-001', 'export_terminal', 'midstream',
  4.4476, 7.1569, 'Rivers State', 'SS',
  'Bonny Island, Rivers State — major crude oil export terminal',
  'Shell Petroleum Development Company (SPDC)', 'IOC',
  800000, 0.62, 181300000,
  'operational', 0.55, 0.90,
  365.0, 7.0, 1200000, 2000000000,
  '{"storage_tanks": 12, "tank_capacity_barrels": 5000000, "berths": 4, "max_tanker_dwt": 300000, "certification": "ISPS_compliant"}'
),
(
  'a2000000-0000-0000-0000-000000000002',
  'Forcados Export Terminal', 'FORC-ET-001', 'export_terminal', 'midstream',
  5.3611, 5.5153, 'Delta State', 'SS',
  'Forcados River, Delta State — offshore single buoy mooring terminal',
  'Shell Petroleum Development Company (SPDC)', 'IOC',
  400000, 0.58, 84680000,
  'degraded', 0.30, 0.82,
  180.0, 21.0, 850000, 1500000000,
  '{"terminal_type": "SBM", "storage_capacity_barrels": 2500000, "berths": 2, "incident_history": "Multiple sabotage incidents 2016-2024"}'
),
(
  'a2000000-0000-0000-0000-000000000003',
  'Escravos Export Terminal', 'ESCR-ET-001', 'export_terminal', 'midstream',
  5.5875, 5.2108, 'Delta State', 'SS',
  'Escravos River mouth, Delta State',
  'Chevron Nigeria Limited (CNL)', 'IOC',
  350000, 0.65, 83037500,
  'operational', 0.48, 0.79,
  240.0, 10.0, 780000, 1400000000,
  '{"terminal_type": "fixed_platform", "storage_capacity_barrels": 2000000, "berths": 3, "gas_processing_mmscfd": 180}'
),
(
  'a2000000-0000-0000-0000-000000000004',
  'Brass Export Terminal', 'BRAS-ET-001', 'export_terminal', 'midstream',
  4.3021, 6.2387, 'Bayelsa State', 'SS',
  'Brass River mouth, Bayelsa State',
  'Nigerian Agip Oil Company (NAOC)', 'IOC',
  200000, 0.55, 40150000,
  'operational', 0.42, 0.72,
  200.0, 12.0, 520000, 900000000,
  '{"terminal_type": "offshore_monobuoy", "storage_capacity_barrels": 1500000, "berths": 2}'
),
(
  'a2000000-0000-0000-0000-000000000005',
  'Qua Iboe Export Terminal', 'QUAI-ET-001', 'export_terminal', 'midstream',
  4.5287, 7.9918, 'Akwa Ibom State', 'SS',
  'Eket, Akwa Ibom State — ExxonMobil flagship export facility',
  'ExxonMobil Producing Nigeria', 'IOC',
  600000, 0.70, 153300000,
  'operational', 0.60, 0.88,
  350.0, 8.0, 1100000, 2200000000,
  '{"terminal_type": "onshore_jetty", "storage_capacity_barrels": 4000000, "berths": 5, "certification": "ISO_14001"}'
),
(
  'a2000000-0000-0000-0000-000000000006',
  'Odudu Offshore Terminal', 'ODUD-ET-001', 'export_terminal', 'midstream',
  3.9800, 6.1200, 'Offshore', 'SS',
  'OML 100/115/135 area, offshore, TotalEnergies operated',
  'TotalEnergies EP Nigeria', 'IOC',
  300000, 0.72, 78840000,
  'operational', 0.55, 0.75,
  290.0, 15.0, 680000, 1300000000,
  '{"terminal_type": "floating_storage", "storage_capacity_barrels": 2200000, "berths": 2}'
),

-- -------------------------------------------------------------------------
-- MIDSTREAM: Refineries (4 nodes)
-- -------------------------------------------------------------------------
(
  'a3000000-0000-0000-0000-000000000001',
  'Port Harcourt Refining Company', 'PHRC-REF-001', 'refinery', 'midstream',
  4.8396, 6.9186, 'Rivers State', 'SS',
  'Alesa-Eleme, Port Harcourt, Rivers State',
  'Nigerian National Petroleum Corporation (NNPC)', 'NNPC',
  210000, 0.28, 21474000,
  'degraded', 0.25, 0.85,
  45.0, 60.0, 1200000, 4500000000,
  '{"commissioned_year": 1965, "rehabilitation_status": "ongoing", "units": ["CDU", "VDU", "HCU", "FCC"], "products": ["PMS", "AGO", "DPK", "LPG"], "current_capacity_pct": 28}'
),
(
  'a3000000-0000-0000-0000-000000000002',
  'Warri Refining and Petrochemical Company', 'WRPC-REF-001', 'refinery', 'midstream',
  5.5316, 5.7464, 'Delta State', 'SS',
  'Ekpan, Warri, Delta State',
  'Nigerian National Petroleum Corporation (NNPC)', 'NNPC',
  125000, 0.18, 8212500,
  'degraded', 0.20, 0.80,
  40.0, 75.0, 900000, 3200000000,
  '{"commissioned_year": 1978, "rehabilitation_status": "partial", "units": ["CDU", "VDU", "FCC", "alkylation"], "products": ["PMS", "AGO", "DPK", "polypropylene"], "current_capacity_pct": 18}'
),
(
  'a3000000-0000-0000-0000-000000000003',
  'Kaduna Refining and Petrochemical Company', 'KRPC-REF-001', 'refinery', 'midstream',
  10.5222, 7.4382, 'Kaduna State', 'NW',
  'Kaduna, Kaduna State — inland refinery serving the North',
  'Nigerian National Petroleum Corporation (NNPC)', 'NNPC',
  110000, 0.12, 4818000,
  'degraded', 0.15, 0.75,
  35.0, 90.0, 750000, 2800000000,
  '{"commissioned_year": 1980, "pipeline_dependence": "New_Warri_Kaduna_Pipeline", "products": ["PMS", "AGO", "DPK", "lubricants"], "current_capacity_pct": 12}'
),
(
  'a3000000-0000-0000-0000-000000000004',
  'Dangote Petroleum Refinery', 'DANG-REF-001', 'refinery', 'midstream',
  6.4090, 3.3800, 'Lagos State', 'SW',
  'Lekki Free Trade Zone, Lagos State — world-class single-train refinery',
  'Dangote Industries Limited', 'Indigenous',
  650000, 0.45, 106762500,
  'operational', 0.70, 0.95,
  200.0, 14.0, 4500000, 20000000000,
  '{"commissioned_year": 2023, "single_train": true, "complexity_nelson_index": 10.5, "crude_flexibility": true, "products": ["PMS", "AGO", "DPK", "LPG", "jet_fuel", "petrochemicals"], "polypropylene_tpa": 500000}'
),

-- -------------------------------------------------------------------------
-- MIDSTREAM: Storage Depots (8 nodes)
-- -------------------------------------------------------------------------
(
  'a4000000-0000-0000-0000-000000000001',
  'Atlas Cove Petroleum Depot', 'ATCV-DEP-001', 'storage_depot', 'midstream',
  6.3922, 3.3512, 'Lagos State', 'SW',
  'Atlas Cove, Lagos Harbour — primary petroleum products import/storage facility',
  'Nigerian National Petroleum Corporation (NNPC)', 'NNPC',
  0, 0.82, 0,
  'operational', 0.50, 0.88,
  120.0, 7.0, 800000, 1500000000,
  '{"storage_capacity_m3": 550000, "product_types": ["PMS", "AGO", "DPK"], "jetties": 6, "pipeline_connected": ["MOSIMI", "PPMC_SW"]}'
),
(
  'a4000000-0000-0000-0000-000000000002',
  'Mosimi Petroleum Depot', 'MOSM-DEP-001', 'storage_depot', 'midstream',
  6.8089, 3.5025, 'Ogun State', 'SW',
  'Mosimi, Ogun State — key SW distribution hub connected to Atlas Cove by pipeline',
  'Nigerian National Petroleum Corporation (NNPC)', 'NNPC',
  0, 0.75, 0,
  'operational', 0.45, 0.82,
  150.0, 5.0, 550000, 900000000,
  '{"storage_capacity_m3": 220000, "product_types": ["PMS", "AGO", "DPK"], "pipeline_km_to_atlas_cove": 65}'
),
(
  'a4000000-0000-0000-0000-000000000003',
  'Ibadan Satellite Depot', 'IBAD-DEP-001', 'storage_depot', 'midstream',
  7.3775, 3.9470, 'Oyo State', 'SW',
  'Ibadan, Oyo State',
  'Nigerian National Petroleum Corporation (NNPC)', 'NNPC',
  0, 0.70, 0,
  'operational', 0.35, 0.72,
  90.0, 4.0, 320000, 450000000,
  '{"storage_capacity_m3": 80000, "product_types": ["PMS", "AGO", "DPK"]}'
),
(
  'a4000000-0000-0000-0000-000000000004',
  'Ore Satellite Depot', 'ORE--DEP-001', 'storage_depot', 'midstream',
  6.9801, 4.8550, 'Ondo State', 'SW',
  'Ore, Ondo State',
  'Nigerian National Petroleum Corporation (NNPC)', 'NNPC',
  0, 0.65, 0,
  'operational', 0.30, 0.65,
  120.0, 5.0, 220000, 320000000,
  '{"storage_capacity_m3": 60000, "product_types": ["PMS", "AGO"]}'
),
(
  'a4000000-0000-0000-0000-000000000005',
  'Enugu Satellite Depot', 'ENUG-DEP-001', 'storage_depot', 'midstream',
  6.4698, 7.5156, 'Enugu State', 'SE',
  'Enugu, Enugu State',
  'Nigerian National Petroleum Corporation (NNPC)', 'NNPC',
  0, 0.60, 0,
  'operational', 0.30, 0.68,
  100.0, 5.0, 250000, 380000000,
  '{"storage_capacity_m3": 75000, "product_types": ["PMS", "AGO", "DPK"]}'
),
(
  'a4000000-0000-0000-0000-000000000006',
  'Kano Satellite Depot', 'KANO-DEP-001', 'storage_depot', 'midstream',
  12.0022, 8.5920, 'Kano State', 'NW',
  'Kano, Kano State — critical northern distribution hub',
  'Nigerian National Petroleum Corporation (NNPC)', 'NNPC',
  0, 0.72, 0,
  'operational', 0.35, 0.78,
  110.0, 6.0, 380000, 520000000,
  '{"storage_capacity_m3": 100000, "product_types": ["PMS", "AGO", "DPK", "LPG"], "serves_population_million": 12}'
),
(
  'a4000000-0000-0000-0000-000000000007',
  'Makurdi Satellite Depot', 'MAKU-DEP-001', 'storage_depot', 'midstream',
  7.7304, 8.5221, 'Benue State', 'NC',
  'Makurdi, Benue State',
  'Nigerian National Petroleum Corporation (NNPC)', 'NNPC',
  0, 0.55, 0,
  'operational', 0.25, 0.60,
  130.0, 6.0, 180000, 280000000,
  '{"storage_capacity_m3": 55000, "product_types": ["PMS", "AGO"]}'
),
(
  'a4000000-0000-0000-0000-000000000008',
  'Gombe Satellite Depot', 'GOMB-DEP-001', 'storage_depot', 'midstream',
  10.2896, 11.1673, 'Gombe State', 'NE',
  'Gombe, Gombe State',
  'Nigerian National Petroleum Corporation (NNPC)', 'NNPC',
  0, 0.50, 0,
  'operational', 0.20, 0.58,
  140.0, 7.0, 150000, 240000000,
  '{"storage_capacity_m3": 45000, "product_types": ["PMS", "AGO"]}'
),

-- -------------------------------------------------------------------------
-- DOWNSTREAM: Ports (4 nodes)
-- -------------------------------------------------------------------------
(
  'a5000000-0000-0000-0000-000000000001',
  'Apapa Port Complex', 'APAP-PORT-001', 'port', 'downstream',
  6.4498, 3.3582, 'Lagos State', 'SW',
  'Apapa, Lagos — primary national port handling ~70% of liquid cargo imports',
  'Nigerian Ports Authority (NPA)', 'Government',
  0, 0.88, 0,
  'degraded', 0.35, 0.95,
  60.0, 14.0, 3500000, 5000000000,
  '{"berths": 42, "congestion_index": 0.88, "avg_vessel_wait_days": 14, "annual_throughput_mt": 35000000, "bottleneck": "Apapa_road_access"}'
),
(
  'a5000000-0000-0000-0000-000000000002',
  'Tin Can Island Port', 'TINC-PORT-001', 'port', 'downstream',
  6.4350, 3.3198, 'Lagos State', 'SW',
  'Tin Can Island, Lagos',
  'Nigerian Ports Authority (NPA)', 'Government',
  0, 0.80, 0,
  'operational', 0.42, 0.82,
  80.0, 10.0, 2200000, 3000000000,
  '{"berths": 24, "congestion_index": 0.70, "annual_throughput_mt": 18000000}'
),
(
  'a5000000-0000-0000-0000-000000000003',
  'Onne Port Complex', 'ONNE-PORT-001', 'port', 'downstream',
  4.7095, 7.1574, 'Rivers State', 'SS',
  'Onne, Rivers State — oil & gas services hub, free trade zone',
  'Nigerian Ports Authority (NPA)', 'Government',
  0, 0.70, 0,
  'operational', 0.50, 0.78,
  100.0, 8.0, 1800000, 2500000000,
  '{"berths": 18, "free_trade_zone": true, "specialization": "oil_gas_services", "annual_throughput_mt": 12000000}'
),
(
  'a5000000-0000-0000-0000-000000000004',
  'Calabar Port', 'CALA-PORT-001', 'port', 'downstream',
  4.9517, 8.3220, 'Cross River State', 'SS',
  'Calabar, Cross River State',
  'Nigerian Ports Authority (NPA)', 'Government',
  0, 0.55, 0,
  'operational', 0.45, 0.65,
  120.0, 6.0, 850000, 1200000000,
  '{"berths": 12, "annual_throughput_mt": 5000000, "deepening_project": "planned"}'
),

-- -------------------------------------------------------------------------
-- DOWNSTREAM: Distribution Hubs (6 nodes)
-- -------------------------------------------------------------------------
(
  'a6000000-0000-0000-0000-000000000001',
  'South-West Distribution Hub (Lagos)', 'SWDH-HUB-001', 'distribution_hub', 'downstream',
  6.5244, 3.3792, 'Lagos State', 'SW',
  'Lagos metropolitan area distribution coordination point',
  'NNPC Retail Limited', 'NNPC',
  0, 0.85, 0,
  'operational', 0.40, 0.88,
  75.0, 4.0, 950000, 800000000,
  '{"population_served_million": 22, "retail_stations": 1200, "zone": "Lagos_Ogun_Oyo_Osun_Ondo_Ekiti"}'
),
(
  'a6000000-0000-0000-0000-000000000002',
  'South-East Distribution Hub (Enugu)', 'SEDH-HUB-001', 'distribution_hub', 'downstream',
  6.4698, 7.5156, 'Enugu State', 'SE',
  'Enugu metropolitan area distribution coordination point',
  'NNPC Retail Limited', 'NNPC',
  0, 0.72, 0,
  'operational', 0.35, 0.72,
  90.0, 5.0, 420000, 350000000,
  '{"population_served_million": 8, "retail_stations": 420, "zone": "Enugu_Anambra_Imo_Abia_Ebonyi"}'
),
(
  'a6000000-0000-0000-0000-000000000003',
  'North-West Distribution Hub (Kano)', 'NWDH-HUB-001', 'distribution_hub', 'downstream',
  12.0022, 8.5920, 'Kano State', 'NW',
  'Kano metropolitan area distribution coordination point',
  'NNPC Retail Limited', 'NNPC',
  0, 0.78, 0,
  'operational', 0.38, 0.80,
  80.0, 5.0, 520000, 450000000,
  '{"population_served_million": 18, "retail_stations": 680, "zone": "Kano_Katsina_Sokoto_Kebbi_Zamfara"}'
),
(
  'a6000000-0000-0000-0000-000000000004',
  'North-Central Distribution Hub (Abuja)', 'NCDH-HUB-001', 'distribution_hub', 'downstream',
  9.0765, 7.3986, 'FCT Abuja', 'NC',
  'Federal Capital Territory distribution coordination point',
  'NNPC Retail Limited', 'NNPC',
  0, 0.80, 0,
  'operational', 0.42, 0.82,
  85.0, 4.0, 480000, 400000000,
  '{"population_served_million": 12, "retail_stations": 520, "zone": "FCT_Kogi_Benue_Niger_Plateau_Nasarawa"}'
),
(
  'a6000000-0000-0000-0000-000000000005',
  'North-East Distribution Hub (Maiduguri)', 'NEDH-HUB-001', 'distribution_hub', 'downstream',
  11.8469, 13.1571, 'Borno State', 'NE',
  'Maiduguri, Borno State — serving the farthest distribution point',
  'NNPC Retail Limited', 'NNPC',
  0, 0.55, 0,
  'operational', 0.20, 0.65,
  150.0, 8.0, 220000, 280000000,
  '{"population_served_million": 9, "retail_stations": 310, "zone": "Borno_Yobe_Gombe_Adamawa_Bauchi_Taraba", "security_risk": "high"}'
),
(
  'a6000000-0000-0000-0000-000000000006',
  'South-South Distribution Hub (Warri)', 'SSDH-HUB-001', 'distribution_hub', 'downstream',
  5.5177, 5.7521, 'Delta State', 'SS',
  'Warri, Delta State — Niger Delta distribution hub',
  'NNPC Retail Limited', 'NNPC',
  0, 0.75, 0,
  'operational', 0.38, 0.75,
  80.0, 5.0, 380000, 350000000,
  '{"population_served_million": 10, "retail_stations": 450, "zone": "Delta_Rivers_Bayelsa_Akwa_Ibom_Cross_River_Edo"}'
),

-- -------------------------------------------------------------------------
-- DOWNSTREAM: Consumer Nodes (4 nodes)
-- -------------------------------------------------------------------------
(
  'a7000000-0000-0000-0000-000000000001',
  'Industrial Consumers Cluster (Lagos)', 'LIND-CON-001', 'consumer', 'downstream',
  6.5530, 3.3020, 'Lagos State', 'SW',
  'Lagos industrial belt — manufacturing, power generation, Lekki FTZ',
  'Various', 'Mixed',
  0, 0.90, 0,
  'operational', 0.55, 0.72,
  30.0, 2.0, 0, 0,
  '{"daily_consumption_bpd": 45000, "sectors": ["manufacturing", "power_generation", "cement", "steel"], "lekki_ftz": true}'
),
(
  'a7000000-0000-0000-0000-000000000002',
  'Power Sector Consumers (Gas Plants)', 'GPOW-CON-001', 'consumer', 'downstream',
  6.0000, 6.5000, 'Multiple States', 'SS',
  'Niger Delta gas-to-power plants — Sapele, Delta IV, Olorunsogo',
  'Various Power Companies', 'Mixed',
  0, 0.75, 0,
  'operational', 0.40, 0.70,
  45.0, 3.0, 0, 0,
  '{"daily_gas_consumption_mmscfd": 800, "installed_capacity_mw": 4500, "plants": ["Sapele_IPP", "Delta_IV", "Olorunsogo", "Omotosho"]}'
),
(
  'a7000000-0000-0000-0000-000000000003',
  'Export Market (International Tankers)', 'XPRT-CON-001', 'consumer', 'downstream',
  3.5000, 4.0000, 'Offshore', 'SS',
  'International crude oil export market — aggregate representation',
  'Various International Buyers', 'International',
  0, 0.85, 0,
  'operational', 0.80, 0.75,
  14.0, 1.0, 0, 0,
  '{"primary_markets": ["Europe", "Asia", "Americas"], "avg_cargo_size_barrels": 1000000, "avg_liftings_per_month": 45}'
),
(
  'a7000000-0000-0000-0000-000000000004',
  'Retail Fuel Stations (Nationwide)', 'RTFL-CON-001', 'consumer', 'downstream',
  9.0820, 8.6753, 'Multiple States', 'NC',
  'Aggregate representation of ~5,000+ retail fuel stations nationwide',
  'NNPC Retail / Ardova / Conoil / TotalEnergies / MRS', 'Mixed',
  0, 0.78, 0,
  'operational', 0.60, 0.68,
  20.0, 1.0, 0, 0,
  '{"station_count": 5200, "daily_petrol_demand_bpd": 280000, "daily_diesel_demand_bpd": 120000, "daily_kerosene_demand_bpd": 40000}'
);

-- =============================================================================
-- SECTION B: SUPPLY CHAIN LINKS (52 links)
-- =============================================================================

INSERT INTO supply_chain_links (
  link_id, link_name, link_code, link_type,
  source_node_id, target_node_id,
  distance_km, diameter_inches, pipeline_year_installed,
  normal_lead_time_days, transport_cost_per_barrel, max_capacity_bpd,
  current_utilization_pct, reliability_score, vandalism_risk_score,
  is_critical_path, status, metadata
) VALUES

-- -------------------------------------------------------------------------
-- Upstream → Export Terminals (Pipelines)
-- -------------------------------------------------------------------------
(
  'b1000000-0000-0000-0000-000000000001',
  'Trans Niger Pipeline — Bonny to Bonny Terminal',
  'TNP-L-001', 'pipeline',
  'a1000000-0000-0000-0000-000000000001',
  'a2000000-0000-0000-0000-000000000001',
  160.0, 24.0, 1966,
  1.5, 0.85, 450000, 0.72, 0.62, 0.78,
  TRUE, 'operational',
  '{"operator": "SPDC", "total_length_km": 600, "vandalism_incidents_2023": 47, "idle_capacity_note": "Frequent forced shutdowns"}'
),
(
  'b1000000-0000-0000-0000-000000000002',
  'Nembe Creek Trunk Line — Bonny to Bonny Terminal',
  'NCTL-L-001', 'pipeline',
  'a1000000-0000-0000-0000-000000000001',
  'a2000000-0000-0000-0000-000000000001',
  97.0, 28.0, 2001,
  1.0, 0.75, 500000, 0.65, 0.55, 0.82,
  TRUE, 'degraded',
  '{"operator": "SPDC", "high_vandalism_corridor": true, "bypass_line": "TNP", "incidents_since_commissioning": 320}'
),
(
  'b1000000-0000-0000-0000-000000000003',
  'Forcados Pipeline — Forcados Field to Terminal',
  'FORC-L-001', 'pipeline',
  'a1000000-0000-0000-0000-000000000002',
  'a2000000-0000-0000-0000-000000000002',
  85.0, 24.0, 1965,
  1.0, 0.90, 300000, 0.58, 0.50, 0.85,
  TRUE, 'degraded',
  '{"operator": "SPDC", "sabotage_events_per_year": 22, "force_majeure_days_2023": 48}'
),
(
  'b1000000-0000-0000-0000-000000000004',
  'Escravos Pipeline — Escravos Field to Terminal',
  'ESCR-L-001', 'pipeline',
  'a1000000-0000-0000-0000-000000000003',
  'a2000000-0000-0000-0000-000000000003',
  75.0, 24.0, 1960,
  0.8, 0.80, 350000, 0.65, 0.68, 0.70,
  TRUE, 'operational',
  '{"operator": "CNL", "cathodic_protection": "upgraded_2019"}'
),
(
  'b1000000-0000-0000-0000-000000000005',
  'Brass Pipeline — Brass Field to Terminal',
  'BRAS-L-001', 'pipeline',
  'a1000000-0000-0000-0000-000000000004',
  'a2000000-0000-0000-0000-000000000004',
  120.0, 20.0, 1975,
  1.2, 1.10, 200000, 0.55, 0.60, 0.72,
  FALSE, 'operational',
  '{"operator": "NAOC"}'
),
(
  'b1000000-0000-0000-0000-000000000006',
  'Qua Iboe Pipeline — QI Field to Terminal',
  'QUAI-L-001', 'pipeline',
  'a1000000-0000-0000-0000-000000000005',
  'a2000000-0000-0000-0000-000000000005',
  45.0, 30.0, 1972,
  0.5, 0.60, 600000, 0.70, 0.75, 0.45,
  TRUE, 'operational',
  '{"operator": "ExxonMobil", "pigging_schedule": "quarterly"}'
),
(
  'b1000000-0000-0000-0000-000000000007',
  'Agbami Subsea Export — Field to SBM',
  'AGBA-L-001', 'pipeline',
  'a1000000-0000-0000-0000-000000000006',
  'a2000000-0000-0000-0000-000000000001',
  115.0, 16.0, 2008,
  1.2, 0.45, 240000, 0.82, 0.92, 0.05,
  TRUE, 'operational',
  '{"type": "subsea_flowline", "water_depth_m": 1500, "cathodic_protection": "impressed_current"}'
),
(
  'b1000000-0000-0000-0000-000000000008',
  'Egina FPSO Offloading — Egina to Bonny',
  'EGIN-L-001', 'sea_route',
  'a1000000-0000-0000-0000-000000000007',
  'a2000000-0000-0000-0000-000000000001',
  200.0, NULL, NULL,
  2.0, 0.95, 200000, 0.78, 0.90, 0.02,
  FALSE, 'operational',
  '{"vessel_type": "shuttle_tanker", "shuttle_frequency_per_month": 4}'
),
(
  'b1000000-0000-0000-0000-000000000009',
  'Erha FPSO Offloading — Erha to Qua Iboe',
  'ERHA-L-001', 'sea_route',
  'a1000000-0000-0000-0000-000000000008',
  'a2000000-0000-0000-0000-000000000005',
  230.0, NULL, NULL,
  2.2, 1.00, 150000, 0.70, 0.88, 0.02,
  FALSE, 'operational',
  '{"vessel_type": "shuttle_tanker", "shuttle_frequency_per_month": 3}'
),

-- -------------------------------------------------------------------------
-- Export Terminals → Refineries (Sea + Pipeline)
-- -------------------------------------------------------------------------
(
  'b2000000-0000-0000-0000-000000000001',
  'Bonny Terminal to PHRC — Crude Supply Pipeline',
  'BOND-PHRC-L-001', 'pipeline',
  'a2000000-0000-0000-0000-000000000001',
  'a3000000-0000-0000-0000-000000000001',
  32.0, 20.0, 1965,
  0.4, 0.40, 250000, 0.28, 0.70, 0.35,
  TRUE, 'operational',
  '{"note": "Short onshore pipeline; Bonny Island to Alesa-Eleme refinery"}'
),
(
  'b2000000-0000-0000-0000-000000000002',
  'Escravos Terminal to Warri Refinery — Crude Supply',
  'ESCR-WRPC-L-001', 'pipeline',
  'a2000000-0000-0000-0000-000000000003',
  'a3000000-0000-0000-0000-000000000002',
  65.0, 18.0, 1978,
  0.7, 0.55, 150000, 0.18, 0.65, 0.42,
  TRUE, 'degraded',
  '{"condition": "aging", "last_inspection": "2021"}'
),
(
  'b2000000-0000-0000-0000-000000000003',
  'Warri to Kaduna Crude Pipeline',
  'WRPC-KRPC-L-001', 'pipeline',
  'a3000000-0000-0000-0000-000000000002',
  'a3000000-0000-0000-0000-000000000003',
  1050.0, 16.0, 1980,
  10.5, 2.20, 120000, 0.12, 0.45, 0.55,
  TRUE, 'degraded',
  '{"condition": "poor", "pump_stations": 6, "vandalism_risk_corridor": "Niger_Delta_to_North", "idle_segments_km": 280}'
),
(
  'b2000000-0000-0000-0000-000000000004',
  'Bonny Terminal to Dangote — Sea Tanker Route',
  'BOND-DANG-L-001', 'sea_route',
  'a2000000-0000-0000-0000-000000000001',
  'a3000000-0000-0000-0000-000000000004',
  520.0, NULL, NULL,
  2.5, 1.20, 400000, 0.45, 0.88, 0.02,
  TRUE, 'operational',
  '{"vessel_type": "aframax", "alternative": "Escravos_to_Dangote"}'
),
(
  'b2000000-0000-0000-0000-000000000005',
  'Escravos Terminal to Dangote — Sea Route',
  'ESCR-DANG-L-001', 'sea_route',
  'a2000000-0000-0000-0000-000000000003',
  'a3000000-0000-0000-0000-000000000004',
  450.0, NULL, NULL,
  2.2, 1.10, 300000, 0.40, 0.90, 0.02,
  FALSE, 'operational',
  '{"vessel_type": "aframax", "note": "Alternative to Bonny-Dangote route"}'
),

-- -------------------------------------------------------------------------
-- Refineries / Terminals → Atlas Cove / Storage Depots (Products)
-- -------------------------------------------------------------------------
(
  'b3000000-0000-0000-0000-000000000001',
  'Dangote Refinery to Apapa Port — Product Pipeline',
  'DANG-APAP-L-001', 'pipeline',
  'a3000000-0000-0000-0000-000000000004',
  'a5000000-0000-0000-0000-000000000001',
  22.0, 20.0, 2023,
  0.3, 0.30, 600000, 0.45, 0.95, 0.05,
  TRUE, 'operational',
  '{"new_infrastructure": true, "products": ["PMS", "AGO", "DPK", "LPG", "jet_fuel"]}'
),
(
  'b3000000-0000-0000-0000-000000000002',
  'Dangote to Atlas Cove — Products Pipeline',
  'DANG-ATCV-L-001', 'pipeline',
  'a3000000-0000-0000-0000-000000000004',
  'a4000000-0000-0000-0000-000000000001',
  18.0, 20.0, 2023,
  0.2, 0.28, 500000, 0.45, 0.95, 0.05,
  TRUE, 'operational',
  '{"products": ["PMS", "AGO", "DPK"]}'
),
(
  'b3000000-0000-0000-0000-000000000003',
  'Apapa Port to Atlas Cove — Marine Transfer',
  'APAP-ATCV-L-001', 'sea_route',
  'a5000000-0000-0000-0000-000000000001',
  'a4000000-0000-0000-0000-000000000001',
  5.0, NULL, NULL,
  0.1, 0.20, 800000, 0.82, 0.80, 0.02,
  TRUE, 'degraded',
  '{"note": "Apapa congestion is major bottleneck; avg wait 14 days"}'
),
(
  'b3000000-0000-0000-0000-000000000004',
  'PHRC to Onne Port — Products by Road/Truck',
  'PHRC-ONNE-L-001', 'road',
  'a3000000-0000-0000-0000-000000000001',
  'a5000000-0000-0000-0000-000000000003',
  28.0, NULL, NULL,
  0.3, 1.50, 50000, 0.28, 0.72, 0.28,
  FALSE, 'operational',
  '{"fleet_trucks": 180, "products": ["PMS", "AGO", "DPK"]}'
),
(
  'b3000000-0000-0000-0000-000000000005',
  'Import Crude — Apapa to Atlas Cove (Import tankers)',
  'IMPT-ATCV-L-001', 'sea_route',
  'a7000000-0000-0000-0000-000000000003',
  'a4000000-0000-0000-0000-000000000001',
  0.0, NULL, NULL,
  14.0, 8.50, 200000, 0.88, 0.60, 0.05,
  FALSE, 'degraded',
  '{"note": "Import route — Apapa port congestion causes 14-day average delays"}'
),

-- -------------------------------------------------------------------------
-- Atlas Cove / Depots to Distribution (PPMC Pipeline + Road)
-- -------------------------------------------------------------------------
(
  'b4000000-0000-0000-0000-000000000001',
  'Atlas Cove to Mosimi PPMC Pipeline',
  'ATCV-MOSM-L-001', 'pipeline',
  'a4000000-0000-0000-0000-000000000001',
  'a4000000-0000-0000-0000-000000000002',
  65.0, 12.0, 1978,
  0.8, 0.45, 120000, 0.75, 0.72, 0.20,
  TRUE, 'operational',
  '{"ppmc_segment": "SW1", "pump_stations": 2}'
),
(
  'b4000000-0000-0000-0000-000000000002',
  'Mosimi to Ibadan PPMC Pipeline',
  'MOSM-IBAD-L-001', 'pipeline',
  'a4000000-0000-0000-0000-000000000002',
  'a4000000-0000-0000-0000-000000000003',
  130.0, 10.0, 1982,
  1.5, 0.55, 80000, 0.70, 0.65, 0.22,
  FALSE, 'operational',
  '{"ppmc_segment": "SW2"}'
),
(
  'b4000000-0000-0000-0000-000000000003',
  'Mosimi to Ore Pipeline',
  'MOSM-ORE-L-001', 'pipeline',
  'a4000000-0000-0000-0000-000000000002',
  'a4000000-0000-0000-0000-000000000004',
  88.0, 10.0, 1985,
  1.0, 0.50, 60000, 0.65, 0.62, 0.25,
  FALSE, 'operational',
  '{"ppmc_segment": "SW3"}'
),
(
  'b4000000-0000-0000-0000-000000000004',
  'Warri PPMC Pipeline to Enugu',
  'SSDH-ENUG-L-001', 'pipeline',
  'a6000000-0000-0000-0000-000000000006',
  'a4000000-0000-0000-0000-000000000005',
  350.0, 10.0, 1980,
  4.0, 1.20, 55000, 0.60, 0.52, 0.48,
  FALSE, 'degraded',
  '{"ppmc_segment": "SE1", "frequent_vandalism": true}'
),
(
  'b4000000-0000-0000-0000-000000000005',
  'Kaduna Refinery to Kano by Road',
  'KRPC-KANO-L-001', 'road',
  'a3000000-0000-0000-0000-000000000003',
  'a4000000-0000-0000-0000-000000000006',
  195.0, NULL, NULL,
  1.0, 2.80, 40000, 0.72, 0.78, 0.15,
  TRUE, 'operational',
  '{"truck_fleet_size": 280, "road_quality": "fair", "products": ["PMS", "AGO", "DPK"]}'
),
(
  'b4000000-0000-0000-0000-000000000006',
  'Kaduna to Abuja Road',
  'KRPC-ABUJ-L-001', 'road',
  'a3000000-0000-0000-0000-000000000003',
  'a6000000-0000-0000-0000-000000000004',
  185.0, NULL, NULL,
  0.9, 2.60, 45000, 0.80, 0.80, 0.12,
  FALSE, 'operational',
  '{"road_quality": "good", "dual_carriageway": true}'
),
(
  'b4000000-0000-0000-0000-000000000007',
  'Kano Depot to Maiduguri — Road',
  'KANO-MAID-L-001', 'road',
  'a4000000-0000-0000-0000-000000000006',
  'a6000000-0000-0000-0000-000000000005',
  850.0, NULL, NULL,
  2.5, 4.20, 20000, 0.55, 0.50, 0.30,
  FALSE, 'operational',
  '{"road_quality": "poor_sections", "security_escort_required": true, "boko_haram_risk_corridor": true}'
),
(
  'b4000000-0000-0000-0000-000000000008',
  'Enugu Depot to SE Distribution Hub',
  'ENUG-SEDH-L-001', 'road',
  'a4000000-0000-0000-0000-000000000005',
  'a6000000-0000-0000-0000-000000000002',
  5.0, NULL, NULL,
  0.1, 0.50, 30000, 0.72, 0.82, 0.12,
  FALSE, 'operational',
  '{"note": "Short haul, same metro area"}'
),
(
  'b4000000-0000-0000-0000-000000000009',
  'Makurdi to NC Hub (Abuja) Road',
  'MAKU-ABUJ-L-001', 'road',
  'a4000000-0000-0000-0000-000000000007',
  'a6000000-0000-0000-0000-000000000004',
  320.0, NULL, NULL,
  1.5, 3.10, 25000, 0.55, 0.68, 0.18,
  FALSE, 'operational',
  '{"road_quality": "fair", "bridging_point": "Niger_River_bridge"}'
),
(
  'b4000000-0000-0000-0000-000000000010',
  'Gombe to NE Distribution Hub',
  'GOMB-NEDH-L-001', 'road',
  'a4000000-0000-0000-0000-000000000008',
  'a6000000-0000-0000-0000-000000000005',
  480.0, NULL, NULL,
  1.8, 4.80, 18000, 0.50, 0.55, 0.28,
  FALSE, 'operational',
  '{"road_quality": "poor", "security_risk": "elevated"}'
),

-- -------------------------------------------------------------------------
-- Distribution Hubs to Consumer Nodes
-- -------------------------------------------------------------------------
(
  'b5000000-0000-0000-0000-000000000001',
  'SW Hub Lagos to Industrial Consumers',
  'SWDH-LIND-L-001', 'road',
  'a6000000-0000-0000-0000-000000000001',
  'a7000000-0000-0000-0000-000000000001',
  25.0, NULL, NULL,
  0.3, 0.80, 50000, 0.90, 0.85, 0.05,
  FALSE, 'operational',
  '{"delivery_mode": "tanker_trucks", "daily_trips": 120}'
),
(
  'b5000000-0000-0000-0000-000000000002',
  'SW Hub to Retail Fuel Stations (SW Zone)',
  'SWDH-RTFL-L-001', 'road',
  'a6000000-0000-0000-0000-000000000001',
  'a7000000-0000-0000-0000-000000000004',
  50.0, NULL, NULL,
  0.5, 1.20, 150000, 0.85, 0.82, 0.08,
  FALSE, 'operational',
  '{"delivery_mode": "tanker_trucks", "stations_served": 1200}'
),
(
  'b5000000-0000-0000-0000-000000000003',
  'NW Hub Kano to Retail Stations (NW Zone)',
  'NWDH-RTFL-L-001', 'road',
  'a6000000-0000-0000-0000-000000000003',
  'a7000000-0000-0000-0000-000000000004',
  200.0, NULL, NULL,
  1.0, 2.50, 80000, 0.78, 0.75, 0.15,
  FALSE, 'operational',
  '{"delivery_mode": "tanker_trucks", "stations_served": 680}'
),
(
  'b5000000-0000-0000-0000-000000000004',
  'SS Hub Warri to Power Plants',
  'SSDH-GPOW-L-001', 'pipeline',
  'a6000000-0000-0000-0000-000000000006',
  'a7000000-0000-0000-0000-000000000002',
  120.0, 12.0, 2005,
  1.4, 0.60, 80000, 0.75, 0.78, 0.25,
  FALSE, 'operational',
  '{"product": "gas_condensate_AGO"}'
),
(
  'b5000000-0000-0000-0000-000000000005',
  'Bonny Export to International Market (VLCC)',
  'BOND-XPRT-L-001', 'sea_route',
  'a2000000-0000-0000-0000-000000000001',
  'a7000000-0000-0000-0000-000000000003',
  5000.0, NULL, NULL,
  7.0, 1.80, 600000, 0.62, 0.92, 0.02,
  TRUE, 'operational',
  '{"vessel_type": "VLCC", "primary_destinations": ["Rotterdam", "Houston", "Qingdao"]}'
),
(
  'b5000000-0000-0000-0000-000000000006',
  'Qua Iboe Export to International Market',
  'QUAI-XPRT-L-001', 'sea_route',
  'a2000000-0000-0000-0000-000000000005',
  'a7000000-0000-0000-0000-000000000003',
  5500.0, NULL, NULL,
  7.5, 1.85, 500000, 0.70, 0.93, 0.02,
  TRUE, 'operational',
  '{"vessel_type": "VLCC", "primary_destinations": ["Asia", "Europe"]}'
),
(
  'b5000000-0000-0000-0000-000000000007',
  'Escravos Export to International Market',
  'ESCR-XPRT-L-001', 'sea_route',
  'a2000000-0000-0000-0000-000000000003',
  'a7000000-0000-0000-0000-000000000003',
  4800.0, NULL, NULL,
  7.0, 1.75, 300000, 0.65, 0.90, 0.02,
  FALSE, 'operational',
  '{"vessel_type": "Suezmax", "primary_destinations": ["Europe", "Americas"]}'
),

-- -------------------------------------------------------------------------
-- Additional Lateral / Redundancy Links
-- -------------------------------------------------------------------------
(
  'b6000000-0000-0000-0000-000000000001',
  'Onne Port to SS Distribution Hub',
  'ONNE-SSDH-L-001', 'road',
  'a5000000-0000-0000-0000-000000000003',
  'a6000000-0000-0000-0000-000000000006',
  38.0, NULL, NULL,
  0.4, 1.20, 40000, 0.70, 0.78, 0.18,
  FALSE, 'operational',
  '{"road_quality": "fair"}'
),
(
  'b6000000-0000-0000-0000-000000000002',
  'Calabar Port to SE Distribution Hub',
  'CALA-SEDH-L-001', 'road',
  'a5000000-0000-0000-0000-000000000004',
  'a6000000-0000-0000-0000-000000000002',
  230.0, NULL, NULL,
  1.2, 2.80, 25000, 0.55, 0.70, 0.15,
  FALSE, 'operational',
  '{"road_quality": "fair"}'
),
(
  'b6000000-0000-0000-0000-000000000003',
  'Mosimi to NC Hub Abuja — PPMC Extension Road',
  'MOSM-ABUJ-L-001', 'road',
  'a4000000-0000-0000-0000-000000000002',
  'a6000000-0000-0000-0000-000000000004',
  490.0, NULL, NULL,
  1.8, 3.20, 35000, 0.68, 0.72, 0.15,
  FALSE, 'operational',
  '{"road_quality": "mixed", "key_route": "Lagos-Ibadan-Abuja"}'
),
(
  'b6000000-0000-0000-0000-000000000004',
  'Ibadan to NC Hub Abuja Road',
  'IBAD-ABUJ-L-001', 'road',
  'a4000000-0000-0000-0000-000000000003',
  'a6000000-0000-0000-0000-000000000004',
  385.0, NULL, NULL,
  1.6, 3.00, 30000, 0.68, 0.74, 0.12,
  FALSE, 'operational',
  '{"road_quality": "good_sections"}'
),
(
  'b6000000-0000-0000-0000-000000000005',
  'Kano to Abuja Road (Strategic Link)',
  'KANO-ABUJ-L-001', 'road',
  'a4000000-0000-0000-0000-000000000006',
  'a6000000-0000-0000-0000-000000000004',
  375.0, NULL, NULL,
  1.4, 3.10, 35000, 0.75, 0.80, 0.10,
  FALSE, 'operational',
  '{"road_quality": "good", "dual_carriageway_partial": true}'
),
(
  'b6000000-0000-0000-0000-000000000006',
  'PHRC to SS Distribution Hub by Road',
  'PHRC-SSDH-L-001', 'road',
  'a3000000-0000-0000-0000-000000000001',
  'a6000000-0000-0000-0000-000000000006',
  165.0, NULL, NULL,
  0.8, 1.80, 30000, 0.28, 0.68, 0.30,
  FALSE, 'degraded',
  '{"note": "Low utilization due to PHRC underperformance"}'
),
(
  'b6000000-0000-0000-0000-000000000007',
  'Dangote to SW Distribution Hub Direct',
  'DANG-SWDH-L-001', 'road',
  'a3000000-0000-0000-0000-000000000004',
  'a6000000-0000-0000-0000-000000000001',
  30.0, NULL, NULL,
  0.4, 0.90, 100000, 0.45, 0.90, 0.05,
  TRUE, 'operational',
  '{"mode": "tanker_trucks", "daily_truck_trips": 280}'
),
(
  'b6000000-0000-0000-0000-000000000008',
  'Makurdi to Gombe Road',
  'MAKU-GOMB-L-001', 'road',
  'a4000000-0000-0000-0000-000000000007',
  'a4000000-0000-0000-0000-000000000008',
  430.0, NULL, NULL,
  2.0, 3.80, 15000, 0.50, 0.55, 0.20,
  FALSE, 'operational',
  '{"road_quality": "poor_to_fair"}'
);

-- =============================================================================
-- SECTION C: INVENTORY LEVELS (Selected key nodes — representative set)
-- =============================================================================

INSERT INTO inventory_levels (
  inventory_id, node_id, product_type,
  quantity_barrels, minimum_threshold_barrels, maximum_capacity_barrels,
  reorder_point_barrels, safety_stock_barrels,
  unit_cost_usd, daily_consumption_rate_bpd, daily_supply_rate_bpd
) VALUES

-- Bonny Export Terminal
('c1000000-0000-0000-0000-000000000001', 'a2000000-0000-0000-0000-000000000001', 'crude_oil', 3200000, 500000, 5000000, 1000000, 500000, 82.50, 480000, 520000),

-- Forcados Export Terminal
('c1000000-0000-0000-0000-000000000002', 'a2000000-0000-0000-0000-000000000002', 'crude_oil', 1400000, 250000, 2500000, 600000, 250000, 80.20, 220000, 230000),

-- Escravos Export Terminal
('c1000000-0000-0000-0000-000000000003', 'a2000000-0000-0000-0000-000000000003', 'crude_oil', 1300000, 200000, 2000000, 500000, 200000, 83.10, 190000, 210000),

-- Qua Iboe Terminal
('c1000000-0000-0000-0000-000000000004', 'a2000000-0000-0000-0000-000000000005', 'crude_oil', 2800000, 400000, 4000000, 900000, 400000, 84.70, 400000, 420000),

-- PHRC — Multiple Products
('c2000000-0000-0000-0000-000000000001', 'a3000000-0000-0000-0000-000000000001', 'crude_oil', 850000, 100000, 1500000, 400000, 150000, 82.00, 58800, 60000),
('c2000000-0000-0000-0000-000000000002', 'a3000000-0000-0000-0000-000000000001', 'petrol', 120000, 30000, 400000, 90000, 30000, 0.65, 35000, 32000),
('c2000000-0000-0000-0000-000000000003', 'a3000000-0000-0000-0000-000000000001', 'diesel', 95000, 25000, 320000, 75000, 25000, 0.72, 28000, 25000),
('c2000000-0000-0000-0000-000000000004', 'a3000000-0000-0000-0000-000000000001', 'kerosene', 45000, 10000, 150000, 35000, 10000, 0.58, 10000, 9000),

-- Warri Refinery
('c2000000-0000-0000-0000-000000000005', 'a3000000-0000-0000-0000-000000000002', 'crude_oil', 420000, 50000, 900000, 200000, 80000, 80.50, 22500, 23000),
('c2000000-0000-0000-0000-000000000006', 'a3000000-0000-0000-0000-000000000002', 'petrol', 60000, 15000, 250000, 55000, 15000, 0.65, 15000, 13000),
('c2000000-0000-0000-0000-000000000007', 'a3000000-0000-0000-0000-000000000002', 'diesel', 50000, 12000, 200000, 45000, 12000, 0.72, 12000, 11000),

-- Dangote Refinery
('c3000000-0000-0000-0000-000000000001', 'a3000000-0000-0000-0000-000000000004', 'crude_oil', 4500000, 1000000, 8000000, 2000000, 1000000, 82.50, 292500, 310000),
('c3000000-0000-0000-0000-000000000002', 'a3000000-0000-0000-0000-000000000004', 'petrol', 1800000, 200000, 3500000, 600000, 200000, 0.65, 150000, 165000),
('c3000000-0000-0000-0000-000000000003', 'a3000000-0000-0000-0000-000000000004', 'diesel', 950000, 100000, 2000000, 350000, 100000, 0.72, 85000, 92000),
('c3000000-0000-0000-0000-000000000004', 'a3000000-0000-0000-0000-000000000004', 'kerosene', 320000, 50000, 800000, 120000, 50000, 0.58, 28000, 30000),
('c3000000-0000-0000-0000-000000000005', 'a3000000-0000-0000-0000-000000000004', 'lpg', 180000, 30000, 500000, 80000, 30000, 0.45, 15000, 18000),
('c3000000-0000-0000-0000-000000000006', 'a3000000-0000-0000-0000-000000000004', 'jet_fuel', 250000, 40000, 600000, 100000, 40000, 0.95, 20000, 22000),

-- Atlas Cove
('c4000000-0000-0000-0000-000000000001', 'a4000000-0000-0000-0000-000000000001', 'petrol', 2800000, 400000, 4800000, 1000000, 400000, 0.65, 200000, 210000),
('c4000000-0000-0000-0000-000000000002', 'a4000000-0000-0000-0000-000000000001', 'diesel', 1200000, 150000, 2500000, 450000, 150000, 0.72, 90000, 95000),
('c4000000-0000-0000-0000-000000000003', 'a4000000-0000-0000-0000-000000000001', 'kerosene', 480000, 60000, 1000000, 180000, 60000, 0.58, 38000, 40000),

-- Mosimi Depot
('c4000000-0000-0000-0000-000000000004', 'a4000000-0000-0000-0000-000000000002', 'petrol', 650000, 80000, 1200000, 250000, 80000, 0.65, 55000, 58000),
('c4000000-0000-0000-0000-000000000005', 'a4000000-0000-0000-0000-000000000002', 'diesel', 320000, 40000, 650000, 120000, 40000, 0.72, 28000, 30000),
('c4000000-0000-0000-0000-000000000006', 'a4000000-0000-0000-0000-000000000002', 'kerosene', 95000, 15000, 220000, 40000, 15000, 0.58, 9000, 9500),

-- Kano Depot
('c4000000-0000-0000-0000-000000000007', 'a4000000-0000-0000-0000-000000000006', 'petrol', 420000, 60000, 850000, 180000, 60000, 0.65, 38000, 40000),
('c4000000-0000-0000-0000-000000000008', 'a4000000-0000-0000-0000-000000000006', 'diesel', 210000, 30000, 450000, 90000, 30000, 0.72, 20000, 21000),
('c4000000-0000-0000-0000-000000000009', 'a4000000-0000-0000-0000-000000000006', 'kerosene', 85000, 12000, 200000, 40000, 12000, 0.58, 8000, 8500),
('c4000000-0000-0000-0000-000000000010', 'a4000000-0000-0000-0000-000000000006', 'lpg', 35000, 5000, 90000, 18000, 5000, 0.45, 3500, 3800);

-- =============================================================================
-- SECTION D: DISRUPTION TYPES (25 types — all 8 categories covered)
-- =============================================================================

INSERT INTO disruption_types (
  disruption_type_id, category, name, description,
  typical_duration_days_min, typical_duration_days_mode, typical_duration_days_max,
  typical_annual_probability,
  severity_min, severity_mode, severity_max,
  cost_multiplier_min, cost_multiplier_max,
  recovery_time_days_min, recovery_time_days_max,
  affected_node_types, affected_link_types,
  correlated_disruption_ids, cascading_probability
) VALUES

-- INFRASTRUCTURE (4)
(
  'd1000000-0000-0000-0000-000000000001',
  'infrastructure', 'Pipeline Vandalism (Niger Delta)',
  'Deliberate sabotage of crude oil/products pipelines in the Niger Delta region. '
  'Most common disruption type; historically 100–200+ incidents per year.',
  1.0, 14.0, 90.0, 0.85,
  0.20, 0.65, 1.00, 1.5, 4.5,
  3.0, 45.0,
  '["pipeline", "export_terminal"]', '["pipeline"]',
  '["d3000000-0000-0000-0000-000000000001"]', 0.45
),
(
  'd1000000-0000-0000-0000-000000000002',
  'infrastructure', 'Refinery Equipment Failure',
  'Unplanned breakdown of critical refinery process units (CDU, FCC, HCU). '
  'Particularly prevalent in aging NNPC refineries with deferred maintenance.',
  7.0, 45.0, 180.0, 0.70,
  0.30, 0.70, 1.00, 1.3, 3.0,
  14.0, 120.0,
  '["refinery"]', '[]',
  '[]', 0.10
),
(
  'd1000000-0000-0000-0000-000000000003',
  'infrastructure', 'Export Terminal Fire / Explosion',
  'Fire or explosion at crude oil export terminals or storage tank farms. '
  'Can cause complete terminal shutdown and crude export halt for weeks.',
  14.0, 60.0, 180.0, 0.15,
  0.50, 0.85, 1.00, 2.0, 6.0,
  21.0, 90.0,
  '["export_terminal", "storage_depot"]', '[]',
  '["d4000000-0000-0000-0000-000000000001"]', 0.35
),
(
  'd1000000-0000-0000-0000-000000000004',
  'infrastructure', 'Subsea Pipeline / Umbilical Failure',
  'Failure of subsea flowlines or umbilicals at deep water fields. '
  'High repair cost and long intervention time due to ROV requirements.',
  30.0, 90.0, 365.0, 0.12,
  0.40, 0.80, 1.00, 2.5, 7.0,
  45.0, 180.0,
  '["wellhead"]', '["pipeline"]',
  '[]', 0.05
),

-- LOGISTICS (4)
(
  'd2000000-0000-0000-0000-000000000001',
  'logistics', 'Apapa Port Severe Congestion',
  'Extreme gridlock at Apapa Port Lagos disrupting tanker discharge and '
  'products loading. Average wait time 2–6 weeks; up to 10 weeks in severe cases.',
  7.0, 21.0, 70.0, 0.80,
  0.15, 0.40, 0.75, 1.2, 2.5,
  7.0, 42.0,
  '["port", "storage_depot"]', '["sea_route", "road"]',
  '[]', 0.20
),
(
  'd2000000-0000-0000-0000-000000000002',
  'logistics', 'Petroleum Tanker Truck Scarcity',
  'Shortage of road tanker trucks for downstream distribution. '
  'Caused by DPPRA compliance crackdowns, accidents, or fleet aging.',
  3.0, 14.0, 45.0, 0.55,
  0.10, 0.30, 0.60, 1.1, 2.0,
  5.0, 30.0,
  '["distribution_hub", "storage_depot"]', '["road"]',
  '[]', 0.15
),
(
  'd2000000-0000-0000-0000-000000000003',
  'logistics', 'Road Blockage (Flooding / Road Collapse)',
  'Key distribution roads blocked by flooding or structural failure. '
  'Particularly affects Onitsha-Enugu, Benin-Ore, and North-South corridors.',
  2.0, 7.0, 30.0, 0.45,
  0.10, 0.35, 0.70, 1.1, 1.8,
  3.0, 21.0,
  '["distribution_hub"]', '["road"]',
  '["d4000000-0000-0000-0000-000000000002"]', 0.30
),
(
  'd2000000-0000-0000-0000-000000000004',
  'logistics', 'Vessel / Tanker Unavailability',
  'Shortage of crude oil or products tankers for export liftings or import. '
  'Driven by global freight market tightness or local vessel certification failures.',
  7.0, 21.0, 60.0, 0.30,
  0.15, 0.35, 0.65, 1.2, 2.2,
  7.0, 35.0,
  '["export_terminal", "port"]', '["sea_route"]',
  '[]', 0.10
),

-- GEOPOLITICAL (3)
(
  'd3000000-0000-0000-0000-000000000001',
  'geopolitical', 'Niger Delta Militant Attacks',
  'Armed attacks on oil infrastructure by militant groups (MEND, NDA, etc.). '
  'Can cause simultaneous multi-node disruptions across the Niger Delta.',
  7.0, 30.0, 120.0, 0.40,
  0.30, 0.70, 1.00, 1.5, 5.0,
  14.0, 90.0,
  '["wellhead", "pipeline", "export_terminal"]', '["pipeline"]',
  '["d1000000-0000-0000-0000-000000000001", "d4000000-0000-0000-0000-000000000001"]', 0.55
),
(
  'd3000000-0000-0000-0000-000000000002',
  'geopolitical', 'Community Protest / Host Community Blockade',
  'Local community protests blocking pipeline right-of-way or facility access. '
  'Common in oil-producing communities disputing royalties or environmental damage.',
  3.0, 14.0, 60.0, 0.60,
  0.10, 0.40, 0.80, 1.1, 2.5,
  5.0, 30.0,
  '["wellhead", "pipeline", "export_terminal"]', '["pipeline", "road"]',
  '[]', 0.20
),
(
  'd3000000-0000-0000-0000-000000000003',
  'geopolitical', 'Government Policy / Regulatory Shock',
  'Sudden policy changes: fuel subsidy removal, export ban, NNPC directive. '
  'Can reshape supply chain economics overnight. Reference: May 2023 subsidy removal.',
  7.0, 30.0, 180.0, 0.20,
  0.05, 0.25, 0.60, 1.0, 3.0,
  14.0, 90.0,
  '["refinery", "distribution_hub", "consumer"]', '[]',
  '["d6000000-0000-0000-0000-000000000001"]', 0.40
),

-- ENVIRONMENTAL (3)
(
  'd4000000-0000-0000-0000-000000000001',
  'environmental', 'Oil Spill (Pipeline Rupture)',
  'Significant crude oil spill requiring regulatory shutdown and remediation. '
  'NOSDRA mandated cleanup; DNI operations suspended until certified clear.',
  14.0, 45.0, 180.0, 0.50,
  0.20, 0.60, 0.90, 1.3, 3.5,
  21.0, 120.0,
  '["pipeline", "export_terminal"]', '["pipeline"]',
  '[]', 0.15
),
(
  'd4000000-0000-0000-0000-000000000002',
  'environmental', 'Seasonal Flooding (Niger Delta)',
  'Annual flood season (July–November) disrupting road access, onshore pipelines. '
  'Predictable seasonality but variable severity year-to-year.',
  30.0, 60.0, 120.0, 0.70,
  0.10, 0.30, 0.70, 1.1, 2.0,
  14.0, 60.0,
  '["storage_depot", "distribution_hub"]', '["road", "pipeline"]',
  '[]', 0.25
),
(
  'd4000000-0000-0000-0000-000000000003',
  'environmental', 'Adverse Weather (Atlantic Storms / Harmattan)',
  'Gulf of Guinea storms disrupting offshore operations; harmattan affecting '
  'visibility for tanker navigation November–March.',
  1.0, 5.0, 21.0, 0.45,
  0.05, 0.20, 0.60, 1.0, 1.5,
  1.0, 14.0,
  '["wellhead", "export_terminal", "port"]', '["sea_route"]',
  '[]', 0.10
),

-- OPERATIONAL (4)
(
  'd5000000-0000-0000-0000-000000000001',
  'operational', 'Inventory Stockout (Fuel Scarcity)',
  'Complete depletion of petroleum products at key depots. '
  'Nigeria''s recurring fuel scarcity; 2022 episode lasted 6+ weeks.',
  7.0, 21.0, 90.0, 0.65,
  0.20, 0.50, 0.90, 1.2, 3.0,
  7.0, 45.0,
  '["storage_depot", "distribution_hub", "consumer"]', '[]',
  '["d6000000-0000-0000-0000-000000000001"]', 0.30
),
(
  'd5000000-0000-0000-0000-000000000002',
  'operational', 'Power Outage (Grid Failure) at Facility',
  'NEPA/PHCN grid failure affecting pumping stations, depot operations. '
  'Nigeria''s chronic power deficit; average >250 outage hours/month.',
  0.5, 3.0, 14.0, 0.90,
  0.05, 0.20, 0.50, 1.0, 1.5,
  0.5, 7.0,
  '["refinery", "storage_depot", "port"]', '["pipeline"]',
  '[]', 0.10
),
(
  'd5000000-0000-0000-0000-000000000003',
  'operational', 'Key Supplier / Trader Default',
  'Primary crude oil purchaser or products importer defaults on contract. '
  'Leaves terminal inventory stranded or creates sudden demand gap.',
  7.0, 30.0, 90.0, 0.25,
  0.10, 0.30, 0.60, 1.0, 2.0,
  14.0, 60.0,
  '["export_terminal", "storage_depot"]', '[]',
  '[]', 0.15
),
(
  'd5000000-0000-0000-0000-000000000004',
  'operational', 'Labour Strike at Refinery or Terminal',
  'Industrial action by NUPENG (petroleum workers union) or PENGASSAN. '
  'Has historically shut down all NNPC refineries simultaneously.',
  3.0, 14.0, 45.0, 0.30,
  0.20, 0.60, 1.00, 1.1, 2.5,
  5.0, 30.0,
  '["refinery", "export_terminal", "port"]', '[]',
  '[]', 0.20
),

-- ECONOMIC (3)
(
  'd6000000-0000-0000-0000-000000000001',
  'economic', 'Naira Devaluation / FX Crisis',
  'Severe Nigerian Naira devaluation increasing import costs for petroleum products. '
  'Affects importers ability to fund cargoes; recent 2023 devaluation was 60%+.',
  30.0, 120.0, 365.0, 0.35,
  0.05, 0.20, 0.50, 1.2, 2.8,
  30.0, 180.0,
  '["storage_depot", "distribution_hub", "consumer"]', '[]',
  '["d5000000-0000-0000-0000-000000000001"]', 0.45
),
(
  'd6000000-0000-0000-0000-000000000002',
  'economic', 'Global Crude Price Shock (>20% Move)',
  'Significant global crude oil price movement affecting production economics '
  'and NNPC allocation decisions. Reference: 2020 COVID crash, 2022 Ukraine spike.',
  30.0, 90.0, 365.0, 0.25,
  0.05, 0.15, 0.40, 1.0, 2.0,
  30.0, 120.0,
  '["wellhead", "export_terminal"]', '[]',
  '[]', 0.15
),
(
  'd6000000-0000-0000-0000-000000000003',
  'economic', 'Fuel Subsidy Policy Change',
  'Government decision to introduce, remove, or modify petroleum product subsidies. '
  'Creates immediate demand surge or collapse and disrupts pricing signals.',
  1.0, 30.0, 180.0, 0.20,
  0.05, 0.25, 0.55, 1.0, 2.5,
  7.0, 90.0,
  '["distribution_hub", "consumer"]', '[]',
  '["d5000000-0000-0000-0000-000000000001"]', 0.40
),

-- CYBERSECURITY (2)
(
  'd7000000-0000-0000-0000-000000000001',
  'cybersecurity', 'SCADA System Cyberattack',
  'Ransomware or state-sponsored cyberattack on pipeline or terminal SCADA systems. '
  'Requires emergency manual operation; reference: Colonial Pipeline 2021.',
  3.0, 14.0, 45.0, 0.08,
  0.30, 0.65, 1.00, 1.5, 4.0,
  7.0, 30.0,
  '["pipeline", "refinery", "export_terminal"]', '["pipeline"]',
  '[]', 0.20
),
(
  'd7000000-0000-0000-0000-000000000002',
  'cybersecurity', 'Data Breach / ERP System Failure',
  'Compromise of operational technology or ERP systems affecting inventory '
  'management, dispatch scheduling, and financial settlements.',
  1.0, 7.0, 30.0, 0.12,
  0.05, 0.20, 0.50, 1.0, 1.8,
  2.0, 14.0,
  '["storage_depot", "distribution_hub", "port"]', '[]',
  '[]', 0.10
),

-- FORCE MAJEURE (2)
(
  'd8000000-0000-0000-0000-000000000001',
  'force_majeure', 'Epidemic / Pandemic Disruption',
  'Public health emergency forcing workforce reductions and supply chain shutdowns. '
  'Reference: COVID-19 caused ~30% Nigeria oil production drop in Q2 2020.',
  30.0, 90.0, 365.0, 0.05,
  0.10, 0.35, 0.80, 1.2, 2.5,
  30.0, 180.0,
  '["wellhead", "refinery", "export_terminal", "port"]', '["pipeline", "sea_route"]',
  '[]', 0.25
),
(
  'd8000000-0000-0000-0000-000000000002',
  'force_majeure', 'Earthquake / Natural Disaster',
  'Seismic or other natural disaster affecting oil infrastructure. '
  'Nigeria has limited earthquake risk but Gulf of Guinea tsunami risk is non-zero.',
  1.0, 14.0, 90.0, 0.02,
  0.20, 0.60, 1.00, 1.5, 5.0,
  7.0, 120.0,
  '["wellhead", "pipeline", "refinery", "port"]', '["pipeline"]',
  '[]', 0.30
);

-- =============================================================================
-- SECTION E: MITIGATION STRATEGIES (12 strategies)
-- =============================================================================

INSERT INTO mitigation_strategies (
  strategy_id, strategy_name, description,
  target_disruption_type_id, applicable_node_types, applicable_link_types,
  implementation_cost_usd, annual_maintenance_cost_usd,
  effectiveness_score, reduces_probability_by, reduces_severity_by,
  reduces_recovery_time_by_pct, feasibility_score,
  implementation_time_days, metadata
) VALUES

(
  'e1000000-0000-0000-0000-000000000001',
  'Pipeline Aerial Surveillance Program',
  'Deployment of drones and helicopters for daily monitoring of Niger Delta '
  'pipeline corridors. Early detection of unauthorized access or tampering '
  'reduces vandalism success rate and enables rapid response.',
  'd1000000-0000-0000-0000-000000000001',
  '["pipeline", "export_terminal"]', '["pipeline"]',
  85000000, 12000000,
  0.55, 0.40, 0.30, 0.35, 0.70,
  180,
  '{"coverage_km": 1200, "drone_fleet": 24, "pilot_program": "SPDC_aerial_2019", "roi_years": 3}'
),
(
  'e1000000-0000-0000-0000-000000000002',
  'Strategic Petroleum Reserve (60-day)',
  'Build national strategic reserve of 60-day petroleum products supply. '
  'Absorbs supply disruptions without affecting consumer markets. '
  'Reference: IEA member states maintain 90-day reserves.',
  'd5000000-0000-0000-0000-000000000001',
  '["storage_depot"]', '[]',
  2500000000, 45000000,
  0.80, 0.00, 0.70, 0.50, 0.55,
  730,
  '{"storage_volume_m3": 8000000, "location": "multiple_strategic_sites", "product_mix": ["PMS", "AGO", "DPK"]}'
),
(
  'e1000000-0000-0000-0000-000000000003',
  'Community Engagement Trust Fund',
  'Establish host community development trust funds to reduce militant '
  'activity and protest blockades. Proven model used by some IOCs. '
  'Addresses root cause of geopolitical disruptions.',
  'd3000000-0000-0000-0000-000000000001',
  '["wellhead", "pipeline", "export_terminal"]', '["pipeline"]',
  200000000, 50000000,
  0.65, 0.55, 0.40, 0.20, 0.75,
  90,
  '{"communities_covered": 45, "annual_disbursement_usd": 50000000}'
),
(
  'e1000000-0000-0000-0000-000000000004',
  'Apapa Port Digital Queue Management System',
  'Real-time vessel scheduling, truck queuing, and jetty management system '
  'for Apapa Port. Reduce average wait time from 14 days to 4–6 days.',
  'd2000000-0000-0000-0000-000000000001',
  '["port"]', '["sea_route", "road"]',
  45000000, 5000000,
  0.60, 0.10, 0.55, 0.60, 0.85,
  365,
  '{"expected_wait_reduction_days": 8, "truck_queue_reduction_pct": 0.55}'
),
(
  'e1000000-0000-0000-0000-000000000005',
  'Pipeline Leak Detection System (Fiber Optic)',
  'Distributed acoustic sensing (DAS) along key pipelines to detect leaks '
  'and third-party interference within minutes. Enables rapid response.',
  'd4000000-0000-0000-0000-000000000001',
  '[]', '["pipeline"]',
  350000000, 22000000,
  0.70, 0.25, 0.50, 0.55, 0.72,
  540,
  '{"pipeline_coverage_km": 3500, "detection_time_minutes": 15, "technology": "Silixa_ULTIMA"}'
),
(
  'e1000000-0000-0000-0000-000000000006',
  'Refinery Rehabilitation (PHRC & WRPC)',
  'Full turnaround maintenance and rehabilitation of Port Harcourt and Warri '
  'refineries to restore nameplate capacity. Reduces import dependence.',
  'd1000000-0000-0000-0000-000000000002',
  '["refinery"]', '[]',
  1800000000, 80000000,
  0.75, 0.50, 0.65, 0.45, 0.50,
  1095,
  '{"target_utilization_pct": 0.75, "contractor": "TBD", "rehabilitation_scope": "full_turnaround"}'
),
(
  'e1000000-0000-0000-0000-000000000007',
  'SCADA Cybersecurity Hardening',
  'Network segmentation, intrusion detection, and air-gapping of critical '
  'OT/ICS networks. Patch management and 24/7 SOC for operational technology.',
  'd7000000-0000-0000-0000-000000000001',
  '["pipeline", "refinery", "export_terminal"]', '["pipeline"]',
  120000000, 18000000,
  0.72, 0.60, 0.55, 0.40, 0.80,
  270,
  '{"SOC_coverage": "24x7", "technology": "Claroty_OT_security", "sites_covered": 18}'
),
(
  'e1000000-0000-0000-0000-000000000008',
  'Multi-Modal Transport Diversification',
  'Develop rail and river transport alternatives to reduce road tanker dependence. '
  'Rehabilitate NRC rail lines for petroleum product movement.',
  'd2000000-0000-0000-0000-000000000002',
  '["distribution_hub", "storage_depot"]', '["road"]',
  950000000, 65000000,
  0.55, 0.30, 0.45, 0.35, 0.45,
  1460,
  '{"rail_km_rehabilitated": 800, "river_barges_deployed": 35, "products": ["PMS", "AGO"]}'
),
(
  'e1000000-0000-0000-0000-000000000009',
  'Emergency Generator Backup at Depot',
  'Install dedicated natural gas or diesel generators at all major depots '
  'and pumping stations to eliminate power outage vulnerability.',
  'd5000000-0000-0000-0000-000000000002',
  '["storage_depot", "refinery", "port"]', '["pipeline"]',
  180000000, 15000000,
  0.85, 0.80, 0.90, 0.95, 0.90,
  180,
  '{"capacity_mw": 850, "fuel_type": "natural_gas_primary", "sites": 22}'
),
(
  'e1000000-0000-0000-0000-000000000010',
  'Offshore Pipeline Route Diversification',
  'Lay new subsea export pipeline bypassing the most vandalism-prone '
  'onshore sections of TNP and NCTL. Higher capex but eliminates vulnerability.',
  'd1000000-0000-0000-0000-000000000001',
  '[]', '["pipeline"]',
  3200000000, 45000000,
  0.85, 0.70, 0.80, 0.50, 0.35,
  1825,
  '{"route_km": 380, "bypass_nodes": ["Bonny", "Forcados"], "technology": "subsea_HDD"}'
),
(
  'e1000000-0000-0000-0000-000000000011',
  'Hedging Program (FX and Crude Price)',
  'Implement structured FX hedging using FMDQ OTC derivatives and crude '
  'price hedging via Brent futures/options to stabilize import costs.',
  'd6000000-0000-0000-0000-000000000001',
  '[]', '[]',
  5000000, 2000000,
  0.50, 0.00, 0.60, 0.00, 0.88,
  90,
  '{"hedge_ratio_pct": 0.60, "instruments": ["FX_forwards", "Brent_puts"], "horizon_months": 12}'
),
(
  'e1000000-0000-0000-0000-000000000012',
  'Pandemic Business Continuity Plan',
  'Formalized BCP including minimum safe crew protocols, remote monitoring, '
  'and pre-positioned maintenance teams for pandemic scenarios.',
  'd8000000-0000-0000-0000-000000000001',
  '["wellhead", "refinery", "export_terminal", "port"]', '[]',
  25000000, 3500000,
  0.65, 0.20, 0.50, 0.40, 0.92,
  120,
  '{"remote_monitoring_sites": 28, "skeleton_crew_pct": 0.30}'
);

-- =============================================================================
-- SECTION F: SCENARIOS (3 pre-built demo scenarios)
-- Requires a user in auth.users — using a fixed demo UUID
-- In production, replace with actual Supabase auth user ID
-- =============================================================================

-- Note: Supabase requires auth.users to exist before referencing.
-- For testing, insert a demo user profile after auth.users is seeded.
-- The following assumes demo_user_id = 'f0000000-0000-0000-0000-000000000001'

INSERT INTO scenarios (
  scenario_id, scenario_name, description,
  created_by, is_public,
  simulation_iterations, time_horizon_days,
  random_seed, status, tags
) VALUES

(
  'f1000000-0000-0000-0000-000000000001',
  'Niger Delta Cascade — Full Chain Stress Test',
  'Simultaneous pipeline vandalism, militant attack, and oil spill in the Niger Delta. '
  'Models compound disruption at Bonny and Forcados nodes propagating through '
  'the full supply chain. Designed to compute maximum credible loss scenario.',
  'f0000000-0000-0000-0000-000000000001',
  TRUE, 10000, 180, 42,
  'completed',
  ARRAY['niger-delta', 'vandalism', 'compound', 'worst-case', '2024']
),
(
  'f1000000-0000-0000-0000-000000000002',
  'Apapa Port Gridlock — Downstream Fuel Scarcity',
  'Extended Apapa Port congestion (30-day shutdown scenario) combined with '
  'tanker truck scarcity. Models nationwide fuel queue propagation and '
  'cost of emergency imports through Tin Can and Onne ports.',
  'f0000000-0000-0000-0000-000000000001',
  TRUE, 10000, 90, 123,
  'completed',
  ARRAY['apapa', 'logistics', 'fuel-scarcity', 'downstream', 'lagos']
),
(
  'f1000000-0000-0000-0000-000000000003',
  'Dangote Refinery Ramp-Up Impact Analysis',
  'Evaluates how Dangote Refinery ramping from 45% to 90% capacity changes '
  'supply chain resilience. Models reduction in import dependence and impact '
  'on Apapa congestion and FX demand.',
  'f0000000-0000-0000-0000-000000000001',
  TRUE, 10000, 365, 999,
  'draft',
  ARRAY['dangote', 'refinery', 'capacity', 'resilience', 'baseline']
);

-- Scenario disruptions for Scenario 1 (Niger Delta Cascade)
INSERT INTO scenario_disruptions (
  scenario_disruption_id, scenario_id, disruption_type_id,
  target_node_id, target_link_id,
  probability_override, severity_override, duration_days_override,
  is_active
) VALUES
(
  'f2000000-0000-0000-0000-000000000001',
  'f1000000-0000-0000-0000-000000000001',
  'd1000000-0000-0000-0000-000000000001',
  NULL, 'b1000000-0000-0000-0000-000000000001',
  0.95, 0.80, NULL, TRUE
),
(
  'f2000000-0000-0000-0000-000000000002',
  'f1000000-0000-0000-0000-000000000001',
  'd1000000-0000-0000-0000-000000000001',
  NULL, 'b1000000-0000-0000-0000-000000000002',
  0.90, 0.90, NULL, TRUE
),
(
  'f2000000-0000-0000-0000-000000000003',
  'f1000000-0000-0000-0000-000000000001',
  'd3000000-0000-0000-0000-000000000001',
  'a1000000-0000-0000-0000-000000000001', NULL,
  0.75, 0.70, 30.0, TRUE
),
(
  'f2000000-0000-0000-0000-000000000004',
  'f1000000-0000-0000-0000-000000000001',
  'd4000000-0000-0000-0000-000000000001',
  NULL, 'b1000000-0000-0000-0000-000000000003',
  0.70, 0.65, NULL, TRUE
);

-- Scenario disruptions for Scenario 2 (Apapa Gridlock)
INSERT INTO scenario_disruptions (
  scenario_disruption_id, scenario_id, disruption_type_id,
  target_node_id, target_link_id,
  probability_override, severity_override, duration_days_override,
  is_active
) VALUES
(
  'f2000000-0000-0000-0000-000000000005',
  'f1000000-0000-0000-0000-000000000002',
  'd2000000-0000-0000-0000-000000000001',
  'a5000000-0000-0000-0000-000000000001', NULL,
  0.90, 0.70, 30.0, TRUE
),
(
  'f2000000-0000-0000-0000-000000000006',
  'f1000000-0000-0000-0000-000000000002',
  'd2000000-0000-0000-0000-000000000002',
  NULL, NULL,
  0.80, 0.50, NULL, TRUE
),
(
  'f2000000-0000-0000-0000-000000000007',
  'f1000000-0000-0000-0000-000000000002',
  'd5000000-0000-0000-0000-000000000001',
  'a4000000-0000-0000-0000-000000000001', NULL,
  0.75, 0.60, NULL, TRUE
);

-- =============================================================================
-- SECTION G: FLOW RECORDS — 90-Day Historical Baseline
-- Inserting representative records for the 10 most critical links
-- (Statistically representative; full dataset would be generated by simulation engine)
-- =============================================================================

-- Helper: generate 90 days of flow records for key pipeline links
-- We insert monthly summaries (30 records × 3 months) for 5 key links
-- representing the crude export pipeline corridors

DO $$
DECLARE
  d DATE;
  link_rec RECORD;
  base_volume DECIMAL;
  base_cost DECIMAL;
  delay DECIMAL;
  actual_lead DECIMAL;
  fstatus flow_status_enum;
BEGIN

  FOR link_rec IN SELECT * FROM (VALUES
    ('b1000000-0000-0000-0000-000000000001'::UUID, 320000::DECIMAL, 0.85::DECIMAL, 'crude_oil'::product_type_enum),
    ('b1000000-0000-0000-0000-000000000002'::UUID, 290000::DECIMAL, 0.75::DECIMAL, 'crude_oil'::product_type_enum),
    ('b1000000-0000-0000-0000-000000000003'::UUID, 175000::DECIMAL, 0.90::DECIMAL, 'crude_oil'::product_type_enum),
    ('b1000000-0000-0000-0000-000000000006'::UUID, 400000::DECIMAL, 0.60::DECIMAL, 'crude_oil'::product_type_enum),
    ('b2000000-0000-0000-0000-000000000004'::UUID, 280000::DECIMAL, 1.20::DECIMAL, 'crude_oil'::product_type_enum),
    ('b3000000-0000-0000-0000-000000000002'::UUID, 260000::DECIMAL, 0.28::DECIMAL, 'petrol'::product_type_enum),
    ('b4000000-0000-0000-0000-000000000001'::UUID, 80000::DECIMAL, 0.45::DECIMAL, 'petrol'::product_type_enum),
    ('b4000000-0000-0000-0000-000000000005'::UUID, 30000::DECIMAL, 2.80::DECIMAL, 'petrol'::product_type_enum)
  ) AS t(link_id, vol, cost_pb, prod_type)
  LOOP

    d := CURRENT_DATE - INTERVAL '90 days';
    WHILE d <= CURRENT_DATE - INTERVAL '1 day' LOOP

      -- Simulate realistic variance
      base_volume := link_rec.vol * (0.75 + random() * 0.40);
      base_cost   := link_rec.cost_pb * base_volume * (0.90 + random() * 0.20);

      -- ~20% chance of delay, ~5% chance of blockage on high-risk links
      IF random() < 0.05 THEN
        fstatus := 'blocked';
        delay := 3.0 + random() * 10.0;
        actual_lead := (SELECT normal_lead_time_days FROM supply_chain_links WHERE link_id = link_rec.link_id) + delay;
        base_cost := base_cost * (1.5 + random() * 2.0);
        base_volume := base_volume * (0.1 + random() * 0.3);
      ELSIF random() < 0.20 THEN
        fstatus := 'delayed';
        delay := 0.5 + random() * 5.0;
        actual_lead := (SELECT normal_lead_time_days FROM supply_chain_links WHERE link_id = link_rec.link_id) + delay;
        base_cost := base_cost * (1.1 + random() * 0.5);
      ELSE
        fstatus := 'completed';
        actual_lead := (SELECT normal_lead_time_days FROM supply_chain_links WHERE link_id = link_rec.link_id) * (0.95 + random() * 0.10);
      END IF;

      INSERT INTO flow_records (
        flow_id, link_id, product_type, volume_barrels, flow_date,
        scheduled_lead_time_days, actual_lead_time_days,
        scheduled_cost_usd, actual_cost_usd, flow_status
      ) VALUES (
        gen_random_uuid(),
        link_rec.link_id,
        link_rec.prod_type,
        ROUND(base_volume::NUMERIC, 2),
        d,
        (SELECT normal_lead_time_days FROM supply_chain_links WHERE link_id = link_rec.link_id),
        ROUND(actual_lead::NUMERIC, 4),
        ROUND((link_rec.cost_pb * link_rec.vol)::NUMERIC, 2),
        ROUND(base_cost::NUMERIC, 2),
        fstatus
      );

      d := d + INTERVAL '1 day';
    END LOOP;
  END LOOP;
END $$;

COMMIT;

-- =============================================================================
-- VERIFICATION QUERIES — Run these after seeding to confirm integrity
-- =============================================================================

SELECT 'supply_chain_nodes'    AS table_name, COUNT(*) AS row_count FROM supply_chain_nodes
UNION ALL
SELECT 'supply_chain_links',    COUNT(*) FROM supply_chain_links
UNION ALL
SELECT 'inventory_levels',      COUNT(*) FROM inventory_levels
UNION ALL
SELECT 'disruption_types',      COUNT(*) FROM disruption_types
UNION ALL
SELECT 'mitigation_strategies', COUNT(*) FROM mitigation_strategies
UNION ALL
SELECT 'scenarios',             COUNT(*) FROM scenarios
UNION ALL
SELECT 'scenario_disruptions',  COUNT(*) FROM scenario_disruptions
UNION ALL
SELECT 'flow_records',          COUNT(*) FROM flow_records;

-- FK integrity check
SELECT
  n.node_name,
  n.stage,
  n.node_type,
  n.geopolitical_zone,
  n.status,
  n.capacity_bpd
FROM supply_chain_nodes n
ORDER BY n.stage, n.node_type, n.node_name;

-- Critical path links
SELECT link_name, link_type, distance_km, reliability_score, vandalism_risk_score
FROM supply_chain_links
WHERE is_critical_path = TRUE
ORDER BY reliability_score ASC;

-- 07 The final feature table: one row per applicant ("report card")
-- = cleaned application + derived ratios + every history summary
-- Grain: one row per SK_ID_CURR (train + test)

CREATE SCHEMA IF NOT EXISTS features;

CREATE OR REPLACE TABLE features.application_features AS
SELECT
    -- keys and target
    a.SK_ID_CURR,
    a.TARGET,
    a.is_train,

    -- application: kept as-is
    a.NAME_CONTRACT_TYPE, a.CODE_GENDER, a.FLAG_OWN_CAR, a.FLAG_OWN_REALTY,
    a.CNT_CHILDREN, a.CNT_FAM_MEMBERS,
    a.AMT_INCOME_TOTAL, a.AMT_CREDIT, a.AMT_ANNUITY, a.AMT_GOODS_PRICE,
    a.NAME_INCOME_TYPE, a.NAME_EDUCATION_TYPE, a.NAME_FAMILY_STATUS, a.NAME_HOUSING_TYPE,
    a.OCCUPATION_TYPE, a.ORGANIZATION_TYPE,
    a.REGION_POPULATION_RELATIVE, a.REGION_RATING_CLIENT_W_CITY, a.OWN_CAR_AGE,
    a.EXT_SOURCE_1, a.EXT_SOURCE_2, a.EXT_SOURCE_3,
    a.FLAG_EMPLOYED_PLACEHOLDER,
    a.AMT_REQ_CREDIT_BUREAU_YEAR, a.DEF_30_CNT_SOCIAL_CIRCLE, a.DEF_60_CNT_SOCIAL_CIRCLE,

    -- application: derived
    -a.DAYS_BIRTH / 365.25                                       AS age_years,
    -a.DAYS_EMPLOYED / 365.25                                    AS years_employed,
    a.DAYS_EMPLOYED / NULLIF(a.DAYS_BIRTH, 0)                    AS employed_to_age_ratio,
    -a.DAYS_ID_PUBLISH / 365.25                                  AS years_since_id_change,
    -a.DAYS_REGISTRATION / 365.25                                AS years_since_registration,
    -a.DAYS_LAST_PHONE_CHANGE                                    AS days_since_phone_change,
    a.AMT_CREDIT  / NULLIF(a.AMT_INCOME_TOTAL, 0)                AS credit_to_income,
    a.AMT_ANNUITY / NULLIF(a.AMT_INCOME_TOTAL, 0)                AS annuity_to_income,
    a.AMT_CREDIT  / NULLIF(a.AMT_ANNUITY, 0)                     AS credit_to_annuity,
    a.AMT_GOODS_PRICE / NULLIF(a.AMT_CREDIT, 0)                  AS goods_to_credit,
    a.AMT_INCOME_TOTAL / NULLIF(a.CNT_FAM_MEMBERS, 0)            AS income_per_person,
    (COALESCE(a.EXT_SOURCE_1, 0) + COALESCE(a.EXT_SOURCE_2, 0) + COALESCE(a.EXT_SOURCE_3, 0))
      / NULLIF((a.EXT_SOURCE_1 IS NOT NULL)::INT + (a.EXT_SOURCE_2 IS NOT NULL)::INT
             + (a.EXT_SOURCE_3 IS NOT NULL)::INT, 0)             AS ext_source_mean,
    LEAST(a.EXT_SOURCE_1, a.EXT_SOURCE_2, a.EXT_SOURCE_3)        AS ext_source_min,
    GREATEST(a.EXT_SOURCE_1, a.EXT_SOURCE_2, a.EXT_SOURCE_3)     AS ext_source_max,
    (a.EXT_SOURCE_1 IS NULL)::INT + (a.EXT_SOURCE_2 IS NULL)::INT
      + (a.EXT_SOURCE_3 IS NULL)::INT                            AS ext_source_missing_count,
    a.FLAG_DOCUMENT_2 + a.FLAG_DOCUMENT_3 + a.FLAG_DOCUMENT_4 + a.FLAG_DOCUMENT_5
      + a.FLAG_DOCUMENT_6 + a.FLAG_DOCUMENT_7 + a.FLAG_DOCUMENT_8 + a.FLAG_DOCUMENT_9
      + a.FLAG_DOCUMENT_10 + a.FLAG_DOCUMENT_11 + a.FLAG_DOCUMENT_12 + a.FLAG_DOCUMENT_13
      + a.FLAG_DOCUMENT_14 + a.FLAG_DOCUMENT_15 + a.FLAG_DOCUMENT_16 + a.FLAG_DOCUMENT_17
      + a.FLAG_DOCUMENT_18 + a.FLAG_DOCUMENT_19 + a.FLAG_DOCUMENT_20 + a.FLAG_DOCUMENT_21
                                                                 AS documents_provided,

    -- "does this person have any history?" flags
    (b.SK_ID_CURR   IS NOT NULL)::INT
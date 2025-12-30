select
  customer_id,
  gender,
  senior_citizen,
  Partner,
  Dependents,
  tenure,
  PhoneService,
  MultipleLines,
  InternetService,
  OnlineSecurity,
  OnlineBackup,
  DeviceProtection,
  TechSupport,
  StreamingTV,
  StreamingMovies,
  Contract,
  PaperlessBilling,
  PaymentMethod,
  monthly_charges,

  case
    when trim(cast(TotalCharges as string)) = '' then null
    else cast(TotalCharges as float64)
  end as total_charges,

  case
    when safe_cast(Churn as bool) is true then 1
    when lower(cast(Churn as string)) = 'yes' then 1
    else 0
  end as churn_flag

from {{ ref('stg_customer_churn') }}

from google.cloud import bigquery

PROJECT_ID = "gcp-churn-platform"
client = bigquery.Client(project=PROJECT_ID)

sql = """
SELECT churn_flag, COUNT(*) AS cnt
FROM `gcp-churn-platform.churn_analytics.customer_churn_clean_dbt`
GROUP BY churn_flag
ORDER BY churn_flag
"""

df = client.query(sql).to_dataframe()
print(df)


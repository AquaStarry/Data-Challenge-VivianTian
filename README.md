# Fetch Data Analysis Repository  

This repository contains the code, SQL queries, and documentation for analyzing Fetch's transaction data. The analysis focuses on identifying data quality issues, uncovering key trends, and providing actionable insights for stakeholders.  

---

## **Repository Structure**  

### 1. **`util.py`**  
This file contains utility functions used for data quality checks and data cleansing. The primary function, `data_quality_check()`, is designed to:  
- Identify missing values, duplicates, and inconsistencies in the data.  
- Generate summary statistics and data quality reports.  
- Output results in a format that can be integrated into the HTML report.  


### 2. **`Data Challenge.ipynb`**  
This folder contains the Jupyter Notebook report generated from the data quality checks and data cleansing process. The report includes:  
- **Data Quality Overview**: Summary of missing values, duplicates, and inconsistencies.  
- **Detailed Findings**: Breakdown of issues in the `product`, `transaction`, and `user` tables.  
- **SQL Queries**: SQL Queries to answer key business questions (with additional supporting files attached for reference).  


### 3. **`sql_queries.pdf`**  
This document contains the SQL queries used to answer key business questions, including:  
- Identifying Fetch's power users.  
- Determining the leading brand in the "Dips & Salsa" category.  
- Calculating Fetch's year-over-year growth.  
- **Power Users**: Identifies users with high engagement based on transaction frequency and spending.  
- **Leading Brand**: Determines the top-performing brand in a specific category.  
- **YoY Growth**: Calculates year-over-year growth in total revenue.  


### 4. **`email.pdf`**  
This document is a written email to stakeholders, summarizing the results of the investigation. It includes:  
- **Key Data Quality Issues**: Missing values, duplicates, and inconsistencies in the data.  
- **Interesting Trend**: CVS's dominance among long-term Fetch users.  
- **Actionable Insights**: Recommendations for optimizing brand partnerships and user engagement.  
- **Request for Action**: Clarification on data collection processes and support for data cleaning.  

---
Thank you for reviewing our analysis. Looking forward to your feedback and guidance.

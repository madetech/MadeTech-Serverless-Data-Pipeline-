# Project Overview 
The goal of the project is to create a data pipeline on AWS, which is responsible for extracting data from APIs.

With the intention to centralize all data extracted from these sources within a database hosted on AWS. 

Below is a high level overview of the diagram for the project. 

<img width="954" height="289" alt="Screenshot 2026-09-03 at 17 07 31" src="https://github.com/user-attachments/assets/bf69d7a5-7877-4598-8fab-944054a9ef90" />


## Breakdown of Components 

### AWS Lambda 
Serverless compute service hosted on AWS. 

Primary Usage 

Running Python Packages which are responsible for API extraction, and performing transformations on extracted data.

#### API Extraction
Lambda function responsible for the extraction of data from various APIs. 

All APIs are open source, and are available to use via this Github Repository 

#### Data Transformations
Lambda function responsible for performing transformations on extracted data. 

Data is intended to be processed via two potential approaches: 

- Medallion Architecture
- Custom Framework

More information regarding the custom framework can be seen here. 

### AWS S3
Cloud based object storage service. 

Primary Usage 

To store files created from the API extraction AWS Lambda. 
The service acts as a staging area to store output files to be used within the transformation scripts.

Proposed Storage Class: S3 Glacier Flexible 

#### AWS S3 File Breakdown 

Below is the proposed file tree diagram for the file structure of the S3 bucket 
```
AWS S3/
├── data_source/
│   ├── 00_staged_files/
│   │   ├── Year
│   │       ├── Month
│   │           ├── Day
│   │               └── source_name_year_month_day_hour_minute_second.extension
│   ├── 01_loaded_files/
│   │   ├── Year
│   │       ├── Month
│   │           ├── Day
│   │               └── source_name_year_month_day_hour_minute_second.extension
│   ├── 00_errored_files/
│   │   ├── Year
│   │       ├── Month
│   │           ├── Day
│   │               └── source_name_year_month_day_hour_minute_second.extension

```
An example of a file placed in S3 

```
api_source/00_staged_files/2026/10/25/api_source_2026_10_25_13_02_56.csv
```

### AWS EventBridge
Serverless event bus service, which aims to process events for when a file lands inside AWS S3. 

The service triggers the AWS Lambda Data Transformations function. 

### AWS RDS
Fully managed cloud service database; supporting database engines such as: 

- PostgreSQL
- Oracle
- SQL Server
- MariaDB
- Amazon Aurora

Current database engine decision is to use PostgreSQL 18.3. 



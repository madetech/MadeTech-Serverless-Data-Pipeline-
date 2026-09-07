# Overview 
Last Updated: 07/09/2026

This document details the decisions made for the project. 

# 001 - Choosing The Cloud Provider

## Context 
The project involves creating an ETL pipeline, which can be reliably scaled to meet extra demands such as: 

- Increased volumes of data
- Increased variety sources of data

The solution must be cost efficient, and require minimal maintenance once implemented. 


### Options Considered 
- Azure (Microsoft Azure)
- AWS (Amazon Web Services)
- GCP (Google Cloud Platform)

Currently, MadeTech has cloud sandboxes within AWS and Azure, with no GCP sandbox at the time of writing. 

## Decision 
Due to the availability of Cloud sandboxes within MadeTech, AWS was chosen as the cloud platform of choice. 


## Consequences 
### Advantages 
- Current sandbox infrastructure allows for simple deployments, and maintenance.
- A larger array of specialised tools and services to allow for project expansion.
  
### Disadvantages 
- AWS Sandbox is torn down at the end of each week, Friday midday, meaning resources will need to be recreated at the start of each week.

### Considerations for Disadvantages 
- Utilise Infrastructure as Code Tools, such as AWS CloudFormation or Terraform to automate the creation of resources on AWS.

  
# 002 - API Extraction Decision 

## Context 
APIs allow users to access and consume data and services from various independent resources. 

They can be used to run test data, and work with real datasets.

### Options Considered 
- Source Databases
- Semi Structured File Formats (i.e. .csv, excel files or .json) 
- Kafka Topics 
- Secure File Transfer Protocol (SFTP)
- APIs

## Decision 
The decision is to use APIs, due to their flexibility, and ability to retrieve data from different types of sources. 

The plan is to use APIs which contain testing data, then move onto other APIs, which contain realistic datasets. 

A list of public APIs can be found here. 

https://github.com/public-apis/public-apis

While Kafka Topics, Source Databases and SFTP provide resilient, stable sources for the extraction of data, these systems would need to be configured within the AWS environment before extracting data from these systems. 

The cost overheads are also higher for maintaining these systems. 
Furthermore, the AWS sandbox removes these resources every week, meaning they would need to be reconfigured at the start of each week -- creating higher amounts of technical debt. 

Semi Structured File Formats would need to be created manually, and uploaded to a staging area. 

While the semi-structured file formats are an ideal solution, the manual creation, configuration and uploading of these resources creates extra manual processing, which the pipeline aims to avoid. 
## Consequences

### Advantages 
- Allows for retrieval of data from different, and varied sources
- No up front cost to set up a back-end data retrieval system such as a source database or SFTP server. 
### Disadvantages 
- Authentication methods vary depending on the API
- Different APIs have different methodologies of retrieving data, leading to increased technical debt on the API Extraction script. 

# 003 - Component Decision: AWS Lambda 

## Context 
AWS Lambda allows for users to run serverless functions within AWS. 
Billing for Lambdas only occurs during their execution, and the number of requests made, making them a lightweight solution for the scope of this project. 

https://aws.amazon.com/lambda/pricing/

### Other Options Considered 
- AWS Glue
- AWS Redshift
- AWS Databricks
- *Talend
- *Integrate.io

* No to low-code tools to automate AWS Pipelines.

## Decision 
After careful consideration, the decision is to go with AWS lambda due to its low cost and versatility. 

For the scope of the project, two AWS Lambdas can be created. 
The first lambda being responsible for the API Extraction and the second lambda being responsible for data transformations. 

Other options such as AWS Redshift, AWS Glue and AWS Databricks incur greater costs. 
 

## Consequences 
### Advantages 
- Low cost per request in comparison to other services
- Can be written in a variety of programming languages
### Disadvantages
- High code solution: can create further technical debt.
- Long term support issues with runtime code versions. AWS will not support failed lambda functions if the runtime code version is no longer supported by AWS.
  
# 004 Component Decision: AWS S3

## Context 
The project requires a staging area used to store files and outputs generated from extracting data from the API 
### Other Options Considered 
- Amazon FSx
- Amazon Elastic File System (EFS)
- Amazon Elastic Block Store (EBS)

## Decision 
The decision is to use AWS S3 due to its high scalability and low storage cost per object. 

## Consequences 
### Advantages 
- Cost per object storage is cheaper than alternatives.
- Files can be moved into different storage tiers depending on the use case. 
### Disadvantages 
- Requires specific fine-grained IAM Roles and permissions to access Buckets.
# 005 - Component Decision: AWS EventBridge 

## Context 
To automate the process between when a file is landed, and when a file is processed, the project requires usage of event driven architecture. 

Event driven architecture simplifies the typical batch processing load process; allowing for data to be processed at anytime.

### Other Considerations 
- Confluent
- Snowflake SnowPipe
- Amazon Eventbridge
- Amazon Simple Queue Service (SQS)
- Amazon Simple Notification Service (SNS)
- Amazon API Gateway

## Decision 
The decision is to use AWS EventBridge to act as a automation layer between AWS S3 and the AWS Lambda which is responsible for data transformations. 

## Consequences 
### Advantages 
- No to low-code interface with syncing services
- Can create different types of rules
- No upfront costs of usage
### Disadvantages
- Has a limit of up to 5 different AWS services
  
# 006 - Component Decision: AWS RDS 

## Context 
To provide a storage solution to data which has been successfully transformed within the project. 

### Other Considerations 
- AWS DyanamoDB
- Amazon Aurora

## Decision 
The decision is to use AWS RDS, due to its high availabilty, and wide choice of database engines. 

Unlike DynamoDB, AWS RDS follows a strict Relational schema, which allows for consistent transactions between scripts and the database. 

Where DynamoDB has advantages in its NoSQL architecture. Extra considerations must be put in place to choosing the correct partition key for the data. 

Due to the volume and variety of data consumed by the APIs, DynamoDB would struggle to scale as more sources are added to the pipeline. 

### Database Engine Decision 
After thoughtful consideration, the decision is to use PostgreSQL for the database engine. 

This is due to PostgreSQL being open source, and its availability across the three main operating systems, Mac, Linux and Windows. 

PGAdmin4 or DBeaver make for simple user interfaces, which allow users to directly connect to the database to retrieve data. 

Furthermore, PostgreSQL supports schemas, which can be used to separate the different layers of the transformation process. 
## Consequences 

### Advantages 
- Automated database snapshots / backups
- Ability to control inbound / outbound networking rules for different users. 
### Disadvantages 
- Strict schema requirements
- Requires further configurations using user personas and profiles within the database. 

# 007 - Version Control Strategy 

## Context 
Provision of a suitable version control methodology to allow for swift and efficient changes made within the project. 

## References Considered 

- https://dev.to/karmpatel/git-branching-strategies-a-comprehensive-guide-24kh#choosing-the-right-strategy
- https://medium.com/@sreekanth.thummala/choosing-the-right-git-branching-strategy-a-comparative-analysis-f5e635443423
- https://www.abtasty.com/blog/git-branching-strategies/

### Strategies Considered  
- Git Flow
- Github Flow
- Trunk-Based Development
- Feature Branching
- Environment Branching
- Release Branching
- Forking Workflow 

## Decision 
The decision was split between **Git Flow** and **Feature Branching** strategies. 
Both strategies are simple to implement, and accommodate the smaller team size. 

The overall decision was to go with a Git Flow strategy; featuring an extra branch, **Dev**, to act as a buffer for new changes before pushing these newer changes to main. 

<img width="1626" height="620" alt="image" src="https://github.com/user-attachments/assets/de2239eb-4355-4c16-a60d-0367d95068e0" />



## Consequences 

### Advantages 
- Suitable for a small team (around 5-6 people)
- Minimizes branch management
- Supports continuous deployments
  
### Disadvantages 
- Does not scale well for larger teams (20+ people)
- No clear branches for running tests
- Poor agility in managing releases
 
# 008 - Data Transformations Script Strategy 

## Context 

Creation of a reusable python framework, which is suitable for reading, transforming and loading data into the target database. 

## Approaches Considered 

### Functional Programming
A singular .py script, which contains all of the necessary functions needed to perform the ETL process. 

A main function would be responsible for running the full process. 

#### Functions considered 

- extract_from_s3 
- extract_from_source_db

If the medallion architecture is chosen, the outputs of these functions would represent the bronze layer of the pipeline. 

- connect_to_db
  
Function to create a connection to the database using sqlalchemy 

- load_to_db
  
Uploads tables to the database using the connection created in **connect_to_db**

- create_metadata_table
  
Creates a metadata_table responsible for giving instructions on how the data will be processed in the pipeline.

- apply_primary_foreign_keys
  
Runs a .sql script against specified tables within the database, applying their primary and foreign key relationships.

###### Medallion Architecture Specific Functions 

- preserve_history

A function responsible for preserving historical records of the pipeline if needed. 

- create_silver_table
  
Creates the silver table for the pipeline.
Calls the perserve_history function inside the create_silver_table to create a table with historical records intact

- create_gold_table
  
Creates an up-to-date, latest version of the data.

Tables are then used to create the data model. 


##### Custom Framework Functions 

Each function below is responsible for creating each of the tables within each of the processing layers 

- create_staging_table

Creates a temporary staging table based on information from the metadata table. 

Within this layer, tables are dropped and recreated on each run. 

- create_history_table

Creates a consolidated historical table, which contains up-to-date and historical records for the table, which is being processed. 

The records are assessed by comparing hashes between the current staging table, and the current history table. 

If there are differences between the hashes, only the latest records are merged into the history table. 

- create_surrogate_key_table

Creates a table, which manages the surrogate keys for each of the tables processed within the pipeline. 

NOTE: this layer may be skipped if the data is being replaced, and history is not being preserved. 

- transform_data_source
A function which provides custom logic to transform the data_extracted from the data source.

Relies on other helper functions to execute depending on what table is being processed. 

There is an appetite for this function to be placed inside a separate .py script should the complexities increase the level of technical debt. 

- create_dimensional_table

Creates an up-to-date dimension table using the outputs of the surrogate key and historical tables. 

- create_fact_table

Creates a fact table based on the outputs of the dimensional tables. 

The level of granularity of the fact table can be set by the user via the metadata table. 

- main
  
Main function, which runs the entire pipeline.

Function order is dependent the framework chosen: medallion or custom framework. (TO BE DECIDED) 

### Object Oriented Programming 
Utilization of Python classes to create custom python modules to be called inside a main.py 

#### Scripts and Classes 

##### data_ingestion.py 

A script responsible for the ingestion of data. 

Contains a class **DataIngestor** which contains the following methods 

- extract_from_s3

- extract_from_source_db

If the medallion architecture is chosen, the outputs of these functions would represent the bronze layer of the pipeline. 


##### historical_data.py 

A script which contains the handling of historical data and records. 

Contains the class **HistoricalDataProcessor**

- create_hash_column

Creates a hash column to be used to compare rows within the tables. 

The hash column created is dependent on a subset of columns to compare records. 

- compare_hashes

Takes in two tables to compare their hashes. 

Records are identified with the following flags. 

Identical (I) 
Changed (C) 
New (N) 

New and changed records are appended to the historical table. 

##### data_connector.py 

- connect_to_db
  
Function to create a connection to the database using sqlalchemy 

- load_to_db
  
Uploads tables to the database using the connection created in **connect_to_db**

## Decision 

The decision is to go with an Object Oriented Programming (OOP) approach as this will create a package of resuable, custom-made python modules, which can be utilized within other future project endeavours. 

## Consequences 

### Advantages 

+ Reusable Python modules, which can be used across future projects.
+ Isolates functionalities into different methods, which can be called within one instance of a class.
+ Can use inheritance to create child classes of the parent class to cover situations where custom logic is needed. 

### Disadvantages 

- Difficult to maintain in comparison to functional programming (one script vs three scripts).
- Requires robust documentation on class strategies, such as inheritance.
- Has the potential to be an over-engineered solution. 

# 009 - AWS Lambda Deployment Strategy Using Lambda Layers

## Context 

To facilitate the execution of AWS Lambda functions, which contain external libraries and dependencies. 

List of known dependencies. 

- Pandas
- Requests
- SQLAlchemy
- Numpy 

Other alternative deployment options 

- Containerised Lambda Function

## Decision 

The decision was to go for a deployment featuring lambda layers. 

This was because lambda layers act as a reusable dependency layer, which can be attached to each Lambda function within the project. 

Containerized Lambdas, whilst allowing for greater storage, require the usage of AWS Elastic Container Registry (ECR), which will incur a greater level of costs attached to the project. 

## References Considered 

- https://pcg.io/insights/lambda-containers/

## Consequences 

### Advantages 

+ Reusable dependencies layer, which is compatible with both Lambda functions.
+ Can be updated with differing versions both on AWS Lambda and version control via Git
+ More cost-effective than containerized lambdas. 
### Disadvantages

- Running Numpy on MacOS requires it to be built within an Amazon Linux Docker Container, which increases tech debt.
(For more information on this issue, check this link: https://medium.com/@humzahmalik/how-to-import-pandas-on-aws-lambda-for-mac-users-using-layers-44079af6a512 ) 

- Lambda size limit is 50 KB. Larger files cannot be uploaded to AWS Lambda directly. Instead, they must be uploaded to AWS S3 before uploading them to AWS Lambda.

- Greater operational overhead in comparison to Lambda Layers. 

# 010 - Component Decision -  AWS EventBridge Scheduler 

## Context 

To automate the scheduling of the ETL pipeline on AWS. 

The current flaw of the current ETL pipeline design is that the initial AWS Lambda, **api_extraction** must be triggered manually in order to run the rest of the pipeline. 

In order to choose a component, two options were discussed, and weighed up for their pros and cons on Thursday 3rd September 2026. 

The two options were: 

- AWS EventBridge Scheduler 
- AWS Step Functions


## Other Options Considered 

- AWS Step Functions
- AWS Managed Apache AirFlow 
- AWS SageMaker 

## Decision 

The decision was to go with AWS EventBridge Scheduler to automate the running the pipeline. 

The schedule can be setup via a Crontab expression 

This is due to the fact that only one lambda, **api_extraction** , must be triggered in order to execute the pipeline. 

However, it was discussed that, should the solution be dependent on different lambdas, which are responsible for extracting from different types of data sources, that a Step Function would be appropriate. 

This decision is subject to change if there are extra AWS Lambdas required, which satisfy the above conditions. 

## Consequences 

### Advantages 

+ Simplicity of deployment within the pipeline.
+ 14 million invocations a month for free.
+ Able to hook up CloudWatch Logs to Eventbridge Scheduler.

### Disadvantages

- Simplified approach. Will require different EventBridge schedulers for different extraction based lambda approaches.

# 011 - Component Decision -  Mechanism Change

## Context 

## Decision 

## Consequences 

### Advantages 

### Disadvantages


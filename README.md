# MadeTech-Severless-Data-Pipeline

# Purpose 

The purpose of the project is to create a low-cost, serverless data pipeline on AWS. 

Utilising an Event Driven Architecture (EDA), data from an api is processed via two lambda functions: **api_extraction** and **data_transformation**; with an S3 bucket acting as a staging area to house the extracted data. 

AWS Eventbridge acts as a trigger to call the **data_transformation** lambda function, which is responsible for transforming and loading the data to an AWS RDS. 


# High Level Overview Diagram 
<img width="3284" height="1190" alt="image" src="https://github.com/user-attachments/assets/9b750100-ee74-445f-ba04-795935342b44" />


# Use Cases 

- To act as an MVP for MadeTech clients looking for a cost-effective, Software as a Service (SaaS) solution. 

- To provide an automated, reusable, event-driven pipeline framework. 

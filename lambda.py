import boto3
import os
from pprint import pprint
import time

logs = boto3.client('logs')
ssm = boto3.client('ssm')

def lambda_handler(event, context):
    extra_args = {}
    log_groups = []
    log_groups_to_export = []
    
    if 'S3_BUCKET' not in os.environ:
        print("Please create S3_BUCKET environment variable and its value in lambda function")
        return
    
    print("--> S3_BUCKET=%s" % os.environ["S3_BUCKET"])

    if 'LOG_GROUP_NAME' not in os.environ:
        print("Please create LOG_GROUP_NAME environment variable and its value in lambda function")
        return
    
    print("--> S3_BUCKET=%s" % os.environ["S3_BUCKET"])
    print("--> LOG_GROUP_NAME=%s" % os.environ["LOG_GROUP_NAME"])
    
log_group_name = os.environ["LOG_GROUP_NAME"]
ssm_parameter_name = ("/log-exporter-last-export/%s" % log_group_name).replace("//", "/")

try:
    ssm_response = ssm.get_parameter(Name=ssm_parameter_name)
    ssm_value = ssm_response['Parameter']['Value']
except ssm.exceptions.ParameterNotFound:
    ssm_value = "0"
        
export_to_time = int(round(time.time() * 1000))
        
print("--> Exporting %s to %s" % (log_group_name, os.environ['S3_BUCKET']))

try:
    response = logs.create_export_task(
        logGroupName=log_group_name,
        fromTime=int(ssm_value),
        to=export_to_time,
        destination=os.environ['S3_BUCKET'],
        destinationPrefix="logs"
    )
    print("Task created: %s" % response['taskId'])
            
except logs.exceptions.LimitExceededException:
    print("Only one active (running or pending) export task at a time, per account, is allowed. ef.: > https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/cloudwatch_limits_cwl.html. Continuing later...")
    pass

except Exception as e:
    print("Error exporting %s: %s" % (log_group_name, getattr(e, 'message', repr(e))))
    pass

ssm_response = ssm.put_parameter(
    Name=ssm_parameter_name,
    Type="String",
    Value=str(export_to_time),
    Overwrite=True)

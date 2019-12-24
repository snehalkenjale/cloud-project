import json
import boto3
from boto3.dynamodb.conditions import Key, Attr
import datetime
import random 
from botocore.exceptions import ClientError


dynamodb = boto3.resource('dynamodb')

table_tech = dynamodb.Table("TechQBank")
table_sit = dynamodb.Table("SitQBank")
table_report = dynamodb.Table("InterviewReport")
table_curr_qid = dynamodb.Table("currentQuestion")


choices = ['a','b','c','d','A','B','C','D']
min_range = 1
max_range = 15
max_questions = 3


def getQuestion(table, qid):
    response = table.query(KeyConditionExpression=Key('id').eq(int(qid)))
    print('Question : ', response)
    return response['Items'][0]


def saveUserAnswer(table, user_id, qid, option):
    answer = getQuestion(table_tech, qid)["Answer"]
    correct = answer.lower() == option.lower()
    timeStamp = str(datetime.datetime.now())
    dict = {
        'id' : timeStamp,
        'user_id': user_id,
        'qid': qid,
        'selected_option':  option,
        'correct': correct,
        'heartbeat' : random.randrange(60, 100, 1)
    }
    print('Item : ', dict)
    table.put_item(Item=dict)


def saveCurrentQuestion(table, qid, count):
    dict = {
        'id' : '1',
        'qid': qid,
        'count': count
    }
    print('Item : ', dict)
    table.put_item(Item=dict)
    
    
def checkCurrentQuestion(table):
    response = table.query(KeyConditionExpression=Key('id').eq("1"))
    if response['Items'][0]['count'] > max_questions:
        return 0  
    else: 
        return response['Items'][0]['count']


def getCurrentQuestion(table):
    response = table.query(KeyConditionExpression=Key('id').eq('1'))
    print('Question : ', response)
    return response['Items'][0]['qid']

def sendSMS(phonenumber):
    region = "us-east-1"
    applicationId = "e04aaa63a57b4d40abbce341d5e768f9"
    msg = 'Here a link to your report : ' + 'https://us-east-1.quicksight.aws.amazon.com/sn/dashboards/58670e59-99c7-4f94-8d40-e709a48107c5'
    ses = boto3.client('ses')
    sns = boto3.client('sns')
    # print (event)
    topic_name = 'report'
    # topic = sns.create_topic(Name = topic_name)
    # msg = message_template(common_data,raw_data)
    # c_data_phone = common_data['Records'][0]['messageAttributes']['PhoneNumber']['stringValue']
    # c_email = common_data['Records'][0]['messageAttributes']['Email']['stringValue']
    tpcArn = 'arn:aws:sns:us-east-1:410382174225:report'

    
    # Email Template
    # contact = c_data_phone
    subs = sns.subscribe(
        TopicArn=tpcArn,
        Protocol='email',
        Endpoint= phonenumber  # <-- number who'll receive an SMS message.
    )

    msgresponse = sns.publish(
    TopicArn = 'arn:aws:sns:us-east-1:410382174225:report',    
    Message=msg)
    
        

def lambda_handler(event, context):
    print ("Event : ",event)
    try:
        query = event['inputTranscript']
        print('query-', query)
        if query.startswith('option'):
            try:
                option = event['currentIntent']['slots']['answer']
                if not option:
                    option = event['currentIntent']['slotDetails']['answer']['originalValue']
                try:
                    if option.endswith('.'):
                        option = option[:-1]
                except:
                    print('')
                if option in choices:
                    qid = getCurrentQuestion(table_curr_qid)
                    print(option, qid)
                    user_id = '1'
                    saveUserAnswer(table_report, user_id, qid, option)
                    response = 'Answer recorded'
                    count = checkCurrentQuestion(table_curr_qid)
                    if count != 0:
                        response = response + "Lets go to next question"
                    else:
                        saveCurrentQuestion(table_curr_qid, qid, 1)
                        response = 'Your interview is over. Thank you for your time. You can now check your results in your email.'
                else:
                    response = 'Choose valid option'
            except Exception as e:
                print(e)
                response = 'Say the option again'
        elif query.startswith('what'):
            qid = random.randrange(min_range, max_range, 1)
            print(qid)
            question = getQuestion(table_tech, qid)
            count = checkCurrentQuestion(table_curr_qid)
            if count != 0:
                saveCurrentQuestion(table_curr_qid, qid, count+1)
                response = question["Question"]
                response = response + " <break time=\"1000ms\"/>Your options are  "
                response = response + " <break time=\"1000ms\"/>Option A   " + question["A"]
                response = response + " <break time=\"1000ms\"/>Option B  " + question["B"]
                response = response + " <break time=\"1000ms\"/>Option C  " + question["C"]
                response = response + " <break time=\"1000ms\"/>Option D  " + question["D"]
                response = response + " <break time=\"1000ms\"/>Select your option"
            else:
                saveCurrentQuestion(table_curr_qid, qid, 1)
                response = 'Your interview is over. Thank you for your time. You can now check your results in your email.'
            print(response)
        elif query.startswith('yes'):
            print('yes')
            # option = event['currentIntent']['slots']['phone']
            option = 'mbj282@nyu.edu'
            sendSMS(option)
            response = 'Your report has been sent to you.'
        else:
            response = ''
        return {     
            "sessionAttributes": {
                "key1": "value1",
                "key2": "value2"
            },   
            "dialogAction": {     
                "type": "Close",
                "fulfillmentState": "Fulfilled",
                "message": {       
                    "contentType": "PlainText",
                    "content": '<speak>' + response + '</speak>'
                    # "content": response
            }   
        } 
    }
    except Exception as e:
        print(e)
        return {     
            "sessionAttributes": {
                "key1": "value1",
                "key2": "value2"
            },   
            "dialogAction": {     
                "type": "Close",
                "fulfillmentState": "Fulfilled",
                "message": {       
                    "contentType": "PlainText",
                    "content": '<speak></speak>'
                }    
            }
        }

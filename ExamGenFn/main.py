from utils.helper_files import HelperFiles
from utils.helper_bedrock import HelperBedrock
import json
import boto3
import urllib.parse
import os
sns = boto3.client('sns')
s3 = boto3.client('s3')
bedrock = HelperBedrock()

sns_topic_arn = os.environ['SNS_TOPIC_ARN']
#email_address = os.environ['NotificationEmail']
questions_bank_location = 'questions_bank'



response_format = """[
{
    "question": "What is the colour of the car in the book?",
    "options": ["Blue", "Green", "Yellow", "Grey"],
    "correct_answer": "Yellow"
},
{
    "question": "what is the capital of France?",
    "options": ["Paris", "Brussels", "Dublin", "London"],
    "correct_answer": "Paris"
},
{
    "question": "The Sky is blue?",
    "options": ["True", "False"],
    "correct_answer": "True"
}
]"""
escaped_format = response_format.replace('{', '{{').replace('}', '}}')
template_formatted=f"""
    Human: using this format {escaped_format} as reference, modify this response to json
    <response>
    {{text}}
    </response>

    Assistant:"""

def main(event, context):
    
    file_key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'], encoding='utf-8')
    bucket_name = event['Records'][0]['s3']['bucket']['name']
    print(f"Creating exam from file {file_key}")
    
    try:
        response = s3.get_object(Bucket=bucket_name, Key=file_key)
        file_object = response['Body'].read()
    except Exception as e:
        print(e)
        print('Error getting object {} from bucket {}. Make sure they exist and your bucket is in the same region as this function.'.format(file_key, bucket_name))
        raise e
    file_helper = HelperFiles(bucket_name=bucket_name, file_object=file_object)
    file = file_helper.get_pdfobject_text()
    
    #setting default values for metadata 
    n_mcq = 5
    n_tfq = 3
    n_mcq_options = 4
    try:
        metadata = response['Metadata']
        print("METADATA", metadata, type(metadata))
        n_mcq = int(metadata['n_mcq'])
        n_tfq = int(metadata['n_tfq'])
        n_mcq_options = int(metadata['n_mcq_options'])
        print(f"params {n_mcq=}, {n_tfq=}, {n_mcq_options=}")
    except:
        print(f"no metadata found, setting default values")
    
    template_instruction = f"""Human: You are a teacher during examination time and you are responsible for creating exam questions from the student study book.before creating the questions- Analyze the book found between <exam_book> </exam_book> tags, to identify distinct chapters, sections, or themes for question generation.
                               - For true/false questions, select statements that can be clearly identified as true or false based on the book's content.
                               - For MCQs, develop questions that challenge the understanding of the material, ensuring one correct answer and {n_mcq_options-1} distractors that are relevant but incorrect.
                               - Randomize the selection of pages or topics for each run to generate a new set of questions, ensuring no two sets are identical.
                               Please provide the questions in this format exactly
                               for MCQ:
                                  - the output should be like     
                                   "question": "What is the colour of the car in the book?",
                                   "options": ["Blue", "Green", "Yellow", "Grey"],
                                   "correct_answer": "Yellow"
                               For True/False:
                                  - the output should be like     
                                   "question": "is the sky Blue?",
                                   "options": ["True", "False"],
                                   "correct_answer": "True"
                               
                               
                               Generate {n_tfq} true/false and {n_mcq} multiple-choice questions (MCQs) ensuring each question pertains to different pages or topics within the book. For MCQs, provide [n_mcq_options] options for each question. Focus on creating unique questions that cover a broad spectrum of the book's content, avoiding repetition and ensuring a diverse examination of the material. Use the following guidelines:
                               
                               1. True/False Questions:
                                  - Craft each true/false question based on factual statements or key concepts from the book.
                                  - Ensure each question spans a wide range of topics to cover the book comprehensively.
                               
                               
                               2. Multiple-Choice Questions (MCQs):
                                  - Formulate each MCQ to assess understanding of significant themes, events, or facts.
                                  - Include {n_mcq_options} options per MCQ, making sure one is correct and the others are plausible but incorrect.
                                  - Diversify the content areas and pages/topics for each MCQ to avoid overlap and repetition. 
                                  """   
    template_instruction += """
                           <exam_book>
                           {text}
                           </exam_book>
                           
                           Assistant:"""  


    response = bedrock.get_response(file, template_instruction)
    response = bedrock.get_response(response, template_formatted)
    json_exam = file_helper.convert_to_json_in_memory(response)

    file_directory = file_key.split("/")[0]
    file_name = file_key.split("/")[1].split(".")[0]
    file_path = questions_bank_location +'/'+file_name+'.json'
    file_helper.upload_to_s3(json_exam, bucket_name, file_path)
    
    # Publish the message to the SNS topic
    email_message = 'Hello, Exam Generated'
    sns.publish(
        TopicArn=sns_topic_arn,
        Message=email_message
    )
    return {
        'statusCode': 200,
        'body': json.dumps('file saved to file_path!'),
    }
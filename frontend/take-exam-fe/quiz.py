import requests
import streamlit as st
import os
from streamlit.web.server.websocket_headers import _get_websocket_headers
import base64
import json
import boto3
from botocore.exceptions import ClientError
st.set_page_config(page_title="Take Quiz", page_icon="📝")
# URL of the API Gateway
#API_GATEWAY_URL = 'https://htprjtcml7.execute-api.us-east-1.amazonaws.com/test/exam'

API_GATEWAY_URL = os.getenv('API_GATEWAY_URL')

# Initialize session state variables
if 'current_question' not in st.session_state:
    st.session_state['current_question'] = 0
if 'answers' not in st.session_state:
    st.session_state['answers'] = {}
if 'selected_file' not in st.session_state:
    st.session_state['selected_file'] = None
if 'questions' not in st.session_state:
    st.session_state['questions'] = []
if 'show_results' not in st.session_state:
    st.session_state['show_results'] = False  # Flag to display the results page

headers = _get_websocket_headers()
token = headers.get('X-Amzn-Oidc-Data')
parts = token.split('.')
if len(parts) > 1:
    payload = parts[1]

    # Decode the payload
    decoded_bytes = base64.urlsafe_b64decode(payload + '==')  # Padding just in case
    decoded_str = decoded_bytes.decode('utf-8')
    decoded_payload = json.loads(decoded_str)

    # Extract the email
    email = decoded_payload.get('email', 'Email not found')
    print(email)
else:
    print("Invalid token")

st.write(f"You're Taking the Exam as: {email}")


st.sidebar.header("Exam Assessment - AI")
#st.sidebar.image("ailogo.png", width=100)  # Adjust the path to your logo image
st.sidebar.markdown("""Here you can take the quizzes you created in the Generate Quiz page.

At the end of the quiz you will immediately get your results.""")

def strip_file_extension(filename):
    if "." in filename:
        return filename[:filename.rindex(".")]
    else:
        return filename
# Function to load questions from S3 through the API Gateway
def load_questions_from_s3(file_name):
    timeout = 300
    response = requests.get(f'{API_GATEWAY_URL}?object_name={file_name}', timeout=timeout)
    response.raise_for_status()  # Raises HTTPError for bad responses (4xx and 5xx)
    questions = response.json()
    return questions

# Function to get the list of files in the questions_bank directory in S3 through the API Gateway
def get_files_in_questions_bank():
    timeout = 300
    response = requests.get(API_GATEWAY_URL, timeout=timeout)
    response.raise_for_status()  # Raises HTTPError for bad responses (4xx and 5xx)
    files = response.json()
    return files

# Start page: File selection
def start_page():
    col1, col2 = st.columns([4, 1])  # Create two columns
    with col1:  # With first column
        st.title("Test your knowledge📝")
    #add your own logo
    #with col2:  # With second column
    #    st.image("logo.png",
    #             caption="", width=100)

    files = get_files_in_questions_bank()
    f_dic = {strip_file_extension(file): file for file in files}
    selected_file = st.selectbox("Select Quiz", ["Select a quiz"] + list(f_dic.keys()))
    if selected_file != "Select a quiz":
        st.session_state['selected_file'] = f_dic[selected_file]

    if st.session_state['selected_file']:
        if st.button("Load quiz"):
            st.session_state['questions'] = load_questions_from_s3(st.session_state['selected_file'])
            st.session_state['current_question'] = 0
            st.session_state['answers'] = {}
            st.session_state['show_results'] = False  # Ensure results are not shown yet
            st.experimental_rerun()

# Quiz page: Display one question at a time with the user's previous selection
def quiz_page():
    if st.session_state['questions']:
        current_question_data = st.session_state['questions'][st.session_state['current_question']]
        st.title(f"Question {st.session_state['current_question'] + 1}/{len(st.session_state['questions'])}")
        st.write(current_question_data['question'])

        options = current_question_data['options']
        default_index = None  # No pre-selection

        # Check if an answer was already given to this question
        if st.session_state['current_question'] in st.session_state['answers']:
            default_index = st.session_state['answers'][st.session_state['current_question']]  # get previously selected option

        user_answer = st.radio("Options", options, index=default_index, key=f"question_{st.session_state['current_question']}")

        # If an option is selected
        if user_answer:
            st.session_state['answers'][st.session_state['current_question']] = options.index(user_answer)

        col1, col2 = st.columns([4, 1])
        if st.session_state['current_question'] > 0:
            if col1.button("Back", key=f"back_button_{st.session_state['current_question']}"):  # Modified this line
                st.session_state['current_question'] -= 1
                st.experimental_rerun()

        if st.session_state['current_question'] < len(st.session_state['questions']) - 1:
            if col2.button("Next") and user_answer:  # Only go next if an option is selected
                st.session_state['current_question'] += 1
                st.experimental_rerun()
        else:
            if col2.button("Submit") and user_answer:  # Only submit if an option is selected
                st.session_state['show_results'] = True  # Set the flag to display results
                st.experimental_rerun()

# Results page: Evaluate answers and display results
def results_page():
    st.title("Results")
    score = 0
    results_data = []  # List to hold each question's result
    for idx, question in enumerate(st.session_state['questions']):
        user_answer_index = st.session_state['answers'][idx]
        correct_answer = question['correct_answer']

        question_str = f"**Q{idx+1}**: {question['question']} "
        answers_str = f"&nbsp;&nbsp;&nbsp;&nbsp;Correct answer: {correct_answer}"
        if question['options'][user_answer_index] == correct_answer:
            score += 1
            question_str += "✅"
        else:
            question_str += "❌"
            answers_str += f"&nbsp;&nbsp;&nbsp;&nbsp;Your answer: {question['options'][user_answer_index]}"
        st.markdown(question_str)
        st.markdown(answers_str)
        is_correct = question['options'][user_answer_index] == correct_answer
        # Append result for each question
        results_data.append({
            "question": question['question'],
            "user_answer": question['options'][user_answer_index],
            "correct_answer": correct_answer,
            "is_correct": is_correct
        })

    percentage = int((score / len(st.session_state['questions'])) * 100)
    pass_status = "passed" if percentage >= 50 else "failed"

    # Compile final results data
    final_results = {
        "email": email,
        "score": score,
        "result": pass_status,
        "details": results_data
    }
    save_quiz_results(final_results)

    st.subheader(f"You scored {score}/{len(st.session_state['questions'])}. That's {percentage}%. You {pass_status}.")

    if st.button("Close"):
        st.session_state['current_question'] = 0  # Resetting the question number
        st.session_state['answers'] = {}  # Clearing the answers
        st.session_state['questions'] = []  # Clearing the questions
        st.session_state['selected_file'] = None  # Resetting the selected file
        st.session_state['show_results'] = False  # Reset the flag
        st.experimental_rerun()  # Rerunning the app from start


def save_quiz_results(data):

    # Initialize DynamoDB table
    table_name = os.getenv('DYNAMODB_TABLE_NAME')
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(table_name)
    table.put_item(Item=data)

def main():
    if st.session_state['show_results']:
        results_page()
    elif not st.session_state['questions']:
        start_page()
    else:
        quiz_page()

# Run the app
if __name__ == "__main__":
    main()

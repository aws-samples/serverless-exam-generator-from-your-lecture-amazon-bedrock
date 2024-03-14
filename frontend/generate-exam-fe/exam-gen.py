import streamlit as st
import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError, ClientError
import os 

# Initialize AWS S3 client with the default profile
s3 = boto3.client('s3')

# Define a Streamlit app
st.set_page_config(page_title="Generate Quiz", page_icon="🪄")
st.sidebar.header("Generate Quiz")
#st.sidebar.image("exam-logo.png", width=100)  # Adjust the path to your logo image
st.sidebar.markdown("""Here you can generate your quiz, made of multiple choice and true/false questions. 

You can start by uploading a PDF file for the quiz topic.""")

def main():
    #bucketname = 'exam-generator-genai'
    bucketname = os.getenv('BUCKET_NAME')
    # Header with logo
    col1, col2 = st.columns([4, 1])  # Create two columns
    with col1:  # With first column
        st.title("Generate a new quiz🪄")
    #you can add your own logo

    #with col2:  # With second column
    #    st.image("logo.png",
    #             caption="", width=100)
    # Separator
    st.markdown("---")
    col1, col2 = st.columns([2, 2])  # Create two columns
    with col1:  # With first column
        n_mcq = st.number_input('How many multiple choice questions?', value=0,
                                step=1, min_value=0, max_value=20, format="%d", key="mcq")
    with col2:  # With second column
        if n_mcq > 0:
            n_mcq_options = st.number_input('How many options in a question?', value=2,
                            step=1, min_value=2, max_value=7, format="%d", key="mcq_n_options")
        else:
            n_mcq_options = 0
    n_tfq = st.number_input('How many true/false questions?', value=0,
                                step=1, min_value=0, max_value=20, format="%d", key="tfq")

    # File Upload
    uploaded_file = st.file_uploader("Upload PDF File", type=["pdf"])
    if uploaded_file is not None:
        # Display uploaded file details
        st.write("File Details:")
        st.write(f"Name: {uploaded_file.name}")
        st.write(f"Type: {uploaded_file.type}")
        st.write(f"Size: {uploaded_file.size} bytes")

        # Upload file to S3 in the "exams" directory with specified ContentType
        try:
            s3.upload_fileobj(
                uploaded_file,
                bucketname,
                'exams/' + uploaded_file.name,
                ExtraArgs={
                    'ContentType': 'application/pdf',
                    'Metadata': {
                        'n_mcq': str(n_mcq),
                        'n_tfq': str(n_tfq),
                        'n_mcq_options': str(n_mcq_options)
                    },
                })
            # Display completion message
            st.success("Upload completed!")
        except ClientError as e:
            # Specific error handling for AWS Client errors
            st.error(f"An error occurred: {e}")
        except NoCredentialsError:
            st.error(
                "No credentials provided. Please configure your AWS credentials.")
        except PartialCredentialsError:
            st.error(
                "Incomplete credentials provided. Please complete your AWS credentials.")
        except Exception as e:
            # General error handling
            st.error(f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    main()
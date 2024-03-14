import json
import os
import sys
import boto3
from langchain.llms.bedrock import Bedrock
from langchain.prompts import PromptTemplate

module_path = ".."
sys.path.append(os.path.abspath(module_path))
print(sys.path.append(os.path.abspath(module_path)))
from utils import bedrock, print_ww  # Importing utility functions

class HelperBedrock(object):
    """
    This class provides an interface to interact with the Bedrock API for generating text responses.
    """
    
    def __init__(self):
        """
        Initializes the HelperBedrock object by setting up the Bedrock client with the appropriate configuration.
        """
        # Obtain the Bedrock client using the utility function
        boto3_bedrock = bedrock.get_bedrock_client(
            assumed_role=os.environ.get("BEDROCK_ASSUME_ROLE", None),
            region=os.environ.get("AWS_DEFAULT_REGION", None)
        )

        # Configuration for inference requests
        inference_modifier = {
            'max_tokens_to_sample': 4096, 
            "temperature": 0.5,
            "top_k": 250,
            "top_p": 1,
            "stop_sequences": ["\n\nHuman"]
        }

        # Initialize the Bedrock LLM with the specified model and configuration
        self.textgen_llm = Bedrock(
            model_id="anthropic.claude-v2",
            client=boto3_bedrock, 
            model_kwargs=inference_modifier 
        )

    def get_response(self, text, template):
        """
        Generates a response based on the provided text and template.

        :param text: Input text for the prompt.
        :param template: Template for formatting the prompt.
        :return: The generated response from the model.
        """
        # Create a prompt template with multiple input variables
        multi_var_prompt = PromptTemplate(
            input_variables=['text'], 
            template=template
        )

        # Format the prompt with the input text
        prompt = multi_var_prompt.format(text=text)
        # Generate the response using the configured LLM
        response = self.textgen_llm(prompt)
        return response
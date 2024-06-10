import boto3
import streamlit as st
from streamlit.components.v1 import html
import json

# Initialize S3 client
s3_client = boto3.client('s3')

# Initialize Bedrock client
bedrock_client = boto3.client('bedrock-agent-runtime', 'eu-west-3')

st.set_page_config(
    page_title="Project Tracker",
    page_icon="📊",
    layout="wide",
)

# CSS for custom styling
st.markdown(
    """
    <style>
    .sidebar .sidebar-content {
        background-color: #2E2E2E;
        color: white;
    }
    .stButton>button {
        width: 100%;
        border-radius: 15px;
        background-color: #4CAF50;
        color: white;
        font-size: 18px;
    }
    .stButton>button:hover {
        background-color: #45a049;
        color: white;
    }
    .stTextInput>div>div>input {
        font-size: 18px;
        border-radius: 15px;
        padding: 10px;
    }
    .stChatMessage {
        border-radius: 15px;
        padding: 10px;
        margin: 5px 0;
    }
    .stChatMessage div[data-baseweb="block"] {
        font-size: 16px;
    }
    .assistant {
        background-color: #F8F9FA;
    }
    .user {
        background-color: #DCF8C6;
    }
    .highlight {
        color: #FFDA33;
    }
    .error {
        color: red;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("📊 Project Tracker")

st.sidebar.title("Project Documents")
selected_doc = None
bucket_name = 'projectstracker'
documents = []

def list_s3_documents(bucket_name):
    response = s3_client.list_objects_v2(Bucket=bucket_name)
    documents = []
    if 'Contents' in response:
        for obj in response['Contents']:
            key = obj['Key']
            if key.endswith('.pdf'):
                parts = key.split('_')
                if len(parts) >= 2:
                    company_name = parts[0]
                    city = parts[1]
                    documents.append({'company': company_name, 'city': city, 'key': key})
    return documents

documents = list_s3_documents(bucket_name)

if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

if 'selected_document' not in st.session_state:
    st.session_state.selected_document = None

if 'selected_workflow' not in st.session_state:
    st.session_state.selected_workflow = None

for doc in documents:
    if st.sidebar.button(f"{doc['company']} - {doc['city']}", key=doc['key']):
        st.session_state.selected_document = doc['key']
        st.session_state.selected_company = doc['company']
        st.session_state.selected_city = doc['city']
        selected_doc = doc

st.sidebar.title("Workflow Options")
workflow_options = ["Tech used", "Key contacts", "Delivery dates"]
for option in workflow_options:
    if st.sidebar.button(option, key=option):
        st.session_state.selected_workflow = option

if st.session_state.selected_document:
    st.write(f"Selected Document: **{st.session_state.selected_company} - {st.session_state.selected_city}**")

if st.session_state.selected_workflow and st.session_state.selected_document:
    query = f"Show me the {st.session_state.selected_workflow.lower()} for {st.session_state.selected_city} projects."
    questions = st.chat_input('Enter your questions here...', value=query)

    if questions:
        with st.chat_message('user'):
            st.markdown(questions)
        st.session_state.chat_history.append({"role": 'user', "text": questions})

        response = bedrock_client.retrieve_and_generate(
            input={'text': questions},
            retrieveAndGenerateConfiguration={
                'knowledgeBaseConfiguration': {
                    'knowledgeBaseId': 'UCVNLTOZKW',
                    'modelArn': 'arn:aws:bedrock:eu-west-3::foundation-model/anthropic.claude-3-haiku-20240307-v1:0'
                },
                'type': 'KNOWLEDGE_BASE'
            })

        answer = response['output']['text']

        with st.chat_message('assistant'):
            st.markdown(answer)
        st.session_state.chat_history.append({"role": 'assistant', "text": answer})

        if len(response['citations'][0]['retrievedReferences']) != 0:
            context = response['citations'][0]['retrievedReferences'][0]['content']['text']
            doc_url = response['citations'][0]['retrievedReferences'][0]['location']['s3Location']['uri']

            st.markdown(f"<span class='highlight'>Context used: </span>{context}", unsafe_allow_html=True)
            st.markdown(f"<span class='highlight'>Source Document: </span>{doc_url}", unsafe_allow_html=True)

        else:
            st.markdown(f"<span class='error'>No Context</span>", unsafe_allow_html=True)

else:
    st.chat_input('Enter your questions here...')

for message in st.session_state.chat_history:
    role_class = 'assistant' if message['role'] == 'assistant' else 'user'
    with st.chat_message(message['role']):
        st.markdown(f"<div class='stChatMessage {role_class}'>{message['text']}</div>", unsafe_allow_html=True)

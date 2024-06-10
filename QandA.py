import boto3
import streamlit as st

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
        background-color: #007BFF;
        color: white;
        font-size: 14px;
        padding: 8px;
    }
    .stButton>button:hover {
        background-color: #0056b3;
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
                    city = parts[1].replace('.pdf', '')
                    documents.append({'company': company_name, 'city': city, 'key': key})
    return documents

documents = list_s3_documents(bucket_name)

if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

if 'selected_document' not in st.session_state:
    st.session_state.selected_document = None

if 'selected_workflow' not in st.session_state:
    st.session_state.selected_workflow = []

# Add a dropdown for projects
project_options = [f"{doc['company']} - {doc['city']}" for doc in documents]
selected_project = st.sidebar.selectbox("Select a Project", project_options)

# Map the selected project to the document key
for doc in documents:
    if f"{doc['company']} - {doc['city']}" == selected_project:
        st.session_state.selected_document = doc['key']
        st.session_state.selected_company = doc['company']
        st.session_state.selected_city = doc['city']
        selected_doc = doc

if st.session_state.selected_document:
    st.sidebar.title("Workflow Options")
    workflow_options = ["Tech used", "Key contacts", "Delivery dates"]
    selected_workflow_options = st.sidebar.multiselect("Select Workflow Options", workflow_options)
    st.session_state.selected_workflow = selected_workflow_options

    if st.sidebar.button("Submit"):
        if st.session_state.selected_workflow:
            query = f"Show me the {', '.join(st.session_state.selected_workflow).lower()} for {st.session_state.selected_city} projects."
            st.session_state.query = query
            # Reset the selected document and workflow
            st.session_state.selected_document = None
            st.session_state.selected_workflow = []

# Add a text input for queries
questions = st.text_input('Enter your questions here...')
if questions:
    st.session_state.query = questions

if 'query' in st.session_state:
    questions = st.session_state.query
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

for message in st.session_state.chat_history:
    role_class = 'assistant' if message['role'] == 'assistant' else 'user'
    with st.chat_message(message['role']):
        st.markdown(f"<div class='stChatMessage {role_class}'>{message['text']}</div>", unsafe_allow_html=True)

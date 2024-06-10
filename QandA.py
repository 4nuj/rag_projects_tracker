import boto3
import streamlit as st

# Add the logo image
st.image("./Howden-Pride-Logo_PNG-2024_1.png", width=300)  # Adjust the width as needed
icon_url = "./Howden-Pride-Logo_PNG-2024_1.png"  # Adjust this path as needed

st.subheader('M & A Projects Tracker', divider='rainbow')

if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

if 'chat_started' not in st.session_state:
    st.session_state.chat_started = False

for message in st.session_state.chat_history:
    with st.chat_message(message['role']):
        st.markdown(message['text'])

bedrockClient = boto3.client('bedrock-agent-runtime', 'eu-west-3')

def getAnswers(questions):
    knowledgeBaseResponse  = bedrockClient.retrieve_and_generate(
        input={'text': questions},
        retrieveAndGenerateConfiguration={
            'knowledgeBaseConfiguration': {
                'knowledgeBaseId': 'UCVNLTOZKW',
                'modelArn': 'arn:aws:bedrock:eu-west-3::foundation-model/anthropic.claude-3-haiku-20240307-v1:0'
            },
            'type': 'KNOWLEDGE_BASE'
        })
    return knowledgeBaseResponse

def list_s3_documents(bucket_name):
    s3_client = boto3.client('s3')
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

bucket_name = 'projectstracker'
documents = list_s3_documents(bucket_name)

st.sidebar.title("Project List")
for doc in documents:
    st.sidebar.write(f"{doc['company']} - {doc['city']}")

questions = st.chat_input('Enter your questions here...')

# Show sample queries only if the chat has not started
if not st.session_state.chat_started:
    st.markdown("### Sample Queries")
    sample_queries = [
        "Who was the architect on Berlin project?",
        "What technologies were used in Mumbai project?",
        "What were the key dates for Tokyo project?"
    ]

    for query in sample_queries:
        if st.button(query):
            questions = query
            st.session_state.query_submitted = True

if questions:
    st.session_state.chat_started = True  # Set chat started flag
    with st.chat_message('user'):
        st.markdown(questions)
    st.session_state.chat_history.append({"role": 'user', "text": questions})

    response = getAnswers(questions)
    answer = response['output']['text']

    with st.chat_message('assistant'):
        st.markdown(answer)
    st.session_state.chat_history.append({"role": 'assistant', "text": answer})

    if len(response['citations'][0]['retrievedReferences']) != 0:
        # context = response['citations'][0]['retrievedReferences'][0]['content']['text']
        doc_url = response['citations'][0]['retrievedReferences'][0]['location']['s3Location']['uri']

        # Show the context and the document source for the latest Question Answer
        # st.markdown(f"<span style='color:#FFDA33'>Context used: </span>{context}", unsafe_allow_html=True)
        st.markdown(f"<span style='color:#FFDA33'>Source Document: </span>{doc_url}", unsafe_allow_html=True)

    else:
        st.markdown(f"<span style='color:red'>No Context</span>", unsafe_allow_html=True)

for message in st.session_state.chat_history:
    role_class = 'assistant' if message['role'] == 'assistant' else 'user'

    with st.chat_message(message['role']):
        st.markdown(f"<div class='stChatMessage {role_class}'>{message['text']}</div>", unsafe_allow_html=True)

# CSS for custom styling
st.markdown(
    f"""
    <style>
    .sidebar .sidebar-content {{
        background-color: #2E2E2E;
        color: white;
    }}
    .stButton>button {{
        width: 100%;
        border-radius: 15px;
        background-color: #007BFF;
        color: white;
        font-size: 14px;
        padding: 8px;
    }}
    .stButton>button:hover {{
        background-color: #0056b3;
        color: white;
    }}
    .stTextInput>div>div>input {{
        font-size: 18px;
        border-radius: 15px;
        padding: 10px;
    }}
    .stChatMessage {{
        border-radius: 15px;
        padding: 10px;
        margin: 5px 0;
    }}
    .assistant {{
        background-color: #F8F9FA;
        display: flex;
        align-items: center;
    }}
    .user {{
        background-color: #DCF8C6;
        display: flex;
        align-items: center;
    }}
    .assistant:before, .user:before {{
        content: url({icon_url});
        display: inline-block;
        width: 30px;
        height: 30px;
        margin-right: 10px;
    }}
    .highlight {{
        color: #FFDA33;
    }}
    .error {{
        color: red;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

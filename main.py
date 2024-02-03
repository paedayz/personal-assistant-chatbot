from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.vectorstores import Pinecone
from langchain_openai import OpenAIEmbeddings
from langchain.chains.question_answering import load_qa_chain
from langchain_community.chat_models import ChatOpenAI
from langchain.docstore.document import Document
import pinecone

import os
from dotenv import load_dotenv
load_dotenv()

app = FastAPI()

CHANNEL_ACCESS_TOKEN = os.getenv('CHANNEL_ACCESS_TOKEN')
CHANNEL_SECRET = os.getenv('CHANNEL_SECRET')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# initial pinecone
pinecone.init(
    api_key=os.getenv("PINECONE_API_KEY"),  # find at app.pinecone.io
    environment=os.getenv("PINECONE_ENV"),  # next to api key in console
)

# initial llm and chain
llm = ChatOpenAI(openai_api_key=OPENAI_API_KEY, model_name="gpt-3.5-turbo")
chain = load_qa_chain(llm, chain_type="stuff")

# inital linebot API
line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

@app.get("/health")
async def healthCheck(request: Request):
    return JSONResponse(content={"status": "OK"})

@app.post("/webhook")
async def webhook(request: Request):
    signature = request.headers.get("X-Line-Signature")

    # Get the request body as text
    body = await request.body()

    try:
        handler.handle(body.decode(), signature)
    except InvalidSignatureError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    return JSONResponse(content={"success": True})


@handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event):
    text = event.message.text
    
    documents = [Document(page_content=text)]
    text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
    docs = text_splitter.split_documents(documents)

    embeddings = OpenAIEmbeddings()

    index_name = "personal-cb"
    
    docsearch = Pinecone.from_documents(docs, embeddings, index_name=index_name)

    result_docs_search = docsearch.similarity_search(text)

    response = chain.run(input_documents=result_docs_search, question=text)
    reply_text = response

    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))

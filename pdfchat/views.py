from django.conf import settings as conf_settings
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout, login, authenticate
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
from .models import Document, Activity, ChatHistory, Chat
from django.db.models import Q
from .activity import *
# from .forms import DocumentForm
import json
from os import environ
import openai
from datetime import datetime
from django.views.decorators.csrf import csrf_exempt

from langchain.vectorstores import Pinecone
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import UnstructuredPDFLoader, OnlinePDFLoader
import pinecone
from langchain.llms import OpenAI
from langchain.chains.question_answering import load_qa_chain

User = get_user_model()

OPENAI_API_KEY = environ.get("OPENAI_API_KEY")
PINECONE_API_KEY = environ.get("PINECONE_API_KEY")
PINECONE_ENVIRONMENT = environ.get("PINECONE_ENVIRONMENT")
INDEX_NAME = environ.get("INDEX_NAME")
openai.api_key = OPENAI_API_KEY

embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
pinecone.init(
    api_key=PINECONE_API_KEY,
    environment=PINECONE_ENVIRONMENT
)
index_name = INDEX_NAME
docsearch = Pinecone.from_existing_index(index_name, embeddings)
llm = OpenAI(temperature=0.0, openai_api_key=OPENAI_API_KEY)
chain = load_qa_chain(llm, chain_type='stuff')


def login_view(request):
    error_message = ""
    if request.method == 'POST':
        username = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(username=username, password=password)
        if user:
            login(request, user)
            # replace home with your app's home page url
            return redirect('/', {'username': username})
        else:
            error_message = "Invalid username or password"

    return render(request, 'login.html', {'error_message': error_message})


def register_view(request):
    return render(request, 'register.html')


def register(request):
    if request.method == 'POST':
        first_name = request.POST.get('firstname')
        last_name = request.POST.get('lastname')
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = User.objects.create_user(
            first_name = first_name, last_name = last_name,
            username=email, password=password, email=email, is_staff=False)
        try:
            user.save()
            user = authenticate(username=email, password=password)
            if user is not None:
                login(request, user)
                return redirect('/', {'username': email})
        except:
            return render(request, 'register.html', {'error_message':'Error occurred!'})
    return render(request, 'register.html')


def sign_out(request):
    logout(request)
    return redirect('/login')


@login_required
def index(request):
    activities = Activity.objects.order_by('-created_at')[:3]
    return render(request, 'index.html', {'activities':activities})


@login_required
def clients(request):
    clients = User.objects.all()
    return render(request, 'clients.html', {'clients': clients})


@login_required
def library(request):
    documents = Document.objects.all()
    return render(request, 'library.html', {'documents': documents})


@login_required
def upload_view(request):
    activities = Activity.objects.order_by('-created_at')[:3]
    return render(request, 'upload.html', {'activities': activities})


@login_required
def upload(request):
    message = ""
    if request.method == 'POST':
        uploaded_file = request.FILES['document']
        name = uploaded_file.name
        try:
            document = Document()
            document.user = User.objects.get(id=request.user.id)
            document.category = request.POST['category']
            document.name = name
            document.page = request.POST['page']
            document.file = uploaded_file
            document.description = request.POST['description']
            document.save()

            # upload to pinecone
            print("=======================File saved before pinecone")

            upload_to_pinecone(document.file.url)
            message = 'Uploaded successfully!'

            activity = Activity()
            activity.user = User.objects.get(id=request.user.id)
            activity.activity = UPLOADED_DOCUMENT
            activity.type = 1
            activity.save()
        except Exception as e:
            message = 'Error occurred.'

    activities = Activity.objects.order_by('-created_at')[:3]
    return render(request, 'upload.html', {'message': message, 'activities': activities})

@login_required
def clientsuccess(request):
    return render(request, 'clientsuccess.html', {'chats': []})

@login_required
def cpa(request):
    return render(request, 'cpa.html', {'chats': []})

@login_required
def legal(request):
    return render(request, 'legal.html', {'chats': []})

@login_required
def hr(request):
    return render(request, 'hr.html', {'chats': []})

@login_required
def prompts(request):
    return render(request, 'prompts.html')


@login_required
def settings(request):
    return render(request, 'settings.html')


@login_required
def help(request):
    return render(request, 'help.html')


@login_required
def contact(request):
    return render(request, 'contact.html')


@login_required
def get_percentage(request):
    value, total_count = Document.get_counts()
    try:
        value = value[0]
        cpa = len(Document.objects.filter(category='CPA'))
        hr = len(Document.objects.filter(category='HR'))
        legal = len(Document.objects.filter(category='Legal'))
    except:
        cpa = 0
        hr = 0
        legal = 0
    return HttpResponse(json.dumps({
        'cpa': cpa,
        'hr': hr,
        'legal': legal,
        'total': total_count
    }), content_type='application/json')


# History
@login_required
def get_history(request):
    category = request.POST['category']
    chat_histories = ChatHistory.objects.filter(
        user=request.user.id, chat_category=category).order_by('-created_at')
    result = []
    for chat in chat_histories:
        result.append(chat.name)
    return HttpResponse(
        json.dumps(result),
        content_type="application/json"
    )



@login_required
def create_history(request):
    category = request.POST['category']
    name = request.POST['history']

    history = ChatHistory()
    history.user = User.objects.get(id=request.user.id)
    history.chat_category = category
    history.name = name
    history.save()

    activity = Activity()
    activity.user = User.objects.get(id=request.user.id)
    activity.activity = CREATED_CHAT
    activity.type = 2
    activity.save()

    return HttpResponse("Success")


@login_required
def delete_history(request):
    category = request.POST['category']
    history = request.POST['history']
    chat_history = ChatHistory.objects.filter(name=history, chat_category=category, user=request.user.id)
    chat_history.delete()

    chat = Chat.objects.filter(chat_history=history, chat_category=category, user=request.user.id)
    chat.delete()

    activity = Activity()
    activity.user = User.objects.get(id=request.user.id)
    activity.activity = DELETED_CHAT
    activity.type = 3
    activity.save()
    return HttpResponse("Success")


@login_required
def get_chat(request):
    # category = request.POST['category']
    # history = request.POST['history']
    chats = Chat.objects.filter(
        user=request.user.id)
        # user=request.user.id, chat_history=history, chat_category=category)
    result = []
    for chat in chats:
        result.append([chat.message, chat.response])

    return HttpResponse(
        json.dumps(result),
        content_type="application/json"
    )

@csrf_exempt
@login_required
def chat(request):
    try:
        category = 'CPA'
        # history = request.POST['history']
        prompt = request.POST['prompt']

        chat = Chat()
        chat.user = User.objects.get(id=request.user.id)
        chat.chat_history = "history"
        chat.chat_category = "category"
        chat.message = prompt
        chat.sent = datetime.now()

        # ===== Normal Chatbot =====
        messages = []
        messages.append(
            {"role": "user", "content": "Your name is Copilot. You are a helpful assistant for CPA, Legal and HR."})

        question = {}
        question['role'] = 'user'
        question['content'] = prompt
        messages.append(question)
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo", messages=messages)
            response = response['choices'][0]['message']['content']
            chat.response = response
            chat.received = datetime.now()
            chat.save()
        except Exception as e:
            print("except", e)
            response = "Sorry, try again in a few minutes."
        # if category == 'CPA':
        #     context = """You are an Accounting Assistant chatbot specifically designed to serve Certified Public Accountants (CPAs) and accountants. 
        #     Your purpose is to provide accurate and helpful information related to accounting topics, including but not limited to 
        #     taxation, financial reporting, audit and assurance, management accounting, financial analysis, and regulatory compliance. 
        #     You should only answer questions and provide guidance within the scope of accounting and CPA-related matters. 
        #     Your responses should be based on the latest accounting principles, standards, and regulations applicable in the given context. 
        #     Please note that you are not providing professional advice but rather general guidance to help accountants and CPAs with their queries."""
        # elif category == 'Legal':
        #     context = """You are a Legal Assistant chatbot specifically designed to serve lawyers and legal professionals. 
        #     Your purpose is to provide accurate and helpful information related to legal matters and law firm operations,
        #     including but not limited to contract law, civil litigation, criminal law, family law, intellectual property, 
        #     employment law, and more. You should only answer questions and provide guidance within the scope of legal matters
        #     and law firm-related topics. Your responses should be based on the general principles and regulations applicable in 
        #     the given context. Please note that you are not providing legal advice but rather general guidance to help lawyers 
        #     and legal professionals with their queries."""
        # else:
        #     context = """ChatGPT, you are an AI-powered HR Assistant designed to help Human Resource professionals with their 
        #     tasks and responsibilities. Your expertise is focused on topics related to Human Resources, including recruitment, 
        #     onboarding, employee relations, training and development, performance management, compensation and benefits, labor laws,
        #     workplace policies, diversity and inclusion, and employee engagement. You should provide relevant and accurate information, 
        #     best practices, and guidance on any HR-related topic, while keeping in mind that your responses should not be considered professional legal advice."""
        
        # pdf chat
        # docs = docsearch.similarity_search(prompt, include_metadata=True)
        # response = chain.run(input_documents=docs, question=prompt + context)
        # chat.response = response
        # chat.received = datetime.now()
        # chat.save()
    except:
        response = "Sorry went wrong. Try again in a few minutes!"

    return HttpResponse(response)


def upload_to_pinecone(filepath):
    
    # loader = UnstructuredPDFLoader(filepath)
    print("=======================before reaing files")
    loader = OnlinePDFLoader(filepath)
    data = loader.load()
    print(f'Loaded {len(data)} page(s) from {filepath}')
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000, chunk_overlap=0)
    texts = text_splitter.split_documents(data)
    Pinecone.from_texts([t.page_content for t in texts],
                        embeddings, index_name=index_name)

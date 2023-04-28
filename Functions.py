# This Python file uses the following encoding: utf-8
from pathlib import Path
import pytesseract
from PIL import Image
import PyPDF2
from pdf2image import convert_from_path
import os
import sqlite3

# from gtts import gTTS
import pyttsx3
engine = pyttsx3.init()
rate = engine.getProperty('rate')   # getting details of current speaking rate
engine.setProperty('rate', 160)     # setting up new voice rate
voices = engine.getProperty('voices')       #getting details of current voice
engine.setProperty('voice', voices[1].id)   #changing index, changes voices. 1 for female

#Summarizer
import spacy
from spacy.lang.en.stop_words import STOP_WORDS
from string import punctuation
stopwords = list(STOP_WORDS)
nlp = spacy.load('en_core_web_sm')


# Paths 
path_tesseract = "Tesseract-OCR\\tesseract.exe"
path_poppler = r'poppler-0.68.0\bin'


# Function to connect to database
def cn():
    conn = sqlite3.connect('DATABASE.sqlite3')
    return conn

# Creating initial database
def create_null_db(): 
    conn = cn()
    conn.execute('''create table if not exists book(
        id integer primary key,
        file_type text,
        file_name text,
        total_pgs integer,
        page_no integer,
        img_path text,
        text_path text,
        audio_path text,
        summary_path text,
        summary_audio_path text
        );
                    ''')
    conn.execute('''CREATE TABLE IF NOT EXISTS other(
        id integer primary key,
        counter integer,
        password text
        );
                    ''')
    conn.commit()
    initialize_counter()


def initialize_counter():
    conn = cn()
    query = "INSERT INTO other(id,counter) VALUES(1,1);"
    conn.execute(query)
    conn.commit()


def get_counter():
    conn =cn()
    query = "select counter from other;"
    for i in conn.execute(query): return i[0]


def set_counter(val):
    conn=cn()
    query = "update other set counter = ? where id==1;"
    conn.execute(query,(val,))
    conn.commit()


def increment_counter():
    set_counter(get_counter()+1)


# database insert function to take entries
def fill_row(id,type,name,pg,no=None,img=None,txt=None,aud=None,summary=None,summaryaudio=None):
    conn = cn()
    query = "insert into book(id,file_type,file_name,total_pgs,page_no,img_path,text_path,audio_path,summary_path,summary_audio_path) values(?,?,?,?,?,?,?,?,?,?);"
    conn.execute(query,(id,type,name,pg,no,img,txt,aud,summary,summaryaudio,))
    conn.commit()

# ----------------------------------------------------------------------------------
# PDF TO TEXT TO AUDIO + DB operations
def pdf2img2txt2aud(pdf_path):         # Dont change the name of path as function are 
    pdf_name = pdf_path[21:-4]         # made according to len of path as here [21:-4]
    full_text = ""       

    images = convert_from_path(pdf_path, poppler_path = path_poppler)
    pytesseract.pytesseract.tesseract_cmd = path_tesseract

    no_img = len(images)

    for i in range(no_img):
        counter = get_counter()

        # Save pages as images in the pdf
        img_path = 'static\\Resources\\IMG\\'+pdf_name+'-'+str(i)+'.jpg'
        images[i].save(img_path,'JPEG')

        img = Image.open(img_path)

        full_text += "\n"
        res = pytesseract.image_to_string(img)              # for english
        #res = pytesseract.image_to_string(img, lang="hin") # for hindi
        full_text += res

        text_path = 'static\\Resources\\TEXT\\'+pdf_name+'-'+str(i)+'.txt'
        with Path(text_path).open('w', encoding = 'utf-8') as op_file:
            op_file.write(res)

        fill_row(counter,"PDF",pdf_name,no_img,i+1,img_path,text_path)
        increment_counter()
        

    full_text_path = 'static\\Resources\\TEXT\\'+pdf_name+'.txt'
    with Path(full_text_path).open('w', encoding = 'utf-8') as op_file:
        op_file.write(full_text)

    try:
        audio_path = 'static\\Resources\\AUDIO\\'+pdf_name+'.mp3'
        engine.save_to_file(full_text , audio_path)
        engine.runAndWait()
    except Exception as e:
        audio_path=""
        print("\n\n Error is due to :\n\n",e,"\n\n")

    counter = get_counter()
    fill_row(id=counter,type='PDF',name=pdf_name,no=0,pg=no_img,txt=full_text_path,aud=audio_path)
    increment_counter()

    return full_text

# -----------------------------------------------------------------------------
# Optimised PDF to Text To Audio + DB Operations

def pdf2img2txt2aud_optimised(pdf_path):

    list_no_of_pg_having_img = []
    # Open the PDF file
    pdf_file = open(pdf_path, 'rb')
    # Create a PDF reader object
    pdf_reader = PyPDF2.PdfFileReader(pdf_file)
    #Total no of pages
    total_pg = pdf_reader.numPages
    # Loop through each page in the PDF file
    for page_num in range(total_pg):
        # Get the page object
        page_obj = pdf_reader.getPage(page_num)
        # Check if the page contains any images
        if '/XObject' in page_obj['/Resources']:
            xobj = page_obj['/Resources']['/XObject'].getObject()
            for obj in xobj:
                # Check if the object is an image
                if xobj[obj]['/Subtype'] == '/Image':
                    print('Page %s contains an image.' % (page_num + 1))
                    list_no_of_pg_having_img.append(page_num)
                    break


    pdf_name = pdf_path[21:-4]
    full_text = ""       

    pytesseract.pytesseract.tesseract_cmd = path_tesseract

    for i in range(total_pg):
        counter = get_counter()

        if i in list_no_of_pg_having_img:
            # Save pages as images in the pdf
            img_path = 'static\\Resources\\IMG\\'+pdf_name+'-'+str(i+1)+'.jpg'
            convert_from_path(pdf_path=pdf_path,poppler_path=path_poppler,first_page=i+1,last_page=i+1)[0].save(img_path)
            img = Image.open(img_path)

            full_text += "\n"
            res = pytesseract.image_to_string(img)              # for english
            #res = pytesseract.image_to_string(img, lang="hin") # for hindi
            full_text += res

            text_path = 'static\\Resources\\TEXT\\'+pdf_name+'-'+str(i)+'.txt'
            with Path(text_path).open('w', encoding = 'utf-8') as op_file:
                op_file.write(res)
            
            fill_row(counter,"PDF",pdf_name,total_pg,i+1,img_path,text_path)
            increment_counter()
        
        else:
            res = pdf_reader.pages[i].extract_text()
            full_text += res

            text_path = 'static\\Resources\\TEXT\\'+pdf_name+'-'+str(i)+'.txt'
            with Path(text_path).open('w', encoding = 'utf-8') as op_file:
                op_file.write(res)
            img_path=None
            fill_row(counter,"PDF",pdf_name,total_pg,i+1,img_path,text_path)
            increment_counter()

    full_text_path = 'static\\Resources\\TEXT\\'+pdf_name+'.txt'
    with Path(full_text_path).open('w', encoding = 'utf-8') as op_file:
        op_file.write(full_text)

    try:
        audio_path = 'static\\Resources\\AUDIO\\'+pdf_name+'.mp3'
        engine.save_to_file(full_text , audio_path)
        engine.runAndWait()
    except Exception as e:
        audio_path=""
        print("\n\n Error is due to :\n\n",e,"\n\n")

    counter = get_counter()
    # fill_row(counter,"PDF",pdf_name,no_img,0,'',full_text_path,audio_path)
    fill_row(id=counter,type='PDF',name=pdf_name,no=0,pg=total_pg,txt=full_text_path,aud=audio_path)
    increment_counter()

    return full_text

# ------------------------------------------------------------------------------------
# PDF TO TEXT
def pdf2img2txt(pdf_path):
                # Dont change the name of path as function are 
                # made according to len of path as here [21:-4]
    pdf_name = pdf_path[21:-4]
    full_text = ""       

    images = convert_from_path(pdf_path, poppler_path = path_poppler)
    pytesseract.pytesseract.tesseract_cmd = path_tesseract

    no_img = len(images)

    for i in range(no_img):
        counter = get_counter()

        # Save pages as images in the pdf
        img_path = 'static\\Resources\\IMG\\'+pdf_name+'-'+str(i)+'.jpg'
        images[i].save(img_path,'JPEG')

        img = Image.open(img_path)

        full_text += "\n"
        res = pytesseract.image_to_string(img)              # for english
        #res = pytesseract.image_to_string(img, lang="hin") # for hindi
        full_text += res

        text_path = 'static\\Resources\\TEXT\\'+pdf_name+'-'+str(i)+'.txt'
        with Path(text_path).open('w', encoding = 'utf-8') as op_file:
            op_file.write(res)

        fill_row(counter,"PDF",pdf_name,no_img,i+1,img_path,text_path)
        increment_counter()

    full_text_path = 'static\\Resources\\TEXT\\'+pdf_name+'.txt'
    with Path(full_text_path).open('w', encoding = 'utf-8') as op_file:
        op_file.write(full_text)

    counter = get_counter()
    fill_row(id=counter,type='PDF',name=pdf_name,no=0,pg=no_img,txt=full_text_path)
    increment_counter()

    return full_text

#-------------------------------------------------------------------------------------------
# OPTIMISED PDF TO TEXT +DB OPERATIONS

def pdf2img2txt_optimised(pdf_path):

    list_no_of_pg_having_img = []
    # Open the PDF file
    pdf_file = open(pdf_path, 'rb')
    # Create a PDF reader object
    pdf_reader = PyPDF2.PdfFileReader(pdf_file)
    #Total no of pages
    total_pg = pdf_reader.numPages
    # Loop through each page in the PDF file
    for page_num in range(total_pg):
        # Get the page object
        page_obj = pdf_reader.getPage(page_num)
        # Check if the page contains any images
        if '/XObject' in page_obj['/Resources']:
            xobj = page_obj['/Resources']['/XObject'].getObject()
            for obj in xobj:
                # Check if the object is an image
                if xobj[obj]['/Subtype'] == '/Image':
                    print('Page %s contains an image.' % (page_num + 1))
                    list_no_of_pg_having_img.append(page_num)
                    break


    pdf_name = pdf_path[21:-4]
    full_text = ""       

    pytesseract.pytesseract.tesseract_cmd = path_tesseract

    for i in range(total_pg):
        counter = get_counter()

        if i in list_no_of_pg_having_img:
            # Save pages as images in the pdf
            img_path = 'static\\Resources\\IMG\\'+pdf_name+'-'+str(i+1)+'.jpg'
            convert_from_path(pdf_path=pdf_path,poppler_path=path_poppler,first_page=i+1,last_page=i+1)[0].save(img_path)
            img = Image.open(img_path)

            full_text += "\n"
            res = pytesseract.image_to_string(img)              # for english
            #res = pytesseract.image_to_string(img, lang="hin") # for hindi
            full_text += res

            text_path = 'static\\Resources\\TEXT\\'+pdf_name+'-'+str(i)+'.txt'
            with Path(text_path).open('w', encoding = 'utf-8') as op_file:
                op_file.write(res)
            
            fill_row(counter,"PDF",pdf_name,total_pg,i+1,img_path,text_path)
            increment_counter()
        
        else:
            res = pdf_reader.pages[i].extract_text()
            full_text += res

            text_path = 'static\\Resources\\TEXT\\'+pdf_name+'-'+str(i)+'.txt'
            with Path(text_path).open('w', encoding = 'utf-8') as op_file:
                op_file.write(res)
            img_path=None
            fill_row(counter,"PDF",pdf_name,total_pg,i+1,img_path,text_path)
            increment_counter()

    full_text_path = 'static\\Resources\\TEXT\\'+pdf_name+'.txt'
    with Path(full_text_path).open('w', encoding = 'utf-8') as op_file:
        op_file.write(full_text)
    
    counter = get_counter()
    fill_row(id=counter,type='PDF',name=pdf_name,no=0,pg=total_pg,txt=full_text_path)
    increment_counter()

    # Close the PDF file
    pdf_file.close()
    return full_text


#-------------------------------------------------------------------------------------------
# code to show_img (not called in app.py)
def pdf2img(pdf_path):
                # Dont change the name of path as function are 
                # made according to len of path as here [21:-4]
    pdf_name = pdf_path[21:-4]
    full_text = ""       

    images = convert_from_path(pdf_path, poppler_path = path_poppler)
    no_img = len(images)

    for i in range(no_img):
        counter = get_counter()

        # Save pages as images in the pdf
        img_path = 'static\\Resources\\IMG\\'+pdf_name+'-'+str(i)+'.jpg'
        images[i].save(img_path,'JPEG')


        fill_row(counter,"PDF",pdf_name,no_img,i+1,img_path)
        increment_counter()

#-------------------------------------------------------------------------------------------
# code of extractive summarizer

def extractive_summarizer(text):
    from string import punctuation
    doc = nlp(text)

    tokens = [token.text for token in doc]

    punctuation = punctuation + '\n'

    word_frequencies = {}
    for word in doc:
        if word.text.lower() not in stopwords:
            if word.text.lower() not in punctuation:
                if word.text not in word_frequencies.keys():
                    word_frequencies[word.text] = 1
                else:
                    word_frequencies[word.text] += 1
                    
    max_frequency = max(word_frequencies.values())

    for word in word_frequencies.keys():
        word_frequencies[word] = word_frequencies[word]/max_frequency

    sentence_tokens = [sent for sent in doc.sents]

    sentence_scores = {}
    for sent in sentence_tokens:
        for word in sent:
            if word.text.lower() in word_frequencies.keys():
                if sent not in sentence_scores.keys():
                    sentence_scores[sent] = word_frequencies[word.text.lower()]
                else:
                    sentence_scores[sent] += word_frequencies[word.text.lower()]
    from heapq import nlargest
    select_length = int(len(sentence_tokens)*0.3)
    summary = nlargest(select_length, sentence_scores, key = sentence_scores.get)
    final_summary = [word.text for word in summary]
    summary = ' '.join(final_summary)
    return summary


#-------------------------------------------------------------------------------------------
# PDF TO TEXT TO SUMMARY + DB OPERATION

def pdf2img2txt2summary(pdf_path):

    pdf_name = pdf_path[21:-4]
    full_text = ""       

    images = convert_from_path(pdf_path, poppler_path = path_poppler)
    pytesseract.pytesseract.tesseract_cmd = path_tesseract

    no_img = len(images)

    for i in range(no_img):
        counter = get_counter()

        # Save pages as images in the pdf
        img_path = 'static\\Resources\\IMG\\'+pdf_name+'-'+str(i)+'.jpg'
        images[i].save(img_path,'JPEG')

        img = Image.open(img_path)

        full_text += "\n"
        res = pytesseract.image_to_string(img)              # for english
        #res = pytesseract.image_to_string(img, lang="hin") # for hindi
        full_text += res

        text_path = 'static\\Resources\\TEXT\\'+pdf_name+'-'+str(i)+'.txt'
        with Path(text_path).open('w', encoding = 'utf-8') as op_file:
            op_file.write(res)

        fill_row(counter,"PDF",pdf_name,no_img,i+1,img_path,text_path)
        increment_counter()
        
    full_text_path = 'static\\Resources\\TEXT\\'+pdf_name+'.txt'
    with Path(full_text_path).open('w', encoding = 'utf-8') as op_file:
        op_file.write(full_text)

    summary = extractive_summarizer(full_text)
    summary_path = 'static\\Resources\\SUMMARY\\'+pdf_name+'.txt'
    with Path(summary_path).open('w', encoding = 'utf-8') as op_file:
        op_file.write(summary)

    counter = get_counter()
    fill_row(id=counter,type='PDF',name=pdf_name,pg=no_img,no=0,txt=full_text_path,summary=summary_path)
    increment_counter()

    return summary


#-------------------------------------------------------------------------------------
# OPTIMISED PDF TO TEXT TO SUMMARY

def pdf2img2txt2summary_optimised(pdf_path):

    list_no_of_pg_having_img = []
    # Open the PDF file
    pdf_file = open(pdf_path, 'rb')
    # Create a PDF reader object
    pdf_reader = PyPDF2.PdfFileReader(pdf_file)
    #Total no of pages
    total_pg = pdf_reader.numPages
    # Loop through each page in the PDF file
    for page_num in range(total_pg):
        # Get the page object
        page_obj = pdf_reader.getPage(page_num)
        # Check if the page contains any images
        if '/XObject' in page_obj['/Resources']:
            xobj = page_obj['/Resources']['/XObject'].getObject()
            for obj in xobj:
                # Check if the object is an image
                if xobj[obj]['/Subtype'] == '/Image':
                    print('Page %s contains an image.' % (page_num + 1))
                    list_no_of_pg_having_img.append(page_num)
                    break


    pdf_name = pdf_path[21:-4]
    full_text = ""       

    pytesseract.pytesseract.tesseract_cmd = path_tesseract

    for i in range(total_pg):
        counter = get_counter()

        if i in list_no_of_pg_having_img:
            # Save pages as images in the pdf
            img_path = 'static\\Resources\\IMG\\'+pdf_name+'-'+str(i+1)+'.jpg'
            convert_from_path(pdf_path=pdf_path,poppler_path=path_poppler,first_page=i+1,last_page=i+1)[0].save(img_path)
            img = Image.open(img_path)

            full_text += "\n"
            res = pytesseract.image_to_string(img)              # for english
            #res = pytesseract.image_to_string(img, lang="hin") # for hindi
            full_text += res

            text_path = 'static\\Resources\\TEXT\\'+pdf_name+'-'+str(i)+'.txt'
            with Path(text_path).open('w', encoding = 'utf-8') as op_file:
                op_file.write(res)
            
            fill_row(counter,"PDF",pdf_name,total_pg,i+1,img_path,text_path)
            increment_counter()
        
        else:
            res = pdf_reader.pages[i].extract_text()
            full_text += res

            text_path = 'static\\Resources\\TEXT\\'+pdf_name+'-'+str(i)+'.txt'
            with Path(text_path).open('w', encoding = 'utf-8') as op_file:
                op_file.write(res)
            img_path=None
            fill_row(counter,"PDF",pdf_name,total_pg,i+1,img_path,text_path)
            increment_counter()

    full_text_path = 'static\\Resources\\TEXT\\'+pdf_name+'.txt'
    with Path(full_text_path).open('w', encoding = 'utf-8') as op_file:
        op_file.write(full_text)

    pdf_file.close()

    summary = extractive_summarizer(full_text)
    summary_path = 'static\\Resources\\SUMMARY\\'+pdf_name+'.txt'
    with Path(summary_path).open('w', encoding = 'utf-8') as op_file:
        op_file.write(summary)

    counter = get_counter()
    fill_row(id=counter,type='PDF',name=pdf_name,pg=total_pg,no=0,txt=full_text_path,summary=summary_path)
    increment_counter()

    return summary


# -------------------------------------------------------------------------------------------------
# PDF TO TEXT TO SUMMARY TO AUDIO +DB OPERATION

def pdf2img2txt2summary2aud(pdf_path):

    pdf_name = pdf_path[21:-4]
    full_text = ""       

    images = convert_from_path(pdf_path, poppler_path = path_poppler)
    pytesseract.pytesseract.tesseract_cmd = path_tesseract

    no_img = len(images)

    for i in range(no_img):
        counter = get_counter()

        # Save pages as images in the pdf
        img_path = 'static\\Resources\\IMG\\'+pdf_name+'-'+str(i)+'.jpg'
        images[i].save(img_path,'JPEG')

        img = Image.open(img_path)

        full_text += "\n"
        res = pytesseract.image_to_string(img)              # for english
        #res = pytesseract.image_to_string(img, lang="hin") # for hindi
        full_text += res

        text_path = 'static\\Resources\\TEXT\\'+pdf_name+'-'+str(i)+'.txt'
        with Path(text_path).open('w', encoding = 'utf-8') as op_file:
            op_file.write(res)

        fill_row(counter,"PDF",pdf_name,no_img,i+1,img_path,text_path)
        increment_counter()

    full_text_path = 'static\\Resources\\TEXT\\'+pdf_name+'.txt'
    with Path(full_text_path).open('w', encoding = 'utf-8') as op_file:
        op_file.write(full_text)

    summary = extractive_summarizer(full_text)
    summary_path = 'static\\Resources\\SUMMARY\\'+pdf_name+'.txt'
    with Path(summary_path).open('w', encoding = 'utf-8') as op_file:
        op_file.write(summary)

    try:
        summary_audio_path = 'static\\Resources\\AUDIO\\'+pdf_name+'_Summary.mp3'
        engine.save_to_file(summary , summary_audio_path)
        engine.runAndWait()
    except Exception as e:
        summary_audio_path=""
        print("\n\n Error is due to :\n\n",e,"\n\n")

    counter = get_counter()
    fill_row(id=counter,type='PDF',name=pdf_name,pg=no_img,no=0,txt=full_text_path,summary=summary_path,summaryaudio=summary_audio_path)
    increment_counter()

    return summary

#--------------------------------------------------------------------------------------------
# OPTIMISED PDF TO TEXT TO SUMMARY TO AUDIO + DB OPERATION

def pdf2img2txt2summary2aud_optimised(pdf_path):

    list_no_of_pg_having_img = []
    # Open the PDF file
    pdf_file = open(pdf_path, 'rb')
    # Create a PDF reader object
    pdf_reader = PyPDF2.PdfFileReader(pdf_file)
    #Total no of pages
    total_pg = pdf_reader.numPages
    # Loop through each page in the PDF file
    for page_num in range(total_pg):
        # Get the page object
        page_obj = pdf_reader.getPage(page_num)
        # Check if the page contains any images
        if '/XObject' in page_obj['/Resources']:
            xobj = page_obj['/Resources']['/XObject'].getObject()
            for obj in xobj:
                # Check if the object is an image
                if xobj[obj]['/Subtype'] == '/Image':
                    print('Page %s contains an image.' % (page_num + 1))
                    list_no_of_pg_having_img.append(page_num)
                    break


    pdf_name = pdf_path[21:-4]
    full_text = ""       

    pytesseract.pytesseract.tesseract_cmd = path_tesseract

    for i in range(total_pg):
        counter = get_counter()

        if i in list_no_of_pg_having_img:
            # Save pages as images in the pdf
            img_path = 'static\\Resources\\IMG\\'+pdf_name+'-'+str(i+1)+'.jpg'
            convert_from_path(pdf_path=pdf_path,poppler_path=path_poppler,first_page=i+1,last_page=i+1)[0].save(img_path)
            img = Image.open(img_path)

            full_text += "\n"
            res = pytesseract.image_to_string(img)              # for english
            #res = pytesseract.image_to_string(img, lang="hin") # for hindi
            full_text += res

            text_path = 'static\\Resources\\TEXT\\'+pdf_name+'-'+str(i)+'.txt'
            with Path(text_path).open('w', encoding = 'utf-8') as op_file:
                op_file.write(res)
            
            fill_row(counter,"PDF",pdf_name,total_pg,i+1,img_path,text_path)
            increment_counter()
        
        else:
            res = pdf_reader.pages[i].extract_text()
            full_text += res

            text_path = 'static\\Resources\\TEXT\\'+pdf_name+'-'+str(i)+'.txt'
            with Path(text_path).open('w', encoding = 'utf-8') as op_file:
                op_file.write(res)
            img_path=None
            fill_row(counter,"PDF",pdf_name,total_pg,i+1,img_path,text_path)
            increment_counter()

    full_text_path = 'static\\Resources\\TEXT\\'+pdf_name+'.txt'
    with Path(full_text_path).open('w', encoding = 'utf-8') as op_file:
        op_file.write(full_text)
    
    pdf_file.close()

    summary = extractive_summarizer(full_text)
    summary_path = 'static\\Resources\\SUMMARY\\'+pdf_name+'.txt'
    with Path(summary_path).open('w', encoding = 'utf-8') as op_file:
        op_file.write(summary)

    try:
        summary_audio_path = 'static\\Resources\\AUDIO\\'+pdf_name+'_Summary.mp3'
        engine.save_to_file(summary , summary_audio_path)
        engine.runAndWait()
    except Exception as e:
        summary_audio_path=""
        print("\n\n Error is due to :\n\n",e,"\n\n")
    
    counter = get_counter()
    fill_row(id=counter,type='PDF',name=pdf_name,pg=total_pg,no=0,txt=full_text_path,summary=summary_path,summaryaudio=summary_audio_path)
    increment_counter()

    return summary

# ---------------------------------------------------------------------------------------------------

def validate_resources_directory():
    try :
        os.mkdir("static\\Resources")
        validate_sub_resources_directory()
    except :
        validate_sub_resources_directory()


def validate_sub_resources_directory(): 
    entries = os.listdir("static\\Resources\\")
    for sub_resource in "IMG",'PDF','TEXT','SUMMARY','AUDIO', "PROCESSED PDF":
        if sub_resource not in entries:
            os.mkdir("static\\Resources\\"+str(sub_resource))

# from crypt import methods
from turtle import heading
from unittest import result
from wsgiref.util import request_uri
from flask import Flask
from flask import render_template, request, redirect
import Functions as fn
import os
import shutil

try :
    fn.validate_resources_directory() # For covinience to create empty directories initially
except Exception as e:
    print(e)
    pass

try :
    fn.create_null_db()
except Exception as e:
    print(e)
    pass


app = Flask(__name__)

# path to save PDF Files
# Add the path of your pdf folder
app.config["PDF_PATH"] = "static\\Resources\\PDF"

# file extension funcyion is not completed yet
app.config["FILE_EXTENSION"] = ["PDF", ]


@app.route('/')
def start():
    return render_template('Index.html')

@app.route('/home', methods=["POST", "GET"])
def home():
    return render_template('home.html') 

@app.route('/upload', methods=["POST", "GET"])
def Home():
    if request.method == "POST":
        if request.files:

            myFile = request.files["myfile"]

            if myFile.filename == "":
                print("Must have filename")
                return render_template('home.html',msg = "Please Choose File !")
            
            elif myFile.filename[-4:] != ".pdf":
                return render_template('home.html', msg = "It is not a PDF file, Choose only PDF file!")
           
            # saving  file to pdf location
            try:
                entries = os.listdir("static\\Resources\\PDF\\")
                for pdf in entries:
                    os.remove("static\\Resources\\PDF\\"+str(pdf))
            except:
                pass

            myFile.save(os.path.join(app.config["PDF_PATH"], myFile.filename))

            global pdfname
            pdfname = myFile.filename

            global pdf_path
            pdf_path = "static\\Resources\\PDF\\"+str(pdfname)

            print("File uploaded sucessfully...")
            return redirect(request.url)

    return render_template('upload.html',pdf_name=pdfname)


@app.route('/upload/show_text', methods=['POST'])
def show_text():
    try :
        res = fn.pdf2img2txt_optimised(pdf_path)
        try:
            shutil.move(pdf_path,"static\\Resources\\PROCESSED PDF")
        except:
            pass
        return render_template('show_text.html', result = res, pdf_name = pdfname)

    except Exception as e:
        return render_template('fileerror.html', msg = "show_text() produced error due to -\n"+str(e))


@app.route('/upload/show_img', methods=['POST'])
def show_img():
    try :
        fn.pdf2img(pdf_path)
        try:
            shutil.move(pdf_path,"static\\Resources\\PROCESSED PDF")
        except:
            pass
        return render_template('show_img.html', pdf_name = pdfname)

    except Exception as e:
        return render_template('fileerror.html', msg = "show_img() produced error due to -\n"+str(e))


@app.route('/upload/play_audio', methods=['POST'])
def play_audio():
    try :
        res = fn.pdf2img2txt2aud_optimised(pdf_path)
        try:
            shutil.move(pdf_path,"static\\Resources\\PROCESSED PDF")
        except:
            pass
        return render_template('play_audio.html', result = res, pdf_name = pdfname, audio_path= "/static/Resources/AUDIO/"+str(pdfname[:-4])+".mp3")

    except Exception as e:
        return render_template('fileerror.html', msg = "play_audio() produced error due to -\n"+str(e))


@app.route('/upload/show_summary', methods=['POST'])
def show_summary():
    try :
        res = fn.pdf2img2txt2summary_optimised(pdf_path)
        try:
            shutil.move(pdf_path,"static\\Resources\\PROCESSED PDF")
        except:
            pass
        return render_template('show_summary.html', result = res, pdf_name = pdfname)

    except Exception as e:
        return render_template('fileerror.html', msg = "show_summary() produced error due to -\n"+str(e))


@app.route('/upload/play_summary', methods=['POST'])
def play_summary():
    try :
        res = fn.pdf2img2txt2summary2aud_optimised(pdf_path)
        try:
            shutil.move(pdf_path,"static\\Resources\\PROCESSED PDF")
        except:
            pass
        return render_template('play_summary.html', result = res, pdf_name = pdfname, audio_path= "/static/Resources/AUDIO/"+str(pdfname[:-4])+"_Summary.mp3")

    except Exception as e:
        return render_template('fileerror.html', msg = "play_audio() produced error due to -\n"+str(e))



if __name__ == '__main__':
    app.run(debug=True)

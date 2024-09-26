import os
import platform
import mutagen
from PIL import Image
from PyPDF2 import PdfFileReader
from docx import Document
from flask import Flask, request, redirect, url_for, render_template, send_from_directory

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def get_basic_metadata(file_path):
    """Get basic metadata for any file."""
    metadata = {}
    metadata['file_name'] = os.path.basename(file_path)
    metadata['file_size'] = os.path.getsize(file_path)
    metadata['file_type'] = os.path.splitext(file_path)[1]
    metadata['location'] = os.path.abspath(file_path)
    metadata['file_source'] = platform.system()

    # Get file creation and modification dates
    if platform.system() == 'Windows':
        metadata['date_created'] = os.path.getctime(file_path)
        metadata['date_modified'] = os.path.getmtime(file_path)
    else:
        stat = os.stat(file_path)
        metadata['date_created'] = stat.st_ctime
        metadata['date_modified'] = stat.st_mtime

    return metadata

def get_image_metadata(file_path):
    """Get metadata for image files."""
    metadata = get_basic_metadata(file_path)
    try:
        with Image.open(file_path) as img:
            metadata['format'] = img.format
            metadata['mode'] = img.mode
            metadata['size'] = img.size
    except Exception as e:
        metadata['error'] = str(e)
    return metadata

def get_audio_metadata(file_path):
    """Get metadata for audio files."""
    metadata = get_basic_metadata(file_path)
    try:
        audio = mutagen.File(file_path, easy=True)
        if audio:
            metadata.update(audio.info.pprint())
    except Exception as e:
        metadata['error'] = str(e)
    return metadata

def get_pdf_metadata(file_path):
    """Get metadata for PDF files."""
    metadata = get_basic_metadata(file_path)
    try:
        with open(file_path, 'rb') as f:
            pdf = PdfFileReader(f)
            doc_info = pdf.getDocumentInfo()
            if doc_info:
                metadata.update({key[1:]: doc_info[key] for key in doc_info.keys()})
    except Exception as e:
        metadata['error'] = str(e)
    return metadata

def get_docx_metadata(file_path):
    """Get metadata for DOCX files."""
    metadata = get_basic_metadata(file_path)
    try:
        doc = Document(file_path)
        core_props = doc.core_properties
        metadata['author'] = core_props.author
        metadata['title'] = core_props.title
        metadata['subject'] = core_props.subject
        metadata['created'] = core_props.created
        metadata['modified'] = core_props.modified
    except Exception as e:
        metadata['error'] = str(e)
    return metadata

def get_metadata(file_path):
    """Get metadata based on file type."""
    _, file_extension = os.path.splitext(file_path)
    if file_extension.lower() in ['.jpg', '.jpeg', '.png', '.bmp', '.gif']:
        return get_image_metadata(file_path)
    elif file_extension.lower() in ['.mp3', '.wav', '.flac', '.aac']:
        return get_audio_metadata(file_path)
    elif file_extension.lower() == '.pdf':
        return get_pdf_metadata(file_path)
    elif file_extension.lower() == '.docx':
        return get_docx_metadata(file_path)
    else:
        return get_basic_metadata(file_path)

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            return redirect(request.url)
        if file:
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(file_path)
            metadata = get_metadata(file_path)
            return render_template('metadata.html', metadata=metadata)
    return render_template('upload.html')

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True)

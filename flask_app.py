from flask import Flask, request
import os
from werkzeug.utils import secure_filename
from werkzeug.datastructures import  FileStorage
from llama_index import SimpleDirectoryReader, GPTVectorStoreIndex, Document,  StorageContext, load_index_from_storage

# initialize manager connection
# NOTE: you might want to handle the password in a less hardcoded way
#manager = BaseManager(('', 5602), b'password')
#manager.register('query_index')
#manager.connect()

#...
#manager.register('insert_into_index')
#...

import os
from multiprocessing import Lock
from llama_index import SimpleDirectoryReader, GPTVectorStoreIndex, Document,  StorageContext, load_index_from_storage
from llama_index.storage.docstore import SimpleDocumentStore
from llama_index.storage.index_store import SimpleIndexStore
from llama_index.vector_stores import SimpleVectorStore


# NOTE: for local testing only, do NOT deploy with your key hardcoded
os.environ['OPENAI_API_KEY'] = "Enter-Your-Key-Here"

index = None
lock = Lock()

#new file insert
def insert_into_index(doc_text, doc_id=None):
    global index
    document = SimpleDirectoryReader(input_files=[doc_text]).load_data()[0]
    if doc_id is not None:
        document.doc_id = doc_id

    with lock:
        index.insert(document)
        index.storage_context.persist()

#query index
def query_index_data(query_text):
   global index
   index_dir = "./storage"
   global index
   storage_context = StorageContext.from_defaults(docstore=SimpleDocumentStore(),vector_store=SimpleVectorStore(),index_store=SimpleIndexStore())
  
   documents = SimpleDirectoryReader("./documents").load_data()
   index = GPTVectorStoreIndex.from_documents(documents, storage_context=storage_context)
   storage_context.persist()#storage_context.persist(index_dir)
   query_engine = index.as_query_engine()
   response = query_engine.query(query_text)
   return str(response)

app = Flask(__name__)

@app.route("/uploadFile", methods=["POST"])
def upload_file():
    global manager
    if 'file' not in request.files:
        return "Please send a POST request with a file", 400

    filepath = None
    try:
        uploaded_file = request.files["file"]
        filename = secure_filename(uploaded_file.filename)
        filepath = os.path.join('documents', os.path.basename(filename))
        uploaded_file.save(filepath)

        if request.form.get("filename_as_doc_id", None) is not None:
            insert_into_index(filepath, doc_id=filename)
        else:
            insert_into_index(filepath)
    except Exception as e:
        # cleanup temp file
        if filepath is not None and os.path.exists(filepath):
            os.remove(filepath)
        return "Error: {}".format(str(e)), 500

    # cleanup temp file
    if filepath is not None and os.path.exists(filepath):
        os.remove(filepath)

    return "File inserted!", 200

@app.route("/query", methods=["GET"])
def query_index():
  global index
  query_text = request.args.get("text", None)
  if query_text is None:
    return "No text found, please include a ?text=blah parameter in the URL", 400
  response = query_index_data(query_text)
  return str(response), 200

@app.route("/")
def home():
    return "Hello World!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5601)
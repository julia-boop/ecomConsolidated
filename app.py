# import eventlet
# eventlet.monkey_patch()

# from flask import Flask, render_template, send_file
# from flask_socketio import SocketIO, emit
# from Main import get_logiwa_file, process_file
# from io import BytesIO
# import re
# import time
# import json
# import os
# import shutil
# from dotenv import load_dotenv

# load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

# RUN_TIMES_FILE = "runtimes.json"
# run_times = []

# if os.path.exists(RUN_TIMES_FILE):
#     with open(RUN_TIMES_FILE, "r") as f:
#         run_times = json.load(f)


# app = Flask(__name__)
# app.config['SECRET_KEY'] = os.getenv("SOCKETIO_SECRET")  # You can change this
# socketio = SocketIO(app, async_mode='threading')

# @app.route('/')
# def index():
#     return render_template('form_socket.html')

# def progress(msg):
#     emit("progress", msg)

# generated_pdfs = {}
# @socketio.on('generate_report')
# def handle_generate(data):

#     global run_times
#     start_time = time.time()

#     try:
#         date = data.get('date', '')
#         job_code = data.get('job_code', '')
#         client = data.get('client', '')
    
#         file_path = get_logiwa_file(job_code=job_code, date=date, client=client, progress_callback=progress)

#         if not file_path:
#             emit("error", "No file downloaded from Logiwa.", broadcast=True)
#             return
#         df = process_file(file_path, progress_callback=progress)

#         if df is None or df.empty:
#             emit("error", "No data after processing.", broadcast=True)
#             return

#         client_df = df[df["Client"] == client]

#         if client_df.empty:
#             emit("error", f"No data found for client: {client}", broadcast=True)
#             return

#         # Generate PDF in memory
#         pdf_bytes, filename = generate_pdf_report_for_client(client_df, return_bytes=True)
#         generated_pdfs[filename] = pdf_bytes  # store in memory temporarily

#         emit("done", {"pdf_url": f"/download/{filename}"})

#         elapsed = round(time.time() - start_time, 2)
#         run_times.append(elapsed)
#         with open(RUN_TIMES_FILE, "w") as f:
#             json.dump(run_times, f)
#         average = round(sum(run_times) / len(run_times), 2)

#     except Exception as e:
#         print("Error:", e)
#         emit("error", str(e))

# def generate_pdf_report_for_client(client_df, return_bytes=False):
#     from weasyprint import HTML
#     from datetime import datetime
#     import pandas as pd

#     client = client_df["Client"].iloc[0]
#     safe_client = re.sub(r'[^A-Za-z0-9_\-]', '_', client)
#     date_str = datetime.today().strftime('%m-%d-%Y')
#     filename = f"{safe_client}_report_{date_str}.pdf"

#     css = """
#     <style>
#         @page {
#             size: A4 landscape;
#             margin: 20mm;
#         }
#         body {
#             font-family: Arial, sans-serif;
#             font-size: 16px;
#         }
#         h2 {
#             text-align: center;
#         }
#         table {
#             border-collapse: collapse;
#             width: 100%;
#             table-layout: fixed;
#         }
#         th, td {
#             border: 1px solid #ddd;
#             text-align: center;
#             padding: 8px;
#         }
#         th {
#             background-color: #f2f2f2;
#         }
#         th:nth-child(2), td:nth-child(2) {
#             width: 150px;
#         }
#         th:nth-child(3), td:nth-child(3) {
#             width: 300px;
#         }
#         thead {
#             display: table-header-group;
#         }
#     </style>
#     """

#     html_table = client_df.to_html(index=False, escape=False)
#     full_html = f"""
#     <html><head>{css}</head>
#     <body>
#         <h2>E-Commerce Orders – {client} – {datetime.today().strftime('%m-%d-%Y')}</h2>
#         {html_table}
#     </body>
#     </html>
#     """

#     if return_bytes:
#         from io import BytesIO
#         pdf_buffer = BytesIO()
#         HTML(string=full_html).write_pdf(pdf_buffer)
#         return pdf_buffer.getvalue(), filename

#     if os.path.exists('barcodes'):
#         shutil.rmtree('barcodes')

#     return pdf_buffer.getvalue(), filename

# @app.route("/average")
# def get_average():
#     if run_times:
#         average = round(sum(run_times) / len(run_times), 2)
#         return {"average": average}
#     else:
#         return {"average": None}
    
# @app.route('/download/<filename>')
# def download_pdf(filename):
#     pdf_bytes = generated_pdfs.get(filename)
#     if pdf_bytes is None:
#         return "File not found", 404
#     return send_file(
#         BytesIO(pdf_bytes),
#         mimetype='application/pdf',
#         as_attachment=True,
#         download_name=filename  # Flask 2.0+ supports this
#     )

# socketio.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

from flask import Flask, render_template, send_file
from flask_socketio import SocketIO, emit
from Main import get_logiwa_file, process_file
from io import BytesIO
from datetime import datetime
import os
import re
import time
import json
import shutil
from dotenv import load_dotenv

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

RUN_TIMES_FILE = "runtimes.json"
generated_pdfs = {}
run_times = []

# Load runtime history if exists
if os.path.exists(RUN_TIMES_FILE):
    with open(RUN_TIMES_FILE, "r") as f:
        run_times = json.load(f)

# Flask app setup
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv("SOCKETIO_SECRET", "supersecretkey")

# ❌ Previously: async_mode="eventlet"
# ✅ Now: async_mode="gevent"
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="gevent")

@app.route('/')
def index():
    return render_template('form_socket.html')

@app.route("/average")
def get_average():
    if run_times:
        average = round(sum(run_times) / len(run_times), 2)
        return {"average": average}
    return {"average": None}

@app.route('/download/<filename>')
def download_pdf(filename):
    pdf_bytes = generated_pdfs.get(filename)
    if not pdf_bytes:
        return "File not found", 404
    return send_file(BytesIO(pdf_bytes),
                     mimetype='application/pdf',
                     as_attachment=True,
                     download_name=filename)

@socketio.on('generate_report')
def handle_generate(data):
    global run_times
    start_time = time.time()

    try:
        job_code = data.get('job_code', '')
        client = data.get('client', '')

        def progress(msg):
            emit("progress", msg)

        file_path = get_logiwa_file(job_code=job_code, date=None, client=client, progress_callback=progress)

        if not file_path:
            emit("error", "No file downloaded from Logiwa.", broadcast=True)
            return

        df = process_file(file_path, progress_callback=progress)
        if df is None or df.empty:
            emit("error", "No data after processing.", broadcast=True)
            return

        client_df = df[df["Client"] == client]
        if client_df.empty:
            emit("error", f"No data found for client: {client}", broadcast=True)
            return

        pdf_bytes, filename = generate_pdf_report_for_client(client_df, return_bytes=True)
        generated_pdfs[filename] = pdf_bytes

        emit("done", {"pdf_url": f"/download/{filename}"})

        elapsed = round(time.time() - start_time, 2)
        run_times.append(elapsed)
        with open(RUN_TIMES_FILE, "w") as f:
            json.dump(run_times, f)

    except Exception as e:
        print("❌ Error:", e)
        emit("error", str(e))

def generate_pdf_report_for_client(client_df, return_bytes=False):
    from weasyprint import HTML

    client = client_df["Client"].iloc[0]
    safe_client = re.sub(r'[^A-Za-z0-9_\-]', '_', client)
    date_str = datetime.today().strftime('%m-%d-%Y')
    filename = f"{safe_client}_report_{date_str}.pdf"

    css = """
    <style>
        @page {
            size: A4 landscape;
            margin: 20mm;
        }
        body {
            font-family: Arial, sans-serif;
            font-size: 16px;
        }
        h2 {
            text-align: center;
        }
        table {
            border-collapse: collapse;
            width: 100%;
            table-layout: fixed;
        }
        th, td {
            border: 1px solid #ddd;
            text-align: center;
            padding: 8px;
        }
        th {
            background-color: #f2f2f2;
        }
        th:nth-child(2), td:nth-child(2) {
            width: 150px;
        }
        th:nth-child(3), td:nth-child(3) {
            width: 300px;
        }
        thead {
            display: table-header-group;
        }
    </style>
    """

    html_table = client_df.to_html(index=False, escape=False)
    full_html = f"""
    <html><head>{css}</head>
    <body>
        <h2>E-Commerce Orders – {client} – {date_str}</h2>
        {html_table}
    </body>
    </html>
    """

    if return_bytes:
        pdf_buffer = BytesIO()
        HTML(string=full_html).write_pdf(pdf_buffer)

        if os.path.exists('barcodes'):
            shutil.rmtree('barcodes')

        return pdf_buffer.getvalue(), filename

    return None, filename

# ✅ Clean production entry point
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host="0.0.0.0", port=port)

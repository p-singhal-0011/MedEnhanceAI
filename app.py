import os
import io
import uuid
import torch
from flask import Flask, render_template, request, send_file, session, make_response, jsonify
from datetime import datetime
from model.hybrid_model import GeneratorUNetTransformer
from utils.preprocess import preprocess_image
from utils.postprocess import save_output
from utils.metrics import calculate_metrics
from utils.llm_analysis import get_llm_report, get_chat_response
from utils.report_generator import generate_report

app = Flask(__name__)

# Global storage to avoid 4KB session cookie limit
latest_result = {}

UPLOAD_DIR = "static/uploads"
OUTPUT_DIR = "static/outputs"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

model = GeneratorUNetTransformer().to(device)
model.load_state_dict(torch.load("model/hybrid_best.pth", map_location=device))
model.eval()

def make_clean_filename(original_filename: str, prefix: str = "") -> str:
    """
    Generates a clean, anonymous filename.
    Example: enhanced_3f8a1c2b_20260530_141022.png
    - Strips original filename entirely (no WhatsApp/personal names in URLs)
    - Adds 8-char UUID for uniqueness
    - Adds timestamp for chronological sorting
    - Preserves original file extension
    """
    ext       = os.path.splitext(original_filename)[-1].lower() or ".png"
    uid       = uuid.uuid4().hex[:8]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    tag       = f"{prefix}_" if prefix else ""
    return f"{tag}{uid}_{timestamp}{ext}"

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        file = request.files["image"]

        # Guard: no file uploaded
        if not file or file.filename == "":
            return render_template("index.html", error="No file selected.")
    
        # Clean filenames — no personal/WhatsApp names in paths or URLs
        input_filename  = make_clean_filename(file.filename, prefix="input")
        output_filename = make_clean_filename(file.filename, prefix="enhanced")

        input_path  = os.path.join(UPLOAD_DIR, input_filename)
        output_path = os.path.join(OUTPUT_DIR, output_filename)

        file.save(input_path)

        inp = preprocess_image(input_path).to(device)

        with torch.no_grad():
            out = model(inp)

        save_output(out, output_path)

        # Calculate quality metrics & AI-powered report
        metrics = calculate_metrics(input_path, output_path)
        report = get_llm_report(input_path, output_path)

        # Store in global for PDF generation
        latest_result['data'] = {
            'input_path':  input_path,
            'output_path': output_path,
            'metrics':     metrics,
            'report':      report,
        }

        input_url  = "/" + input_path.replace("\\", "/")
        output_url = "/" + output_path.replace("\\", "/")

        return render_template(
            "index.html",
            input_image  = input_url,
            output_image = output_url,
            metrics      = metrics,
            report       = report,
        )
    return render_template("index.html")

@app.route("/download-report")
def download_report():
    """Generate and stream the clinical PDF report."""
    data = latest_result.get('data')
    if not data:
        return "No report data found. Please enhance an image first.", 404
    
    try:
        pdf_bytes = generate_report(
            data['input_path'],
            data['output_path'],
            data['metrics'],
            data['report']
        )
        
        timestamp   = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_name = f"MedEnhance_Report_{timestamp}.pdf"
        
        return send_file(
            io.BytesIO(pdf_bytes),
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'MedEnhance_Report_{timestamp}.pdf'
        )
        
    except Exception as e:
        print(f"PDF generation error: {e}")
        return f"Error generating PDF: {str(e)}", 500

@app.route("/chat", methods=["POST"])
def chat():
    """Clinical assistant — answers questions about the current scan pair."""
    payload  = request.json or {}
    question = payload.get("question", "").strip()

    analysis_data = latest_result.get('data')
    if not analysis_data:
        return jsonify({
            "response": "Please enhance an image first so I can analyse it for you."
        }), 400
    
    if not question:
        return jsonify({
            "response": "Please type a question about the scan."
        }), 400
            
    response_text = get_chat_response(
        question, 
        analysis_data['input_path'], 
        analysis_data['output_path']
    )
    
    return jsonify({"response": response_text})

if __name__ == "__main__":
    app.run(debug=True)

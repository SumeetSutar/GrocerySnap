from flask import Flask, request, jsonify, render_template, send_file
from flask_cors import CORS
from reportlab.pdfgen import canvas
from io import BytesIO
import openai, base64

app = Flask(__name__)
CORS(app)

openai.api_key = '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'  # Replace with your OpenAI API key

@app.route('/')
def index():
    return render_template('index.html')

def make_base64_image(file):
    img_bytes = file.read()
    return "data:image/jpeg;base64," + base64.b64encode(img_bytes).decode()

@app.route('/generate', methods=['POST'])
def generate():
    if 'file' not in request.files:
        return jsonify(success=False, error='No file provided')
    img = request.files['file']
    b64 = make_base64_image(img)
    try:
        resp = openai.chat.completions.create(
            model="gpt-4o",
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": "List ingredients with approximate quantities for this dish."},
                    {"type": "image_url", "image_url": {"url": b64}}
                ]
            }],
            max_tokens=400
        )
        items = [line.strip("•- ").strip() for line in resp.choices[0].message.content.split('\n') if line.strip()]
        return jsonify(success=True, items=items)
    except Exception as e:
        return jsonify(success=False, error=str(e))

@app.route('/get-recipe-steps', methods=['POST'])
def get_steps():
    if 'file' not in request.files:
        return jsonify(success=False, error='No file provided')
    b64 = make_base64_image(request.files['file'])
    try:
        resp = openai.chat.completions.create(
            model="gpt-4o",
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": "Provide step-by-step cooking instructions for 2 servings including quantities."},
                    {"type": "image_url", "image_url": {"url": b64}}
                ]
            }],
            max_tokens=600
        )
        steps = [s.strip("•- 1234567890.").strip() for s in resp.choices[0].message.content.split('\n') if s.strip()]
        return jsonify(success=True, steps=steps)
    except Exception as e:
        return jsonify(success=False, error=str(e))

def make_pdf(lines, title):
    buf = BytesIO()
    p = canvas.Canvas(buf)
    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, 800, title)
    p.setFont("Helvetica", 12)
    y = 770
    for idx, text in enumerate(lines, 1):
        p.drawString(60, y, text if isinstance(text, str) else f"{idx}. {text}")
        y -= 20
        if y < 50:
            p.showPage()
            y = 800
    p.save()
    buf.seek(0)
    return buf

@app.route('/download-pdf', methods=['POST'])
def download_list_pdf():
    items = request.get_json().get('items', [])
    buf = make_pdf([f"• {it}" for it in items], "Grocery List")
    return send_file(buf, as_attachment=True, download_name='grocery_list.pdf', mimetype='application/pdf')

@app.route('/download-steps-pdf', methods=['POST'])
def download_steps_pdf():
    steps = request.get_json().get('steps', [])
    buf = make_pdf([f"{i}. {s}" for i, s in enumerate(steps, 1)], "Recipe Steps")
    return send_file(buf, as_attachment=True, download_name='recipe_steps.pdf', mimetype='application/pdf')

if __name__ == '__main__':
    app.run(debug=True)

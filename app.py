import os
import datetime
from flask import Flask, render_template, request, jsonify, session
from agent_logic import get_logistics_research, ask_followup_question

app = Flask(__name__)
app.secret_key = "logistics_secret_key_123" # Required for session storage

REPORTS_DIR = "reports"
os.makedirs(REPORTS_DIR, exist_ok=True)

@app.route('/')
def home():
    # Start fresh on page load (optional, or keep history)
    session.clear() 
    return render_template('index.html')

@app.route('/new_chat')
def new_chat():
    session.clear()
    return jsonify({'status': 'cleared'})

@app.route('/history')
def get_history():
    if not os.path.exists(REPORTS_DIR): return jsonify([])
    files = [f for f in os.listdir(REPORTS_DIR) if f.endswith('.md')]
    files.sort(reverse=True)
    return jsonify(files)

@app.route('/load_report/<filename>')
def load_report(filename):
    filepath = os.path.join(REPORTS_DIR, filename)
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Set this file as the "Active Context" for follow-ups
        session['active_file'] = filename
        
        return jsonify({'content': content})
    return jsonify({'error': 'File not found'}), 404

@app.route('/process_query', methods=['POST'])
def process_query():
    user_input = request.form['query']
    active_file = session.get('active_file')

    # SCENARIO A: Follow-up Question (Active File Exists)
    if active_file:
        filepath = os.path.join(REPORTS_DIR, active_file)
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                report_content = f.read()
            
            print(f"--- Processing Follow-up on {active_file} ---")
            answer = ask_followup_question(report_content, user_input)
            return jsonify({'response': answer, 'mode': 'chat'})
        else:
            # File missing? Reset.
            session.pop('active_file', None)

    # SCENARIO B: New Research Task (No Active File)
    try:
        print(f"--- Starting New Research Task: {user_input} ---")
        report = get_logistics_research(user_input)
        
        # Save Report
        safe_topic = "".join(x for x in user_input if x.isalnum() or x in " -_").strip()[:30]
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"{timestamp}_{safe_topic}.md"
        filepath = os.path.join(REPORTS_DIR, filename)
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"# Research Task: {user_input}\n")
            f.write(f"Date: {datetime.datetime.now()}\n\n")
            f.write(report)
        
        # Set as active for future follow-ups
        session['active_file'] = filename
        
        final_response = f"{report}\n\n---\n*Report saved. You can now ask follow-up questions about this topic.*"
        return jsonify({'response': final_response, 'mode': 'research', 'filename': filename})

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'response': f"An error occurred: {str(e)}"})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
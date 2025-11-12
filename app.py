from flask import Flask, request, jsonify
import threading
from secret import EMAIL, SECRET
from quiz_solver import QuizSolver

app = Flask(__name__)

@app.route('/quiz', methods=['POST'])
def handle_quiz():
    """Main endpoint to receive quiz tasks"""
    try:
        # Parse JSON payload
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "Invalid JSON"}), 400
        
        # Verify secret
        if data.get('secret') != SECRET:
            return jsonify({"error": "Invalid secret"}), 403
        
        # Verify email
        if data.get('email') != EMAIL:
            return jsonify({"error": "Invalid email"}), 403
        
        # Get quiz URL
        quiz_url = data.get('url')
        if not quiz_url:
            return jsonify({"error": "Missing URL"}), 400
        
        # Start quiz solver in background thread (non-blocking)
        solver = QuizSolver()
        thread = threading.Thread(
            target=solver.solve_quiz_chain,
            args=(quiz_url,),
            daemon=True
        )
        thread.start()
        
        # Return immediate 200 response
        return jsonify({
            "status": "accepted",
            "message": "Quiz solving initiated"
        }), 200
        
    except Exception as e:
        print(f"Error in handle_quiz: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=7777, debug=False)
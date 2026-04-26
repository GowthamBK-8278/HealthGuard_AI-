from flask import Flask, request, jsonify, render_template
import google.generativeai as genai
import os, base64, json
from dotenv import load_dotenv

load_dotenv(override=True)
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("⚠️ WARNING: GEMINI_API_KEY not found in .env file. AI features will not work.")
else:
    genai.configure(api_key=api_key)

app = Flask(__name__)

# ================= ROUTES ================= #

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/chatbot')
def chatbot():
    return render_template('chatbot.html')

@app.route('/health')
def health():
    return render_template('health.html')


# ================= MEDICAL DATASET ================= #

def load_dataset():
    try:
        with open('dataset.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading dataset: {e}")
        return []

MEDICAL_DATASET = load_dataset()


def analyze_symptoms(symptom_text):
    symptom_text = symptom_text.lower()
    user_symptoms = [s.strip() for s in symptom_text.replace(",", " ").split()]

    best_match = None
    best_score = 0

    for disease in MEDICAL_DATASET:
        score = 0
        matched_keywords = []

        # Check required symptoms first
        required_met = all(req in symptom_text for req in disease["required"])
        if disease["required"] and not required_met:
            continue

        # Score based on keyword matches
        for keyword in disease["keywords"]:
            if keyword in symptom_text:
                score += 1
                matched_keywords.append(keyword)

        if score >= disease["min_match"] and score > best_score:
            best_score = score
            best_match = disease
            best_match = {**disease, "matched": matched_keywords, "score": score}

    return best_match


# ================= ANALYZE SYMPTOMS API ================= #


@app.route('/analyze-symptoms', methods=['POST'])
def analyze_symptoms_api():
    try:
        data = request.get_json()
        symptoms = data.get("symptoms", "").strip()

        if not symptoms:
            return jsonify({"error": "No symptoms provided"}), 400

        result = analyze_symptoms(symptoms)

        if not result:
            return jsonify({
                "condition": "Unidentified Condition",
                "dengue_risk": False,
                "severity": "Unknown ❓",
                "observations": ["Symptoms do not clearly match a known condition"],
                "advice": [
                    "Please consult a General Physician for a proper checkup",
                    "Describe all your symptoms clearly to the doctor",
                    "Stay hydrated and take rest",
                    "Monitor if symptoms worsen or new symptoms appear"
                ],
                "medicines": ["Consult a doctor before taking any medication"],
                "specialist": "General Physician",
                "matched": []
            })

        return jsonify(result)

    except Exception as e:
        print("ERROR:", e)
        return jsonify({"error": "Server error"}), 500


# ================= GEMINI CHAT API ================= #

SYSTEM_PROMPT = """
You are HealthGuard AI+, an expert medical assistant with knowledge equivalent to a senior physician with 20+ years of experience.
Your role:
- Analyze symptoms described by the user with clinical precision
- Provide detailed, accurate medical information including possible conditions, causes, and urgency level
- Give specific, actionable advice (not just 'see a doctor')
- Suggest likely medicines (with generic names) and when to seek emergency care
- Mention red flag symptoms the user should watch for
- Be empathetic, clear, and professional
- Always add a disclaimer that you are AI and professional consultation is recommended for serious conditions
Format your responses in clear sections when appropriate. Be thorough but concise.
"""

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        msg = data.get("message", "").strip()
        history = data.get("history", [])

        if not msg:
            return jsonify({"reply": "⚠️ Please type something"})

        model = genai.GenerativeModel(
            model_name="gemini-flash-latest",
            system_instruction=SYSTEM_PROMPT
        )

        # Build conversation history
        chat_history = []
        for turn in history[-10:]:  # keep last 10 turns for context
            chat_history.append({"role": turn["role"], "parts": [turn["text"]]})

        chat_session = model.start_chat(history=chat_history)
        response = chat_session.send_message(msg)
        reply = response.text

        return jsonify({"reply": reply})

    except Exception as e:
        print("CHAT ERROR:", e)
        return jsonify({"reply": "⚠️ AI service temporarily unavailable. Please try again."})


# ================= GEMINI IMAGE ANALYSIS ================= #

REPORT_ANALYSIS_PROMPT = """
You are a senior medical consultant and laboratory expert. Analyze the provided medical report (blood test, scan, or prescription).

Break down the findings into these sections:
1. **📊 Key Biomarkers:** [List important values and if they are high/low/normal]
2. **📝 Summary of Findings:** [Plain English explanation of what the report means]
3. **❓ Clinical Implications:** [What these results could indicate]
4. **💡 Suggested Next Steps:** [Further tests or doctor visits needed]
5. **🥗 Lifestyle/Dietary Advice:** [Based on the results]

Always emphasize that this is an AI summary and they must discuss it with their prescribing doctor.
"""

@app.route('/report')
def report_page():
    return render_template('report.html')

IMAGE_ANALYSIS_PROMPT = """
You are a medical imaging and dermatology AI expert. Analyze the provided medical image carefully.

Provide a comprehensive clinical analysis in this exact structure:

**🔍 Visual Findings:**
[Describe what you observe in the image - color, texture, shape, size, distribution, location if visible]

**🩺 Possible Conditions:**
[List 1-3 most likely conditions based on visual findings, ranked by probability]

**⚠️ Severity Assessment:**
[Rate as: Mild / Moderate / Severe / Emergency - with brief justification]

**💡 Immediate Actions:**
[Specific steps the person should take right now]

**👨‍⚕️ Specialist Recommended:**
[Which type of doctor to visit and how urgently]

**🚨 Red Flag Warnings:**
[Signs that mean they need emergency care immediately]

**💊 General Care Tips:**
[Home care measures while awaiting professional help]

Be accurate, specific, and clinically rigorous. This analysis helps people understand their condition.
"""

@app.route('/analyze-image', methods=['POST'])
def analyze_image():
    try:
        data = request.get_json()
        image_b64 = data.get("image")
        mime_type = data.get("mime_type", "image/jpeg")
        context = data.get("context", "")

        if not image_b64:
            return jsonify({"result": "⚠️ No image provided"})

        image_bytes = base64.b64decode(image_b64)

        model = genai.GenerativeModel("gemini-flash-latest")

        prompt = IMAGE_ANALYSIS_PROMPT
        if context:
            prompt += f"\n\nAdditional context from patient: {context}"

        response = model.generate_content([
            prompt,
            {"mime_type": mime_type, "data": image_bytes}
        ])

        return jsonify({"result": response.text})

    except Exception as e:
        print("IMAGE ANALYSIS ERROR:", e)
        return jsonify({"result": "⚠️ Could not analyze the image. Please try again with a clearer photo."})


@app.route('/analyze-report', methods=['POST'])
def analyze_report():
    try:
        data = request.get_json()
        image_b64 = data.get("image")
        mime_type = data.get("mime_type", "image/jpeg")

        if not image_b64:
            return jsonify({"result": "⚠️ No report image provided"})

        image_bytes = base64.b64decode(image_b64)
        model = genai.GenerativeModel("gemini-flash-latest")

        response = model.generate_content([
            REPORT_ANALYSIS_PROMPT,
            {"mime_type": mime_type, "data": image_bytes}
        ])

        return jsonify({"result": response.text})

    except Exception as e:
        print("REPORT ANALYSIS ERROR:", e)
        return jsonify({"result": "⚠️ Error analyzing report. Please ensure the image is clear."})

@app.route('/diet')
def diet_page():
    return render_template('diet.html')

@app.route('/generate-diet', methods=['POST'])
def generate_diet():
    try:
        data = request.get_json()
        age = data.get("age")
        weight = data.get("weight")
        goal = data.get("goal")
        conditions = data.get("conditions", "None")

        prompt = f"""
        You are an expert clinical nutritionist. Generate a personalized 1-day sample meal plan for a person with the following profile:
        - Age: {age}
        - Weight: {weight} kg
        - Goal: {goal}
        - Health Conditions: {conditions}

        Provide:
        1. **🍳 Breakfast:** [Meal + nutritional benefit]
        2. **🍱 Lunch:** [Meal + nutritional benefit]
        3. **🍎 Snacks:** [Healthy snack options]
        4. **🍽️ Dinner:** [Meal + nutritional benefit]
        5. **💧 Hydration Goal:** [Daily water target]
        6. **🚫 Avoid:** [Foods to avoid based on conditions]

        Keep the tone encouraging and professional.
        """

        model = genai.GenerativeModel("gemini-flash-latest")
        response = model.generate_content(prompt)

        return jsonify({"plan": response.text})

    except Exception as e:
        print("DIET GENERATION ERROR:", e)
        return jsonify({"plan": "⚠️ Error generating diet plan. Please try again."})

# ================= RUN ================= #

if __name__ == "__main__":
    app.run(debug=True)
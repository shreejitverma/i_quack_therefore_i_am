import os, json, random
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash
from jinja2 import DictLoader

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'app.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# ---------- Title / XP thresholds ----------
TITLE_THRESHOLDS = [
    (0, 99, "Novice"),
    (100, 299, "Seeker"),
    (300, 599, "Philosopher"),
    (600, 100000, "Peaceful")
]

def get_title(xp):
    for low, high, title in TITLE_THRESHOLDS:
        if low <= xp <= high:
            return title
    return "Unknown"

# ---------- Database Model ----------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False, default="")
    xp = db.Column(db.Integer, default=0)
    current_pillar = db.Column(db.Integer, default=1)
    concentration = db.Column(db.String(128), default="")
    last_quiz_time = db.Column(db.DateTime, default=datetime.utcnow)
    created_on = db.Column(db.DateTime, default=datetime.utcnow)

with app.app_context():
    db.create_all()
    # Ensure single user "Attila the Duck"
    user = User.query.filter_by(username="Attila the Duck").first()
    if not user:
        duck = User(
            username="Attila the Duck",
            password_hash=generate_password_hash("secretpw"),
            xp=0
        )
        db.session.add(duck)
        db.session.commit()

def get_attila():
    return User.query.filter_by(username="Attila the Duck").first()

# ---------- Load Generic Quiz Data ----------
QUIZ_FILE = os.path.join(basedir, 'quiz.json')
if os.path.exists(QUIZ_FILE):
    with open(QUIZ_FILE, "r", encoding="utf-8") as f:
        generic_quiz_data = json.load(f).get("quiz", [])
else:
    generic_quiz_data = []

def init_quiz_state():
    # Check if the user has selected a concentration
    concentration = session.get("selected_concentration")
    if concentration:
        quiz_file = os.path.join(basedir, f'{concentration}_quiz.json')
    else:
        quiz_file = QUIZ_FILE

    if os.path.exists(quiz_file):
        with open(quiz_file, "r", encoding="utf-8") as f:
            all_questions = json.load(f).get("quiz", [])
    else:
        all_questions = []

    # Filter out questions that have been answered already.
    answered_ids = session.get("answered_ids", [])
    filtered_questions = [q for q in all_questions if q.get("question") not in answered_ids]

    if not filtered_questions:
        # If user answered all questions, use full list.
        filtered_questions = all_questions

    total = len(filtered_questions)
    if total == 0:
        selected_questions = []
    elif total < 12:
        selected_questions = filtered_questions
    else:
        selected_questions = random.sample(
            filtered_questions,
            random.randint(12, min(20, total))
        )
    session['quiz_questions'] = selected_questions
    session['quiz_current'] = 0
    session['hearts'] = 5
    session['feedback'] = None
    session['wrong_ids'] = []

# ---------- Embedded Templates ----------
templates = {
    "base.html": """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Quack Philosophy</title>
    <style>
        * {
          margin: 0;
          padding: 0;
          box-sizing: border-box;
        }
        html, body {
          height: 100%;
          width: 100%;
        }
        body {
          background-color: #0c0c0c;
          color: #f5f5f5;
          font-family: sans-serif;
          transition: transform 0.7s ease;
          transform: translateY(0);
        }
        body.slide-up {
          transform: translateY(-100%);
        }
        body.slide-down {
          transform: translateY(100%);
        }
        .back-home {
          position: fixed;
          bottom: 20px;
          right: 20px;
        }
        .container {
          max-width: 1000px;
          margin: 40px auto;
          padding: 20px;
        }
        .btn {
          display: inline-block;
          padding: 0.75em 1.5em;
          border-radius: 30px;
          background: #f5f5f5;
          color: #0c0c0c;
          font-weight: 600;
          cursor: pointer;
          border: none;
          text-align: center;
          text-decoration: none;
          margin: 5px;
          transition: background 0.3s;
        }
        .btn:hover {
          background: #dadada;
        }
        .heart {
          color: red;
          font-size: 1.2em;
        }
    </style>
</head>
<body>
    {% block content %}{% endblock %}
    <script>
      document.addEventListener('DOMContentLoaded', () => {
        const transitionLinks = document.querySelectorAll('a.btn, .btn.back-home');
        transitionLinks.forEach(link => {
          link.addEventListener('click', event => {
            const href = link.getAttribute('href');
            // Skip the transition if link is for next_question
            if (href && href.startsWith('/') && !href.includes("next_question")) {
              event.preventDefault();
              if (link.classList.contains('back-home') || href === '/') {
                document.body.classList.add('slide-down');
              } else {
                document.body.classList.add('slide-up');
              }
              setTimeout(() => {
                window.location.href = href;
              }, 700);
            }
          });
        });
      });
    </script>
</body>
</html>
""",

    "index.html": """
{% extends "base.html" %}
{% block content %}
<style>
  .hero {
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    text-align: center;
    background: linear-gradient(rgba(189,189,189,0.3), rgba(189,189,189,0.3)),
                url('{{ url_for('static', filename='backdrop.jpg') }}') no-repeat center center;
    background-size: cover;
    padding: 40px 20px;
  }
  .hero-title {
    font-size: 3rem;
    margin-bottom: 1rem;
    color: #f5f5f5;
    text-shadow: 2px 2px 5px rgba(0,0,0,0.5);
    line-height: 1.2;
  }
  .highlighted-line {
    background: #bdbdbd;
    border-radius: 40px;
    padding: 0 12px;
    color: #0c0c0c;
    display: inline-block;
    text-shadow: none;
  }
  .tagline {
    font-size: 1.2rem; margin-bottom: 2rem; color: #bdbdbd;
  }
  .hero-buttons {
    display: flex; gap: 1em; flex-wrap: wrap; justify-content: center; margin-top: 2rem;
  }
</style>
<div class="hero">
  <h1 class="hero-title">
    I Quack<br/>
    <span class="highlighted-line">Therefore I Am</span>
  </h1>
  <p class="tagline">#1 Stoic Quack Quiz Backed by Wisdom</p>
  <div class="hero-buttons">
    <a class="btn" href="{{ url_for('profile_page') }}">Profile</a>
    <a class="btn" href="{{ url_for('start_quiz') }}">Take Quiz</a>
    <a class="btn" href="{{ url_for('concentrations') }}">Concentrations</a>
  </div>
  <div style="margin-top: 2rem;">
    <p>Current XP: {{ user.xp }}</p>
    <p>Title: {{ title }}</p>
    <p>Current Pillar: {{ user.current_pillar }} / 7</p>
    <p>
      Hearts:
      {% for i in range(hearts) %}
        <span class="heart">&#10084;</span>
      {% endfor %}
    </p>
    <p>Selected Concentration: {{ session.get('selected_concentration', 'None')|capitalize }}</p>
  </div>
</div>
{% endblock %}
""",

    "profile.html": """
{% extends "base.html" %}
{% block content %}
<style>
  .profile-page {
    width: 100%; min-height: 100vh; display: flex; background-color: #0c0c0c;
  }
  .profile-left {
    flex: 2;
    background: url('{{ url_for('static', filename='profile_backdrop.jpg') }}') no-repeat center center;
    background-size: contain;
  }
  .profile-right {
    flex: 3;
    display: flex; flex-direction: column; justify-content: center; align-items: flex-start;
    padding: 40px;
  }
  .profile-image {
    width: 150px; height: 150px; border-radius: 50%; border: 3px solid #999;
    margin-bottom: 20px; object-fit: cover;
  }
  .profile-name { font-size: 2rem; margin-bottom: 0.5rem; }
  .profile-title { font-size: 1.2rem; margin-bottom: 1rem; color: #cfcfcf; }
  .profile-stats { margin-top: 1rem; font-size: 1rem; color: #bebebe; }
  .profile-stats p { margin: 0.3rem 0; }
</style>
<div class="profile-page">
  <div class="profile-left"></div>
  <div class="profile-right">
    <img src="{{ url_for('static', filename='profile_picture.jpg') }}" alt="Profile" class="profile-image">
    <h2 class="profile-name">{{ user.username }}</h2>
    <div class="profile-title">{{ title }}</div>
    <div class="profile-stats">
      <p>Day Joined: {{ user.created_on.strftime('%B %d, %Y') if user.created_on else 'Unknown' }}</p>
      <p>Completed Lessons: <strong>None</strong></p>
    </div>
  </div>
</div>
<a class="btn back-home" href="{{ url_for('index') }}">Back to Homepage</a>
{% endblock %}
""",

    "concentrations.html": """
{% extends "base.html" %}
{% block content %}
<style>
  .char-container {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 30px;
    align-items: end;
    justify-items: center;
    margin-top: 40px;
  }
  .char-card {
    width: 250px;
    height: 420px;
    background-color: #222;
    position: relative;
    text-align: center;
    cursor: pointer;
  }
  .char-card img {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }
  .post-img {
    position: absolute;
    top: 0; left: 0;
    width: 100%; height: 100%;
    opacity: 0;
    transition: opacity 0.4s;
  }
  .char-card:hover .post-img {
    opacity: 1;
  }
  .info-block {
    position: absolute;
    bottom: 10px; left: 50%;
    transform: translateX(-50%);
    text-align: center;
  }
  .char-title {
    font-weight: bold;
    background: rgba(0,0,0,0.5);
    padding: 3px 6px;
    margin-bottom: 0.5rem;
    display: inline-block;
  }
</style>
<div class="container">
  <h2>Concentration Selection</h2>
  <p style="font-size:0.9rem;color:#ccc;">
    Hover over each philosophy to see the transition. Click to select a concentration.
  </p>
  <div class="char-container">
    {% for phil in phil_data %}
      <div class="char-card">
        <img src="{{ url_for('static', filename=phil.pre_img) }}" alt="{{ phil.name }} pre">
        <img class="post-img" src="{{ url_for('static', filename=phil.post_img) }}" alt="{{ phil.name }} post">
        <div class="info-block">
          <div class="char-title">{{ phil.name }}</div>
          <a class="btn" href="{{ url_for('select_concentration', phil=phil.name) }}">Select</a>
          {% if phil.status == 'some_wrong' %}
            <a class="btn" href="{{ url_for('learn_where_you_lack', phil=phil.name.lower()) }}">Learn Where You Lack</a>
          {% else %}
            <a class="btn" href="{{ url_for('learn', phil=phil.name.lower()) }}">Learn</a>
          {% endif %}
        </div>
      </div>
    {% endfor %}
  </div>
</div>
<a class="btn back-home" href="{{ url_for('index') }}">Back to Homepage</a>
{% endblock %}
""",

    "learn.html": """
{% extends "base.html" %}
{% block content %}
<div class="container" style="text-align:center;">
    <h2>Learn {{ phil|capitalize }}</h2>
    <p>Select how you want to learn:</p>
    <a class="btn" href="{{ url_for('learn_ebook', phil=phil) }}">e_book</a>
    <a class="btn" href="{{ url_for('learn_audiobook', phil=phil) }}">audiobook</a>
</div>
<a class="btn back-home" href="{{ url_for('concentrations') }}">Back to Concentrations</a>
{% endblock %}
""",

    "learn_ebook.html": """
{% extends "base.html" %}
{% block content %}
<div class="container" style="text-align:center;">
    <h2>Reading {{ phil|capitalize }} eBook</h2>
    <div style="margin:20px auto; max-width:600px; height:800px;">
      <iframe src="{{ url_for('static', filename=(phil+'_ebook.pdf')) }}" width="100%" height="100%"></iframe>
    </div>
</div>
<a class="btn back-home" href="{{ url_for('concentrations') }}">Back to Concentrations</a>
{% endblock %}
""",

    "learn_audiobook.html": """
{% extends "base.html" %}
{% block content %}
<div class="container" style="text-align:center;">
    <h2>Listening to {{ phil|capitalize }} Audiobook</h2>
    <p style="margin:20px auto; max-width:600px;">
      <audio id="audioPlayer" controls style="width:100%;">
        <source src="{{ url_for('static', filename=(phil+'_audiobook.mp3')) }}" type="audio/mpeg">
        Your browser does not support audio playback.
      </audio>
    </p>
    <button class="btn" onclick="skipTime(-10)">-10s</button>
    <button class="btn" onclick="skipTime(10)">+10s</button>
    <script>
      const audio = document.getElementById('audioPlayer');
      function skipTime(seconds) {
        audio.currentTime = Math.max(0, audio.currentTime + seconds);
      }
    </script>
</div>
<a class="btn back-home" href="{{ url_for('concentrations') }}">Back to Concentrations</a>
{% endblock %}
""",

    "quiz.html": """
{% extends 'base.html' %}
{% block content %}
<style>
.quiz-container {
  width: 100%;
  min-height: 100vh;
  background-color: #0c0c0c;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 40px 20px;
}
.quiz-header {
  color: #f5f5f5;
  font-size: 1.8rem;
  margin-bottom: 40px;
  text-transform: uppercase;
  letter-spacing: 2px;
}
.quiz-options {
  width: 100%;
  max-width: 600px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.option-block {
  border: 1px solid #f5f5f5;
  padding: 15px 20px;
  text-align: center;
  cursor: pointer;
  font-size: 1.1rem;
  color: #f5f5f5;
  position: relative;
  transition: background 0.3s;
}
.option-block:hover {
  background: #181818;
}
.option-block.selected {
  background: #333;
  border-color: #41f581;
}
.option-block input[type='radio'] {
  position: absolute;
  left: -9999px;
}
.quiz-actions {
  margin-top: 30px;
  text-align: center;
}
.quiz-actions .btn {
  margin: 10px;
}
.quiz-progress-bar {
  margin-top: 50px;
  width: 100%;
  max-width: 600px;
  height: 8px;
  background-color: #333;
  position: relative;
}
.quiz-progress-fill {
  background-color: #41f581;
  height: 100%;
  width: 0%;
  transition: width 0.3s;
}
</style>
<div class='quiz-container'>
  <div class='quiz-header'>QUIZ</div>
  <form method='post' style='text-align:center;'>
    {% if not feedback %}
      <div style='color:#f5f5f5; font-size:1.3rem; margin-bottom:20px;'>
        <div class="quiz-question">
          {{ question.question }}
        </div>
      </div>
      <div class='quiz-options'>
        {% for opt in question.options %}
          <div class='option-block' onclick="selectOption(this)">
            <input type='radio' id='opt{{ loop.index }}' name='answer' value='{{ opt[0] }}' required>
            <label for='opt{{ loop.index }}'>{{ opt }}</label>
          </div>
        {% endfor %}
      </div>
      <div class='quiz-actions'>
        <button type='submit' class='btn'>Submit</button>
      </div>
    {% else %}
      {% if feedback.correct %}
        <p style='color:green;font-size:1.2rem;'>Correct!</p>
        <p style='font-size:1rem;'>Principle: {{ question.principle }}</p>
        <p style='font-size:1rem;'>Marcus Quote: {{ question.marcusQuote }}</p>
      {% else %}
        <p style='color:red;font-size:1.2rem;'>Incorrect!</p>
      {% endif %}
      <div class='quiz-actions'>
        <a href='{{ url_for("next_question") }}' class='btn'>Next</a>
      </div>
    {% endif %}
  </form>
  <div style='position:absolute; top:20px; right:20px;'>
    {% for i in range(hearts) %}
      <img src='{{ url_for("static", filename="heart.jpg") }}' alt='Heart' style='width:30px;height:30px;margin-left:2px;'>
    {% endfor %}
  </div>
  <div class='quiz-progress-bar'>
    {% set progress = (current_index + 1) / total_questions * 100 %}
    <div class='quiz-progress-fill' style='width:{{ progress }}%;'></div>
  </div>
</div>
<a class='btn back-home' href='{{ url_for("index") }}' style='position:absolute; bottom:20px; left:20px;'>
  Back
</a>
<script>
  function selectOption(element) {
    // Remove selection from all option blocks
    document.querySelectorAll('.option-block').forEach(block => {
      block.classList.remove('selected');
      block.querySelector('input[type="radio"]').checked = false;
    });
    // Mark the clicked block as selected and check its radio input
    element.classList.add('selected');
    element.querySelector('input[type="radio"]').checked = true;
  }
</script>
{% endblock %}
""",

    "review.html": """
{% extends "base.html" %}
{% block content %}
<div class="container">
    {% with messages = get_flashed_messages() %}
      {% if messages %}
        <ul style="color: red;">
          {% for message in messages %}
            <li>{{ message }}</li>
          {% endfor %}
        </ul>
      {% endif %}
    {% endwith %}
    <h2>Review Wrong Answers</h2>
    {% if wrong_question %}
        <p><strong>Review this concept:</strong></p>
        <p>{{ wrong_question.question }}</p>
        <p>Type an explanation of the concept (min 10 words) to recover your heart:</p>
        <form method="post">
            <textarea name="explanation" rows="4" cols="50" required></textarea><br/><br/>
            <button type="submit" class="btn">Submit Explanation</button>
        </form>
    {% else %}
        <p>No wrong answers to review. You're all set!</p>
        <p><a href="{{ url_for('start_quiz') }}" class="btn">Start New Quiz</a></p>
    {% endif %}
</div>
<a class="btn back-home" href="{{ url_for('index') }}">Back to Homepage</a>
{% endblock %}
"""
}

app.jinja_loader = DictLoader(templates)

def get_phil_status(user, phil_name):
    # Simulated status. In practice, this should reflect actual quiz outcomes.
    return random.choice(['no_quiz','no_wrong','some_wrong'])

@app.route("/")
def index():
    user = get_attila()
    hearts = session.get("hearts", 5)
    title = get_title(user.xp)
    return render_template("index.html", user=user, title=title, hearts=hearts)

@app.route("/profile")
def profile_page():
    user = get_attila()
    title = get_title(user.xp)
    return render_template("profile.html", user=user, title=title)

@app.route("/concentrations")
def concentrations():
    user = get_attila()
    phil_list = ["Stoicism", "Existentialism", "Platonism", "Utilitarianism"]
    phil_data = []
    for phil in phil_list:
        status = get_phil_status(user, phil)
        pre_img = phil.lower() + "_pre.jpg"
        post_img = phil.lower() + "_post.jpg"
        phil_data.append({
            "name": phil,
            "pre_img": pre_img,
            "post_img": post_img,
            "status": status
        })
    return render_template("concentrations.html", phil_data=phil_data)

@app.route("/select_concentration/<phil>")
def select_concentration(phil):
    session["selected_concentration"] = phil.lower()
    flash(f"{phil.capitalize()} selected!")
    return redirect(url_for("index"))

@app.route("/learn/<phil>")
def learn(phil):
    return render_template("learn.html", phil=phil)

@app.route("/learn_where_you_lack/<phil>")
def learn_where_you_lack(phil):
    flash(f"Showing specialized lessons for your wrong answers in {phil.capitalize()}.")
    return redirect(url_for("learn", phil=phil))

@app.route("/learn/<phil>/ebook")
def learn_ebook(phil):
    return render_template("learn_ebook.html", phil=phil)

@app.route("/learn/<phil>/audiobook")
def learn_audiobook(phil):
    return render_template("learn_audiobook.html", phil=phil)

@app.route("/start_quiz")
def start_quiz():
    init_quiz_state()
    return redirect(url_for("quiz_page"))

@app.route("/quiz", methods=["GET", "POST"])
def quiz_page():
    user = get_attila()
    quiz_questions = session.get("quiz_questions", [])
    current_index = session.get("quiz_current", 0)
    hearts = session.get("hearts", 5)

    if hearts <= 0:
        flash("No hearts remaining! Please review your wrong answers to earn hearts.")
        return redirect(url_for("review"))

    if current_index >= len(quiz_questions):
        flash("Quiz completed!")
        return redirect(url_for("index"))

    question = quiz_questions[current_index] if quiz_questions else {}
    feedback = session.get("feedback")

    if request.method == "POST" and not feedback:
        answer = request.form.get("answer")
        is_correct = (answer == question.get("correct"))
        feedback = {"correct": is_correct}

        # Save answered question text to avoid repeating it in future quizzes.
        answered_ids = session.get("answered_ids", [])
        answered_ids.append(question.get("question"))
        session["answered_ids"] = answered_ids

        if is_correct:
            flash("Correct!")
            user.xp += question.get("xp", 0)
            if user.current_pillar < 7:
                user.current_pillar += 1
            db.session.commit()
        else:
            flash("Incorrect!")
            session["hearts"] = hearts - 1
            wrong_list = session.get("wrong_ids", [])
            wrong_list.append(question)
            session["wrong_ids"] = wrong_list

        session["feedback"] = feedback
        return redirect(url_for("quiz_page"))

    return render_template("quiz.html",
                           question=question,
                           current_index=current_index,
                           total_questions=len(quiz_questions),
                           hearts=hearts,
                           feedback=feedback)

@app.route("/next_question")
def next_question():
    feedback = session.get("feedback")
    if feedback:
        session["feedback"] = None
    current_index = session.get("quiz_current", 0)
    session["quiz_current"] = current_index + 1
    return redirect(url_for("quiz_page"))

@app.route("/review", methods=["GET", "POST"])
def review():
    wrong_list = session.get("wrong_ids", [])
    wrong_question = wrong_list[0] if wrong_list else None

    if request.method == "POST" and wrong_question:
        explanation = request.form.get("explanation", "")
        # Simulated AI check: for now require a minimum of 10 words.
        if len(explanation.split()) >= 10:
            flash("Review passed! You earned a heart.")
            wrong_list.pop(0)
            session["wrong_ids"] = wrong_list
            session["hearts"] = session.get("hearts", 0) + 1
            return redirect(url_for("index"))
        else:
            flash("Explanation too short. Please elaborate.")

    return render_template("review.html", wrong_question=wrong_question)

if __name__ == "__main__":
    app.run(debug=True)

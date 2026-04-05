# from flask import Flask
# from flask import render_template
# from models import db

# app = Flask(__name__)

# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
# app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# db.init_app(app)

# # Import models AFTER db init
# from models.student import Student
# from models.hall import Hall

# @app.route("/")
# def home():
#     return render_template("login.html")


# if __name__ == "__main__":
#     with app.app_context():
#         db.create_all()
#     app.run(debug=True)



from flask import Flask, render_template, request, redirect, url_for, session


from models import db
from seating_algorithm import fill_seats_zigzag
hall_allocations = {}
# from models.exam import Exam


app = Flask(__name__)
app.secret_key = "exam_secret_key"

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

from models.student import Student
from models.hall import Hall



# ----------------------
# ROUTES
# ----------------------

@app.route("/")
def login():
    return render_template("login.html")


@app.route("/login", methods=["POST"])
def login_post():
    username = request.form["username"]
    password = request.form["password"]

    # Simple admin login (you can upgrade later)
    if username == "admin" and password == "1234":
        session["user"] = username
        return redirect(url_for("dashboard"))
    else:
        return render_template("login.html", error="Invalid Credentials")


@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))

    total_students = Student.query.count()
    total_halls = Hall.query.count()
    total_departments = db.session.query(Student.department).distinct().count()

    return render_template(
        "dashboard.html",
        total_students=total_students,
        total_halls=total_halls,
        total_departments=total_departments
    )

@app.route("/students")
def students_page():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template("upload_students.html")


from docx import Document

@app.route("/upload_students", methods=["POST"])
def upload_students():
    if "user" not in session:
        return redirect(url_for("login"))

    department = request.form["department"]
    semester = request.form["semester"]
    file = request.files["file"]

    if file:

        document = Document(file)

        for table in document.tables:
            for row in table.rows[1:]:  # Skip header row

                reg_no = row.cells[1].text.strip()   # REGNO
                name = row.cells[2].text.strip()     # NAME

                # Skip empty rows
                if not reg_no or not name:
                    continue

                student = Student(
                    register_number=reg_no,
                    name=name,
                    department=department,
                    semester=int(semester)
                )

                db.session.add(student)

        db.session.commit()

        return render_template(
            "upload_students.html",
            message="Students Uploaded Successfully!"
        )

    return redirect(url_for("students_page"))

@app.route('/halls', methods=['GET', 'POST'])
def halls_page():
    if "user" not in session:
        return redirect(url_for("login"))

    if request.method == 'POST':
        hall_name = request.form['hall_name']
        rows = int(request.form['rows'])
        columns = int(request.form['columns'])

        capacity = rows * columns

        new_hall = Hall(
            hall_name=hall_name,
            rows=rows,         
            columns=columns,
            capacity=capacity
        )

        db.session.add(new_hall)
        db.session.commit()

    halls = Hall.query.all()

    return render_template("halls.html", halls=halls)



@app.route("/uploaded_batches")
def uploaded_batches():
    if "user" not in session:
        return redirect(url_for("login"))

    batches = db.session.query(
        Student.department,
        Student.semester,
        db.func.count(Student.id).label("count")
    ).group_by(
        Student.department,
        Student.semester
    ).all()

    return render_template("uploaded_batches.html", batches=batches)

@app.route("/delete_batch/<department>/<int:semester>")
def delete_batch(department, semester):
    if "user" not in session:
        return redirect(url_for("login"))

    Student.query.filter_by(
        department=department,
        semester=semester
    ).delete()

    db.session.commit()

    return redirect(url_for("uploaded_batches"))

@app.route('/toggle_hall/<int:hall_id>')
def toggle_hall(hall_id):
    hall = Hall.query.get(hall_id)

    if hall.status == "active":
        hall.status = "disabled"
    else:
        hall.status = "active"

    db.session.commit()
    return redirect(url_for('halls_page'))


@app.route('/hall_plan', methods=['GET','POST'])
# @app.route("/hall_plan")
def hall_plan():

    if "user" not in session:
        return redirect(url_for("login"))

    halls = Hall.query.filter_by(status="active").all()

    return render_template("hall_plan.html", halls=halls)

@app.route('/generate_all_seating', methods=['POST'])
def generate_all_seating():
    
    global hall_allocations
    hall_allocations = {}

    # halls = Hall.query.all()
    halls = Hall.query.filter_by(status="active").all()

    # Get students department wise
    cse_students = Student.query.filter_by(department="CSE").all()
    ece_students = Student.query.filter_by(department="ECE").all()
    it_students  = Student.query.filter_by(department="IT").all()
    eee_students = Student.query.filter_by(department="EEE").all()

    dept_students = {
        "CSE": cse_students.copy(),
        "ECE": ece_students.copy(),
        "IT": it_students.copy(),
        "EEE": eee_students.copy()
    }

    for hall in halls:

        rows = hall.rows
        cols = hall.columns
        capacity = rows * cols

        seating = [[None for _ in range(cols)] for _ in range(rows)]

        dept_order = ["CSE", "ECE", "IT", "EEE"]
        dept_index = 0

        for i in range(rows):

            if i % 2 == 0:
                col_range = range(cols)
            else:
                col_range = range(cols-1, -1, -1)

            for j in col_range:

                for _ in range(len(dept_order)):

                    dept = dept_order[dept_index]
                    dept_index = (dept_index + 1) % len(dept_order)

                    if dept_students[dept]:

                        student = dept_students[dept].pop(0)
                        seating[i][j] = student
                        break

        hall_allocations[hall.id] = seating

    return redirect('/hall_plan')


@app.route('/view_seating/<int:hall_id>')
def view_seating(hall_id):

    hall = Hall.query.get(hall_id)
    seating = hall_allocations.get(hall_id)

    return render_template(
        'seating_output.html',
        hall=hall,
        seating=seating
    )

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))



# ----------------------

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)

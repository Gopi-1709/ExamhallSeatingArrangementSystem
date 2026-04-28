
from flask import Flask, flash, render_template, request, redirect, url_for, session
from reportlab.platypus import Image

from models import db
from seating_algorithm import fill_seats_zigzag
hall_allocations = {}
# from models.exam import Exam


app = Flask(__name__)
app.secret_key = "exam_secret_key"
app.secret_key = "your_secret_key"
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
    total_halls = Hall.query.filter_by(status="active").count()
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
    year = request.form["year"]
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
                    year=int(year)
                )

                db.session.add(student)

        db.session.commit()

        return render_template(
            "upload_students.html",
            message="Students Uploaded Successfully!"
        )

    return redirect(url_for("students_page"))

from sqlalchemy.exc import IntegrityError

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
            capacity=capacity,
            status="active"
        )
        try:
            db.session.add(new_hall)
            db.session.commit()
            flash("✅ Hall added successfully!", "success")
            
        except IntegrityError:
            db.session.rollback()
            flash("⚠️ Hall already exists!", "error")
        return redirect(url_for('halls_page'))  # 🔥 stay on same page


    halls = Hall.query.all()

    return render_template("halls.html", halls=halls)



@app.route("/uploaded_batches")
def uploaded_batches():
    if "user" not in session:
        return redirect(url_for("login"))

    batches = db.session.query(
        Student.department,
        Student.year,
        db.func.count(Student.id).label("count")
    ).group_by(
        Student.department,
        Student.year,
    ).all()

    return render_template("uploaded_batches.html", batches=batches)

@app.route("/delete_batch/<department>/<int:year>")
def delete_batch(department, year):
    if "user" not in session:
        return redirect(url_for("login"))

    Student.query.filter_by(
        department=department,
        year=year
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

from flask import session

@app.route('/hall_plan', methods=['GET','POST'])
# @app.route("/hall_plan")
def hall_plan():

    if "user" not in session:
        return redirect(url_for("login"))
    
    if request.method == "POST":
        session['exam_date'] = request.form.get('exam_date')
        session['session'] = request.form.get('session')

    halls = Hall.query.filter_by(status="active").all()

    return render_template("hall_plan.html", halls=halls)

@app.route('/generate_all_seating', methods=['POST'])
def generate_all_seating():
    
    global hall_allocations
    hall_allocations = {}
    
    session['exam_date'] = request.form.get('exam_date')
    session['exam_session'] = request.form.get('session')

    years = request.form.getlist("year")

    # convert to int
    years = [int(y) for y in years]
    
    halls = Hall.query.all()

    # Get students department wise
    cse_students = Student.query.filter_by(department="CSE").all()
    ece_students = Student.query.filter_by(department="ECE").all()
    it_students  = Student.query.filter_by(department="IT").all()
    eee_students = Student.query.filter_by(department="EEE").all()

    
    dept_students = {}
    
    

    for dept in ["CSE", "ECE", "IT", "EEE"]:
        for y in years:

            students = Student.query.filter_by(
                department=dept,
                year=y
            ).all()

            if students:
                dept_students[f"{dept}_{y}"] = students.copy()
    
    
    dept_subject = {}

    for dept in ["CSE", "ECE", "IT", "EEE"]:
        for y in years:
            key = f"{dept}_{y}"
            dept_subject[key] = request.form.get(f"{dept.lower()}_{y}_subject")

    
    for hall in halls:

        rows = hall.rows
        cols = hall.columns

        seating = [[None for _ in range(cols)] for _ in range(rows)]


        # ✅ Step 1: pick FIRST 2 departments
        available = [d for d in dept_students if dept_students[d]]

        if len(available) < 2:
            break

        active_depts = [available[0], available[1]]

        toggle = 0

        for i in range(rows):

            if i % 2 == 0:
                col_range = range(cols)
            else:
                col_range = range(cols-1, -1, -1)

            for j in col_range:

                placed = False

                # 🔥 Update active departments dynamically
                active_depts = [d for d in active_depts if dept_students[d]]
                only_one = len(available) == 1
                if only_one:

                    dept = available[0]

                    # 🔥 Alternate seat logic
                    if (i + j) % 2 == 0:
                        if dept_students[dept]:
                            student = dept_students[dept].pop(0)
                            seating[i][j] = (student, dept)
                        else:
                            seating[i][j] = None
                    else:
                        seating[i][j] = None

                    continue

                # 🔥 If one dept finished → ADD NEW dept
                if len(active_depts) < 2:
                    for d in dept_students:
                        if d not in active_depts and dept_students[d]:
                            active_depts.append(d)
                            if len(active_depts) >= 2:
                                break

                # 🔥 Try adding 3rd dept ONLY if needed
                if len(active_depts) == 2:
                    for d in dept_students:
                        if d not in active_depts and dept_students[d]:
                            active_depts.append(d)
                            break

                # 🔁 Try placement with rules
                for _ in range(len(active_depts)):

                    dept = active_depts[toggle % len(active_depts)]
                    toggle += 1

                    if not dept_students[dept]:
                        continue

                    current_subject = dept_subject.get(dept)

                    # LEFT CHECK
                    left = seating[i][j-1] if j > 0 else None
                    if left:
                        if left[1] == dept:
                            continue
                        if dept_subject.get(left[1]) == current_subject:
                            continue

                    # TOP CHECK
                    top = seating[i-1][j] if i > 0 else None
                    if top:
                        if top[1] == dept:
                            continue
                        if dept_subject.get(top[1]) == current_subject:
                            continue

                    # ✅ PLACE
                    student = dept_students[dept].pop(0)
                    seating[i][j] = (student, dept)
                    placed = True
                    break

                # 🔥 FINAL CONTROLLED FALLBACK
                if not placed:

                    remaining = [d for d in dept_students if dept_students[d]]

                    # ✅ If multiple depts → TRY OTHER dept (not same as left/top)
                    if len(remaining) > 1:
                        for dept in remaining:

                            left = seating[i][j-1] if j > 0 else None
                            top = seating[i-1][j] if i > 0 else None

                            if left and left[1] == dept:
                                continue
                            if top and top[1] == dept:
                                continue

                            student = dept_students[dept].pop(0)
                            seating[i][j] = (student, dept)
                            placed = True
                            break

                    
        
        
        hall_allocations[hall.id] = seating
        
        
    
    return redirect('/hall_plan')


from flask import session

@app.route('/view_seating/<int:hall_id>')
def view_seating(hall_id):

    hall = Hall.query.get(hall_id)
    seating = hall_allocations.get(hall_id)
    
    exam_date = session.get('exam_date')
    exam_session = session.get('exam_session')

    return render_template(
        'seating_output.html',
        hall=hall,
        seating=seating,
        exam_date = exam_date,
        exam_session = exam_session
    )

@app.route('/print_all')
def print_all():

    halls = Hall.query.filter_by(status="active").all()
    exam_date = session.get('exam_date')
    exam_session = session.get('exam_session')
    
    all_seating = []

    for hall in halls:
        seating = hall_allocations.get(hall.id)

        # ✅ Skip if no seating generated
        if not seating:
            continue

        # ✅ Check if at least one student exists
        has_student = any(
            seat is not None
            for row in seating
            for seat in row
        )

        if not has_student:
            continue

        all_seating.append({
            "hall": hall,
            "seating": seating
        })

    return render_template(
        "print_all.html",
        all_seating=all_seating,
        exam_date=exam_date,
        exam_session=exam_session
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

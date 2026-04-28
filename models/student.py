from . import db

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    register_number = db.Column(db.String(20), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    department = db.Column(db.String(50), nullable=False)
    
    year = db.Column(db.Integer, nullable=False)

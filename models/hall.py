from . import db

class Hall(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hall_name = db.Column(db.String(50), unique=True, nullable=False)
    rows = db.Column(db.Integer, nullable=False)
    columns = db.Column(db.Integer, nullable=False)
    capacity = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), default="active")

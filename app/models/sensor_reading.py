from app.extensions import db
from datetime import datetime

class SensorReading(db.Model):
    __tablename__ = 'sensor_readings'
    id         = db.Column(db.Integer, primary_key=True)
    sensor_id  = db.Column(db.Integer, nullable=False, index=True)
    value      = db.Column(db.Float,   nullable=False)
    ts         = db.Column(db.DateTime, default=datetime.utcnow, index=True)

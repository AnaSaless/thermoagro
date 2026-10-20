from app.extensions import db
from datetime import datetime

class ActuatorHistory(db.Model):
    __tablename__ = 'actuator_history'
    id          = db.Column(db.Integer, primary_key=True)
    actuator_key= db.Column(db.String(50), index=True, nullable=False)
    user_id     = db.Column(db.Integer, db.ForeignKey('users.id'))
    action      = db.Column(db.String(10))        # open / close
    ts          = db.Column(db.DateTime, default=datetime.utcnow, index=True)

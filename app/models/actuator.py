from app.extensions import db
import json

class Actuator(db.Model):
    __tablename__ = 'actuators'
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    topic = db.Column(db.String(100), nullable=False)
    icon = db.Column(db.String(50), nullable=False)
    open_payload = db.Column(db.Text, nullable=False)   # armazenar JSON como string
    close_payload = db.Column(db.Text, nullable=False)

    def get_open_payload(self):
        return json.loads(self.open_payload)

    def get_close_payload(self):
        return json.loads(self.close_payload)

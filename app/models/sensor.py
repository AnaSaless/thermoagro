from app.extensions import db
import json

class Sensor(db.Model):
    __tablename__ = 'sensors'
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    topic = db.Column(db.String(100), nullable=False)
    icon = db.Column(db.String(50), nullable=False)
    unit = db.Column(db.String(20), nullable=True)
    defaults = db.Column(db.Text, nullable=True)

    def get_defaults(self):
        return json.loads(self.defaults or '{}')

    def set_defaults(self, defaults_dict):
        self.defaults = json.dumps(defaults_dict)

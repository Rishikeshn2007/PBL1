from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_name = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phno_no = db.Column(db.String(20), nullable=False)

    ckd_data = db.relationship('CKDData', backref='user', lazy=True)

    @staticmethod
    def register(user_name, password, email, phno_no):
        if User.query.filter_by(user_name=user_name).first() or User.query.filter_by(email=email).first():
            return None, "User already exists"
        
        hashed_password = generate_password_hash(password)
        new_user = User(user_name=user_name, password=hashed_password, email=email, phno_no=phno_no)
        db.session.add(new_user)
        db.session.commit()
        return new_user, "Registration successful"

    @staticmethod
    def authenticate(user_name, password):
        user = User.query.filter_by(user_name=user_name).first()
        if user and check_password_hash(user.password, password):
            return user
        return None

    def update_ckd_parameters(self, data):
        new_ckd = CKDData(user_id=self.id, **data)
        db.session.add(new_ckd)
        db.session.commit()
        return True

class CKDData(db.Model):
    __tablename__ = 'ckd_data'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())
    
    age = db.Column(db.Float)
    bp = db.Column(db.Float)
    sg = db.Column(db.Float)
    al = db.Column(db.String(20))
    su = db.Column(db.String(20))
    rbc = db.Column(db.String(20))
    pc = db.Column(db.String(20))
    pcc = db.Column(db.String(20))
    ba = db.Column(db.String(20))
    bgr = db.Column(db.Float)
    bu = db.Column(db.Float)
    sc = db.Column(db.Float)
    sod = db.Column(db.Float)
    pot = db.Column(db.Float)
    hemo = db.Column(db.Float)
    pcv = db.Column(db.Float)
    wc = db.Column(db.Float)
    rc = db.Column(db.Float)
    htn = db.Column(db.String(20))
    dm = db.Column(db.String(20))
    cad = db.Column(db.String(20))
    appet = db.Column(db.String(20))
    pe = db.Column(db.String(20))
    ane = db.Column(db.String(20))

    @property
    def prediction(self):
        if self.hemo and self.hemo < 12:
            return "CKD"
        return "Not CKD"

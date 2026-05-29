from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, make_response
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity, set_access_cookies, unset_jwt_cookies
from modules import db, User, CKDData
from sqlalchemy import text
from ai import MODEL_PATH, load_model, predict_ckd_details, train_and_save_model
import os
import mimetypes

mimetypes.add_type('text/css', '.css')
mimetypes.add_type('application/javascript', '.js')

app = Flask(__name__)
app.config['SECRET_KEY'] = 'Rishi123' 
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'Rishi123'
app.config['JWT_TOKEN_LOCATION'] = ['cookies']
app.config['JWT_COOKIE_CSRF_PROTECT'] = False
app.config['JWT_ACCESS_COOKIE_PATH'] = '/'

db.init_app(app)
jwt = JWTManager(app)


def ensure_ckd_data_columns():
    columns = db.session.execute(text("PRAGMA table_info(ckd_data)")).fetchall()
    column_names = {column[1] for column in columns}
    if "prediction_result" not in column_names:
        db.session.execute(
            text("ALTER TABLE ckd_data ADD COLUMN prediction_result VARCHAR(20)")
        )
    if "prediction_confidence" not in column_names:
        db.session.execute(
            text("ALTER TABLE ckd_data ADD COLUMN prediction_confidence FLOAT")
        )
    db.session.commit()


def ensure_model_file():
    if not os.path.exists(MODEL_PATH):
        train_and_save_model()
    model_data = load_model()
    if "model_accuracy" not in model_data:
        train_and_save_model()
        model_data = load_model()
    return model_data


with app.app_context():
    db.create_all()
    ensure_ckd_data_columns()

CKD_MODEL_DATA = ensure_model_file()


@app.route('/')
def home():
    return render_template('home.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        user_name = request.form.get('user_name')
        password = request.form.get('password')
        email = request.form.get('email')
        phno_no = request.form.get('phone') # Matching HTML name='phone'
        
        user, message = User.register(user_name, password, email, phno_no)
        if user:
            flash(message, 'success')
            return redirect(url_for('login'))
        else:
            flash(message, 'danger')
            return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user_name = request.form.get('user_name')
        password = request.form.get('password')
        if user_name=='admin' and password=='123456':
                access_token = create_access_token(identity=str('admin'))
                resp = make_response(redirect(url_for('admin')))
                set_access_cookies(resp, access_token)
                return resp
        user = User.authenticate(user_name, password)
        if user:
            access_token = create_access_token(identity=str(user.id))
            resp = make_response(redirect(url_for('dashboard')))
            set_access_cookies(resp, access_token)
            return resp
        else:
            flash('Invalid username or password', 'danger')
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    resp = make_response(redirect(url_for('home')))
    unset_jwt_cookies(resp)
    return resp

@app.route('/dashboard')
@jwt_required()
def dashboard():
    user_id = get_jwt_identity()
    user = db.session.get(User, int(user_id))
    if not user:
        resp = make_response(redirect(url_for('login')))
        unset_jwt_cookies(resp)
        return resp
    return render_template('dashboard.html', user=user)

@app.route('/history')
@jwt_required()
def history():
    user_id = get_jwt_identity()
    user = db.session.get(User, int(user_id))
    if not user:
        resp = make_response(redirect(url_for('login')))
        unset_jwt_cookies(resp)
        return resp
    records = CKDData.query.filter_by(user_id=int(user_id)).order_by(CKDData.timestamp.desc()).all()
    return render_template('history.html', user=user, history=records)

@app.route('/result/<int:record_id>')
@jwt_required()
def result(record_id):
    user_id = get_jwt_identity()
    user = db.session.get(User, int(user_id))
    if not user:
        resp = make_response(redirect(url_for('login')))
        unset_jwt_cookies(resp)
        return resp

    record = CKDData.query.filter_by(id=record_id, user_id=int(user_id)).first_or_404()
    model_accuracy = CKD_MODEL_DATA.get('model_accuracy')
    next_steps = get_next_steps(record.prediction)
    return render_template(
        'result.html',
        user=user,
        record=record,
        model_name=CKD_MODEL_DATA.get('model_name'),
        model_accuracy=model_accuracy,
        next_steps=next_steps,
    )


def get_next_steps(prediction):
    if prediction == 'CKD':
        return [
            'Book an appointment with a nephrologist or physician for proper clinical evaluation.',
            'Carry this report and ask about confirmatory tests such as urine albumin, eGFR, creatinine, and blood pressure review.',
            'Avoid self-medicating painkillers or kidney-related medicines without medical advice.',
            'Keep hydrated as advised by your doctor and monitor blood pressure and sugar if applicable.',
        ]

    return [
        'Keep regular health checkups, especially if you have diabetes, hypertension, or family history of kidney disease.',
        'Maintain healthy blood pressure, blood sugar, hydration, sleep, and diet habits.',
        'Repeat testing if symptoms continue or if a doctor recommends follow-up kidney function tests.',
    ]


@app.route('/form', methods=['GET', 'POST'])
@jwt_required()
def form():
    user_id = get_jwt_identity()
    user = db.session.get(User, int(user_id))
    if not user:
        resp = make_response(redirect(url_for('login')))
        unset_jwt_cookies(resp)
        return resp

    if request.method == 'POST':
        params = [
            'age', 'bp', 'sg', 'al', 'su', 'rbc', 'pc', 'pcc', 'ba', 'bgr', 
            'bu', 'sc', 'sod', 'pot', 'hemo', 'pcv', 'wc', 'rc', 'htn', 
            'dm', 'cad', 'appet', 'pe', 'ane'
        ]
        data = {}
        for p in params:
            val = request.form.get(p)
            if p in ['age', 'bp', 'sg', 'bgr', 'bu', 'sc', 'sod', 'pot', 'hemo', 'pcv', 'wc', 'rc']:
                try:
                    data[p] = float(val) if val else None
                except (ValueError, TypeError):
                    data[p] = None
            else:
                data[p] = val

        prediction_details = predict_ckd_details(data.get('sg'), data.get('al'), CKD_MODEL_DATA)
        data['prediction_result'] = prediction_details['prediction']
        data['prediction_confidence'] = prediction_details['confidence']

        record = user.update_ckd_parameters(data)
        return redirect(url_for('result', record_id=record.id))

    return render_template('form.html', ckd_data=user.ckd_data)

@app.route('/seed')
@jwt_required()
def seed():
    """Seed dummy CKD history data for the logged-in user (for demo purposes)."""
    from datetime import datetime, timedelta
    user_id = get_jwt_identity()
    user = db.session.get(User, int(user_id))
    if not user:
        resp = make_response(redirect(url_for('login')))
        unset_jwt_cookies(resp)
        return resp

    dummy_records = [
        {'age': 45, 'bp': 80, 'sg': 1.020, 'al': 'negative', 'su': 'negative', 'rbc': 'normal', 'pc': 'normal',
         'pcc': 'notpresent', 'ba': 'notpresent', 'bgr': 148, 'bu': 35, 'sc': 1.2, 'sod': 135,
         'pot': 4.5, 'hemo': 14.5, 'pcv': 44, 'wc': 7800, 'rc': 5.2, 'htn': 'no',
         'dm': 'no', 'cad': 'no', 'appet': 'good', 'pe': 'no', 'ane': 'no'},
        {'age': 62, 'bp': 100, 'sg': 1.010, 'al': '3+', 'su': 'positive', 'rbc': 'abnormal', 'pc': 'abnormal',
         'pcc': 'present', 'ba': 'notpresent', 'bgr': 380, 'bu': 120, 'sc': 6.4, 'sod': 128,
         'pot': 6.1, 'hemo': 9.8, 'pcv': 30, 'wc': 11400, 'rc': 3.2, 'htn': 'yes',
         'dm': 'yes', 'cad': 'yes', 'appet': 'poor', 'pe': 'yes', 'ane': 'yes'},
        {'age': 53, 'bp': 90, 'sg': 1.015, 'al': '1+', 'su': 'negative', 'rbc': 'normal', 'pc': 'normal',
         'pcc': 'notpresent', 'ba': 'notpresent', 'bgr': 200, 'bu': 60, 'sc': 2.8, 'sod': 132,
         'pot': 5.0, 'hemo': 11.2, 'pcv': 36, 'wc': 9000, 'rc': 4.1, 'htn': 'yes',
         'dm': 'yes', 'cad': 'no', 'appet': 'good', 'pe': 'no', 'ane': 'yes'},
    ]

    base_time = datetime.now()
    for i, record_data in enumerate(dummy_records):
        record = CKDData(user_id=int(user_id), **record_data)
        record.timestamp = base_time - timedelta(days=(i + 1) * 7)
        db.session.add(record)

    db.session.commit()
    flash('Dummy history data seeded successfully!', 'success')
    return redirect(url_for('history'))

@app.route('/admin')
@jwt_required()
def admin():
    id = get_jwt_identity()
    print(id)
    if id=='admin':
        users = User.query.all()
        return render_template('admin.html', users=users)
    resp = make_response(redirect(url_for('login')))
    unset_jwt_cookies(resp)
    return resp,403
        
if __name__ == '__main__':
    app.run(debug=True, port=5000)

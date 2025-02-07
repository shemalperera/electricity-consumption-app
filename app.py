from flask import Flask, render_template, url_for, request, redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os 

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Electricity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    last_reading_date = db.Column(db.DateTime, nullable=False)
    last_reading = db.Column(db.Integer, nullable=False)
    current_reading_date = db.Column(db.DateTime,nullable=False)
    current_reading = db.Column(db.Integer, nullable=False)
    total_units = db.Column(db.Integer, nullable=False)
    total_charge = db.Column(db.Float, nullable=False)
    billing_period = db.Column(db.String(50), nullable=False)    
    
with app.app_context():
    db.create_all()

def tot_charge(tot_units):
    if tot_units>180:
        return 89.0 + 2360/tot_units
    elif 180>=tot_units>120:
        return 32.0 + 480/tot_units
    elif 120>=tot_units>90:
        return 27.75 + 480/tot_units
    elif 90>=tot_units>60:
        return 10.0 + 90/tot_units
    else:
        return 7.85
        

@app.route('/', methods=['GET','POST'])
def index():
    if request.method == 'POST':

        last_reading_date = datetime.strptime(request.form['date1'], '%Y-%m-%d')
        last_reading = int(request.form['num1'])
        current_reading_date = datetime.strptime(request.form['date2'], '%Y-%m-%d')
        current_reading = int(request.form['num2'])

        if current_reading < last_reading:
            records = Electricity.query.all()
            return render_template('index.html', message="Error! Current reading must be greater than Last reading", ids=records)
        
        if current_reading_date < last_reading_date:
            records = Electricity.query.all()
            return render_template('index.html', message="Error! Wrong Date Entries", ids=records)
        
        total_units = current_reading - last_reading
        CHARGE_PER_UNIT = tot_charge(total_units)
        total_charge = total_units*CHARGE_PER_UNIT
        billing_period = f"{last_reading_date.strftime('%b %d, %Y')} - {current_reading_date.strftime('%b %d, %Y')}"

        new_entry = Electricity(
            last_reading_date = last_reading_date,
            last_reading = last_reading,
            current_reading_date = current_reading_date,
            current_reading = current_reading,
            total_units = total_units,
            total_charge = total_charge,
            billing_period = billing_period
        )

        db.session.add(new_entry)
        db.session.commit()
        return redirect('/')
    
    records = Electricity.query.all()
    return render_template('index.html', ids=records)

@app.route('/delete/<int:id>')
def delete(id):
    record = Electricity.query.get_or_404(id)
    db.session.delete(record)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/update/<int:id>', methods=['GET', 'POST'])
def update(id):
    record = Electricity.query.get_or_404(id)
    record.last_reading_date = record.last_reading_date.strftime('%Y-%m-%d')
    record.current_reading_date = record.current_reading_date.strftime('%Y-%m-%d')
    
    if request.method == 'POST':
        record.last_reading_date = datetime.strptime(request.form['date1'], '%Y-%m-%d')
        record.last_reading = int(request.form['num1'])
        record.current_reading_date = datetime.strptime(request.form['date2'], '%Y-%m-%d')
        record.current_reading = int(request.form['num2'])

        if record.current_reading < record.last_reading:
            records = Electricity.query.all()
            return render_template('index.html', message="Error! Current reading must be greater than Last reading", ids=records)
        
        if record.current_reading_date < record.last_reading_date:
            records = Electricity.query.all()
            return render_template('index.html', message="Error! Wrong Date Entries", ids=records)

        record.total_units = record.current_reading - record.last_reading
        CHARGE_PER_UNIT = tot_charge(record.total_units)
        record.total_charge = record.total_units*CHARGE_PER_UNIT
        record.billing_period = f"{record.last_reading_date.strftime('%b %d, %Y')} - {record.current_reading_date.strftime('%b %d, %Y')}"   
        
        db.session.commit()
        return redirect(url_for('index'))
    
    return render_template('update.html', record=record)

if __name__ ==  "__main__":
    app.run(debug=True, host="0.0.0.0")




# flask imports
from flask import Flask,jsonify, make_response
from flask_sqlalchemy import SQLAlchemy
import uuid 
from werkzeug.security import generate_password_hash, check_password_hash
# imports for PyJWT authentication
import jwt
from datetime import datetime, timedelta
from functools import wraps
from flask import request

# creates Flask object
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your secret key'
# database name
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///Database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
# creates SQLALCHEMY object
db = SQLAlchemy(app)

# Database ORMs
class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(50), unique=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(70), unique=True,nullable=False)
    password = db.Column(db.String(80),nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    is_admin=db.Column(db.Boolean, default=False, nullable=False)
    is_customer=db.Column(db.Boolean, default=False, nullable=False)

class Screen(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True)

class Row(db.Model):
    id = db.Column(db.String(10), primary_key=True)
    number_of_seats = db.Column(db.Integer)
    aisle_seats = db.Column(db.String)
    reserved_seats = db.Column(db.String)

# decorator for verifying the JWT
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        # jwt is passed in the request header
        if 'x-access-token' in request.headers:
            token = request.headers['x-access-token']
        # return 401 if token is not passed
        if not token:
            return jsonify({'message': 'Token is missing !!'}), 401
        try:
            # decoding the payload to fetch the stored details
            data = jwt.decode(token, app.config['SECRET_KEY'])
            current_user = User.query.filter_by(
                public_id=data['public_id']).first()
        except:
            return jsonify({
                'message': 'Token is invalid !!'
            }), 401
        # returns the current logged in users contex to the routes
        return f(current_user, *args, **kwargs)
    return decorated

# signup route
@app.route('/signup', methods=['POST'])
def signup():
    # creates a dictionary of the form data
    data = request.form
    print(data,'=======>')
    # gets name, email and password
    name, email = data.get('name'), data.get('email')
    password = data.get('password')

    # checking for existing user
    user = User.query.filter_by(email=email).first()
    if not user:
        # database ORM object
        user = User(
            public_id=str(uuid.uuid4()),
            name=name,
            email=email,
            password=generate_password_hash(password)
        )
        # insert user
        db.session.add(user)
        db.session.commit()

        return make_response('Successfully registered.', 201)
    else:
        # returns 202 if user already exists
        return make_response('User already exists. Please Log in.', 202)


# route for loging user in
@app.route('/login', methods=['POST'])
def login():
    # creates dictionary of form data
    auth = request.form
    if not auth or not auth.get('email') or not auth.get('password'):
        # returns 401 if any email or / and password is missing
        return make_response('Could not verify',401,{'WWW-Authenticate': 'Basic realm ="Login required !!"'})

    user = User.query.filter_by(email=auth.get('email')).first()
    if not user:
        # returns 401 if user does not exist
        return make_response('Could not verify',401,{'WWW-Authenticate': 'Basic realm ="User does not exist !!"'})

    if check_password_hash(user.password, auth.get('password')):
        # generates the JWT Token
        token = jwt.encode({
            'public_id': user.public_id,
            'exp': datetime.utcnow() + timedelta(minutes=30)
        }, app.config['SECRET_KEY'])

        return make_response(jsonify({'token': token.decode('UTF-8')}), 201)
    # returns 403 if password is wrong
    return make_response('Could not verify',403,{'WWW-Authenticate': 'Basic realm ="Wrong Password !!"'})


#Admin post informations
@app.route('/screens', methods=['POST'])
@token_required
def screens_info(current_user):
    try:
        name = request.json['name']
        seat_info = request.json['seatInfo']
    except:
        return jsonify({"status": 400, "message": "Bad Request"})
    screen = Screen(name=name)
    try:
        db.session.add(screen)
        db.session.commit()
        screen = Screen.query.filter_by(name=name).first()
        for key, value in seat_info.items():
            num_seats = value['numberOfSeats']
            aisle_seats = value['aisleSeats']
            row_id = str(screen.id) + '_' + key
            row = Row(id=row_id,
                      number_of_seats=num_seats,
                      aisle_seats="_".join(str(x) for x in aisle_seats),
                      reserved_seats="")

            db.session.add(row)
            db.session.commit()

        db.session.commit()
        return jsonify({"status": 200, "message": "Screen details successfully added"})
    except :
        return jsonify({"status": 400,
                        "message": "Failure to add screen details.This may occur due to duplicate entry of screen name"})


#User-Customer get the available seat info
@app.route('/customer_screens/<screen_name>/seats', methods=['GET'])
@token_required
def available_seats_row(current_user,screen_name):
    status = None
    try:
        status = request.args.get('status')
    except:
        pass
    if not status:
        num_seats = None
        choice = None
        try:
            num_seats = request.args.get('numSeats')
            choice = request.args.get('choice')
        except:
            return jsonify({"message": "Bad request", "status": 400})

        if num_seats and choice:
            try:
                num_seats = int(num_seats)
            except:
                return jsonify({"status": 400, "message": "Bad Request"})
            row_num = choice[0]
            seat_num = choice[1:]
            # Get the screen id of the screen spedified by name=screen_name
            id = Screen.query.filter_by(name=screen_name).first().id
            # Get the specified row of the screen given by the paarameter 'choice'
            row = Row.query.filter_by(id=str(id)+"_"+row_num).first()
            reserved_seats = row.reserved_seats.split("_")
            reserved_seats.remove('')
            reserved_seats = list(map(int, reserved_seats))
            aisle_seats = row.aisle_seats.split("_")
            aisle_seats = list(map(int, aisle_seats))
            aisle_seats.sort()
            rem_seats = [x for x in list(range(0, row.number_of_seats)) if x not in reserved_seats]
            if int(seat_num) in reserved_seats:
                return jsonify({"message": "Required seats not available"})

            lst = []
            i = 0
            while i < len(aisle_seats):
                l = []
                for j in rem_seats:
                    if j <= aisle_seats[i+1] and j >= aisle_seats[i]:
                        l.append(j)
                if len(l) >= num_seats:
                    lst.append(l)
                i = i+2
            if len(lst) == 0:
                return jsonify({"status": 520, "message": "Required seats not available!"})

            for l in lst:
                if int(seat_num) in l:
                    if len(l) == seat_num:
                        return jsonify({"availableSeats": {row_num: l}})
                    ind = l.index(int(seat_num))
                    if ind >= num_seats:
                        return jsonify({"availableSeats": {row_num: l[ind+1-num_seats:ind+1]}})
                    else:
                        return jsonify({"availableSeats": {row_num: l[0:num_seats]}})

            return jsonify({"message": "Required seats not available!"})

    # To get all unreserved seats at a given screen
    if status != "unreserved":
        return jsonify({"message": "Bad request", "status": 400})

    # Get the screen object from database with name=screen_name
    screen = Screen.query.filter_by(name=screen_name).first()
    id = screen.id
    # Get all the rows at the screen given by 'screen_name'
    rows = Row.query.filter(Row.id.like("%"+str(id)+"%")).all()
    result = dict()
    seats = dict()
    for row in rows:
        reserved = row.reserved_seats.split('_')
        num = row.number_of_seats
        lst = list(range(0, num))
        for item in reserved:
            try:
                lst.remove(int(item))
            except:
                None
        seats[row.id[-1]] = lst
    result["seats"] = seats
    
    # Return a list of all unreserved seats
    return jsonify(result)

# Route for reserving a ticket at a given screen
@app.route('/screens/<screen_name>/reserve', methods=['POST'])
@token_required
def customer_reserved_seats(current_user,screen_name):
    if not screen_name:
        return jsonify({"message": "Bad request", "status": 400})
    screen = Screen.query.filter_by(name=screen_name).first()
    req_seats_list = []
    seats = request.json['seats']
    
    # Check whether the required seats are available or not
    for key, value in seats.items():
        req_seats = value
        req_seats_list += value
        row_id = str(screen.id)+'_'+key
        row = Row.query.filter_by(id=row_id).first()
        reserved_seats = row.reserved_seats.split('_')
        for seat_no in req_seats:
            if str(seat_no) in reserved_seats:
                return jsonify({"status": 400,"message": "Cannot reserve specified seats!"})
                
    # Mark the reserved seats in the database
    for key, value in seats.items():
        row_id = str(screen.id) + '_' + key
        row = Row.query.filter_by(id=row_id).first()
        reserved_seats = row.reserved_seats.split('_')
        reserved_seats += value
        reserved_seats = "_".join(str(x) for x in reserved_seats)
        row.reserved_seats = reserved_seats
        db.session.commit()

    return jsonify({"status": 200, "message": "Seats successfully reserved"})

if __name__ == "__main__":
    db.create_all()
    user=User(name='admin',email='admin@yopmail.com',password=generate_password_hash('password'),is_admin=True)
    db.session.add(user)
    # db.session.commit()
    app.run('0.0.0.0',debug=True)



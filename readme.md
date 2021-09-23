*** API for movie ticket-booking authentication in Flask ***

* Create the virtual enviroment <python3 -m venv env> and activate it <source env/bin/activate>,
* install all packages by using <pip install -r requirements.tx> 

# In app.py file given all the api for post and get data
# Here , Three table models are given as User ,Screen and Row .These are showing all available user,    
# available screens data  can post by admin and and available all user row can by post raw json data in 
# body and reserved the available seats.

*** Note - Here tests.png file containing all operatutions demo picture ***

*** Token gengeration for authentication for authorize member ***

# Signup user can register self by giving name ,email and password in form-data

# Login by username and password in form-data as well as generate the token 

# Use token for authorization to post available information in json format , get the unresrved seats and 
# reserved the seats by passing json data

### sample json data for post in body and pass the x-access-token 

{
    "name": "inox",
    "seatInfo": {
        "A": {
            "numberOfSeats": 11,
            "aisleSeats": [
                0,
                5,
                6,
                9
            ]
        },
        "B": {
            "numberOfSeats": 11,
            "aisleSeats": [
                0,
                7,
                8,
                14
            ]
        },
        "C": {
            "numberOfSeats": 21,
            "aisleSeats": [
                0,
                9,
                10,
                19
            ]
        }
    }
}

### get the all data 
### Reserved the all seats by pasing below json data

{
    "seats":{
        "B":[1,2],
        "C":[6,7]
    }
}


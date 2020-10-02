import os
import requests

from flask import Flask,render_template,session,request,redirect,url_for,jsonify,abort
from cs50 import sql
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from datetime import timedelta 

# setting up a flask app
app = Flask(__name__)
app.secret_key = 'BOOKSFORLIFE'


# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

# fetch book with isbn number and return a json object with details of the book
@app.route("/api/<string:isbn>")
def json(isbn):
	result=db.execute("SELECT * FROM BOOKS WHERE isbn=:isbn",{"isbn":isbn}).fetchone()
	if result is None:
		return f"<h1>no such book available</h1>"
	count=db.execute("SELECT COUNT(*) FROM REVIEW WHERE book_id=:book_id", {"book_id":result.id}).fetchall()
	count=str(count)
	count=count[2:-3]
	average=db.execute("SELECT ROUND(AVG(rating),1) FROM REVIEW WHERE book_id=:book_id",{"book_id":result.id}).fetchall()
	average=str(average)
	average=average[11:-5]
	return jsonify({
		"title" : result.title,
		"author":result.author,
		"year" : result.year,
		"isbn" : result.isbn,
		"review_count" : count,
		"average_count" : average
		})	

# Open the page on default route
@app.route("/")
def index():
    return render_template('main.html')

# /login will take you to the login page
@app.route("/login")
def login():
    return render_template('login.html')

# /register will take you to the register page
@app.route("/register")
def register():
    return render_template('register.html')

# The route which will be called when you submit registration form
@app.route("/registering",methods=["GET","POST"])
def registering():
	if request.method=="GET":
		return f"<h>PLEASE SUBMIT THE FORM INSTEAD.<h1>"

	else:
		username=request.form.get("USERNAME")
		password=request.form.get("PASSWORD")
		# insert new User into the table
		db.execute("INSERT INTO users(username,password) VALUES(:username,:password)",{"username":username,"password":password})
		db.commit()
		return redirect(url_for("login"))

# The route which will be called when you submit login form
@app.route("/logging",methods=["GET","POST"])
def logging():
	if request.method=="GET":
		return f"<h1>PLEASE SUBMIT THE FORM INSTEAD"
	else:
		username=request.form.get("username")
		password=request.form.get("password")
		# check if the username and password match
		Check=db.execute("SELECT * FROM USERS WHERE username=:username AND password=:password",{"username":username,"password":password}).fetchone()
		if Check is None:
			return f"<h1>No such user found</h1>"
		else:
			user=username
			session["user"]=user
			return redirect(url_for("user"))

# create a session for the current user
@app.route("/user")
def user():
	if "user" in session:
		user=session["user"]
		return render_template("search.html")
	else:
		return redirect(url_for("login"))

# logout from the application
@app.route("/logout")
def logout():
	session.pop("user",None)
	return redirect(url_for("login"))				

# search any book by title , author or isbn from database using LIKE query
@app.route("/search", methods=["POST"])
def search():
	search=request.form.get("search")
	result=db.execute("SELECT * FROM BOOKS WHERE title LIKE'%"+search+"%'").fetchall()
	if len(result)<1:
		result=db.execute("SELECT * FROM BOOKS WHERE author LIKE'%"+search+"%'").fetchall()
	if len(result)<1:
		result=db.execute("SELECT * FROM BOOKS WHERE isbn LIKE'%"+search+"%'").fetchall()
	return render_template("search.html",result=result)	
		
# returning a book with particular book id from database
@app.route("/books/<int:books_id>")
def books(books_id):
	"Details about books:"
	books=db.execute("SELECT * FROM BOOKS WHERE id=:id",{"id":books_id}).fetchone()
	reviews=db.execute("SELECT * FROM REVIEW WHERE book_id=:book_id",{"book_id":books_id}).fetchall()
	res=requests.get("https://www.goodreads.com/book/review_counts.json",params={"key":"w0Rt9RAV8VOlMH5HQY4g","isbns": books.isbn})
	data=res.json()
	mybook=data["books"]
	for book in mybook:
		average_rating=book["average_rating"]
		number_of_ratings=book["work_ratings_count"]
	return render_template("books.html",books=books,reviews=reviews,a=average_rating,n=number_of_ratings)	
    
# add review for a book
@app.route("/review/<int:books_id>",methods=["POST"])
def review(books_id):
	review=request.form.get("review")
	rating=request.form.get("rating")
	user=session["user"]
	# check if current user has already submitted a review for the book
	count=db.execute("SELECT * FROM REVIEW WHERE username=:username and book_id=:book_id",{"username":user,"book_id":books_id}).fetchone()
	if count is None:
		db.execute("INSERT INTO REVIEW(username,book_id,review,rating) VALUES(:username,:book_id,:review,:rating)",{"username":user,"book_id":books_id,"review":review,"rating":rating})
		db.commit()
		books=db.execute("SELECT * FROM BOOKS WHERE id=:id",{"id":books_id}).fetchone()
		reviews=db.execute("SELECT * FROM REVIEW WHERE book_id=:book_id",{"book_id":books_id}).fetchall()
		return render_template("books.html",books=books,reviews=reviews)
	else:
		return f"<h1>Already Submitted one."

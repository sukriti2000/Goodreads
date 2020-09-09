import os
import csv
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session,sessionmaker
 
engine=create_engine(os.getenv("DATABASE_URL"))

os.getenv("DATABASE_URL")

db=scoped_session(sessionmaker(bind=engine))

def main():
 	f=open("books.csv")
 	reader=csv.reader(f)
 	for isbn,title,author,year in reader:
 	  db.execute("INSERT INTO BOOKS(ISBN,TITLE,AUTHOR,YEAR) VALUES(:ISBN,:TITLE,:AUTHOR,:YEAR)",{"ISBN":isbn,"TITLE":title,"AUTHOR":author,"YEAR":year})
 	 
 	  db.commit()
if __name__ == '__main__':
 main()
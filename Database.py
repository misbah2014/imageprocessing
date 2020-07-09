import sys
import sqlite3
import jsonpickle
from flask import Flask, request, Response, make_response
import requests
import json

class Database:
    dataBase_name = 'Data.db'

    def __init__(self):
        print('In Database class')

        pass

    def InsertStatus(self,_status): # status 0 => pending , status 1 => In process , status 2 => complete
        try:
            conn = sqlite3.connect(self.dataBase_name)
            cursor = conn.cursor()
            cursor.execute("""CREATE TABLE IF NOT EXISTS statusdb
                                           (STATUS_ID INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                                           status INTEGER
                                            )""")
            cursor.execute(""" INSERT INTO statusdb 
                                           ( status INTEGER )
                                       VALUES 
                                       (?)
                                       """, (_status))
            conn.commit()
            cursor.close()
            conn.close()
            return True

        except Exception as ex:
            print('Error in Data base: Inserting Status values {}'.format(ex))
            return False
            pass
    def UpdateStatus(self,id, _status ):
        try:
            conn = sqlite3.connect(self.dataBase_name)
            cursor = conn.cursor()
            cursor.execute(""" UPDATE statusdb SET status = ? WHERE STATUS_ID = ?
                                           
                                       """, (id, _status))
            conn.commit()
            cursor.close()
            conn.close()
            return True

        except Exception as ex:
            print('Error in Data base: Updating Status values {}'.format(ex))
            return False

    def UpdateStudent(self, _rollnumber, _customer_id, _status ):
        try:
            str_rollnumber = str(_rollnumber)
            str_customer_id = str(_customer_id)
            conn = sqlite3.connect(self.dataBase_name)
            cursor = conn.cursor()
            cursor.execute(""" UPDATE studentdb SET Status = ? WHERE  RollNumber = ? AND CustomerId = ? 
                                       """, (_status, str_rollnumber, str_customer_id))
            conn.commit()
            cursor.close()
            conn.close()
            return True
            pass
        except Exception as error:
            print('ERROR in UPDATING STUDENTSDB : {}'.format(error))
            return False
        pass

    def InsertStudent(self, roll_numbner, customer_id , _status):
        try:
            print('DATA BASE FILE : roll number = {}'.format(roll_numbner))
            str_rol_number = str(roll_numbner)
            str_id = str(customer_id)
            conn = sqlite3.connect(self.dataBase_name)
            cursor = conn.cursor()

            cursor.execute("""
                               CREATE TABLE IF NOT EXISTS studentdb
                               (STUDENT_ID INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                               RollNumber TEXT, 
                               CustomerId TEXT, 
                               Status INTEGER
                                )""")

            cursor.execute(""" INSERT INTO studentdb 
                               (RollNumber,CustomerId,Status  )
                           VALUES 
                           (?,?,?)
                           """, (str_rol_number , str_id, _status))

            conn.commit()
            cursor.close()
            conn.close()
            return True
        except Exception as ex:
            print('Error in Data base: Inserting Student Values {}'.format(ex))
            return False

    def check_id(self, _id):
        id = int(_id)
        print('checking ID')
        conn = sqlite3.connect(self.dataBase_name)
        if id < 0:
            return False
        else:
            print('checking Edit id details please wait ')

            cursor = conn.cursor()
            cursor.execute("SELECT * FROM studentdb WHERE SID = {}".format(id))
            val = cursor.fetchall()
            if len(val) >= 1:

                for x in val:
                    # print('1 - {} , 2- {} , 3- {}, 4- {} '.format(x[0], x[1], x[2], x[3]))
                    return x
            else:
                return 'Null'



    def show_users_data(self, id):
        try:
            str_id = str(id)
            record = []
            print('In show user database calling')
            conn = sqlite3.connect(self.dataBase_name)
            sql = 'SELECT RollNumber, Status from studentdb WHERE CustomerId = {}'.format(str_id)
            cur = conn.cursor()
            cur.execute(sql)
            for row in cur:
                record.append( json.dumps(row) )
            print(record)
            conn.commit()
            cur.close()
            conn.close()
            return  record
        except Exception as error:
            print('Error in fetching Users {}'.format(error))

    def fetch_new_user_id(self):
        try:
            print('In fetch_new_user_idcalling')
            db = sqlite3.connect(self.dataBase_name)
            sql = 'SELECT * from studentdb'
            cur = db.cursor()
            cur.execute(sql)
            record = cur.fetchall()
            for x in record:
                self.j = x
            db.close()
            return self.j
        except:
            print('Error in fetching Users')
            return False

    def delete_student(self, id):

        print('deleting please wait')
        conn = sqlite3.connect(self.dataBase_name)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM studentdb WHERE SID = ?", (id,))
        conn.commit()
        cursor.close()
        conn.close()
        return True

    def get_all_users(self, _id):
        str_id = str(_id)
        conn = sqlite3.connect(self.dataBase_name)
        conn.row_factory = sqlite3.Row  # This enables column access by name: row['column_name']
        db = conn.cursor()
        #SELECT to_json(result) FROM (SELECT * FROM TABLE table) result)
        rows = db.execute('''
        SELECT RollNumber, Status from studentdb WHERE CustomerId = ?
        ''', [str_id]).fetchall()

        conn.commit()
        conn.close()
        print(json.dumps([dict(ix) for ix in rows]))
        return json.dumps([dict(ix) for ix in rows])  # CREATE JSON





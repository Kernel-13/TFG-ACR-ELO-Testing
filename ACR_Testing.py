import pymysql
import datetime
import time
import ELO_Simulation

# Database connection
connection = pymysql.connect(host="localhost",user="root",passwd="",database="acr_dat")
cursor = connection.cursor()

def create_and_fill_ELO_tables():
	users = {}
	problems = {}
	problem_already_solved = []

	cursor.execute("SELECT * from submission where submissionDate >= '2015-09-01 00:00:00' and submissionDate < '2017-09-01 00:00:00'")

	for row in cursor.fetchall():
		if row[2] not in users:	users[row[2]] = 8
		if row[1] not in problems:	problems[row[1]] = 8

		if (row[2],row[1]) not in problem_already_solved:
			ELO_rating.simulate(users, problems, row[2], row[1], row[5])
			if row[5] in ('AC', 'PE'): 
				problem_already_solved.append((row[2],row[1]))

	cursor.execute("SHOW TABLES LIKE 'users_elo'")
	if cursor.fetchone():	print('Table "users_elo" already exists.')
	else: 
		cursor.execute("""CREATE TABLE IF NOT EXISTS users_elo(user_id INT PRIMARY KEY, elo_score DECIMAL(6,4))""")
		for k,v in users.items():		
			cursor.execute(f"INSERT INTO users_elo(user_id,elo_score) values({k},{v})")
			connection.commit()

	cursor.execute("SHOW TABLES LIKE 'problems_elo'")
	if cursor.fetchone():	print('Table "problems_elo" already exists.')
	else: 
		cursor.execute("""CREATE TABLE IF NOT EXISTS problems_elo(problem_id INT PRIMARY KEY, elo_score DECIMAL(6,4))""")
		for k,v in problems.items():	
			cursor.execute(f"INSERT INTO problems_elo(problem_id,elo_score) values({k},{v})")
			connection.commit()

users = {}
user_query = f"SELECT * FROM users_elo"
cursor.execute(user_query)
[users.update({k:v}) for k,v in cursor.fetchall()]

problems = {}
prob_query = f"SELECT * FROM problems_elo"
cursor.execute(prob_query)
[problems.update({k:v}) for k,v in cursor.fetchall()]

cursor.execute("""SELECT * from submission where submissionDate >= '2017-09-01 00:00:00' and submissionDate < '2018-09-01 00:00:00' AND (status='AC' OR status='PE') AND user_id in (SELECT user_id from users_elo) GROUP BY user_id having count(id)>49""")
rows = cursor.fetchall()
problem_already_tried = []

for row in rows:
	try:
		if (row[2], row[1]) not in problem_already_tried:
			print(f"User {row[2]} with ELO {users[row[2]]} tried Problem {row[1]} with ELO {problems[row[1]]}	- ELO Difference {abs(users[row[2]] - problems[row[1]])}")
			problem_already_tried.append((row[2], row[1]))
	except:
		pass

connection.close()

import math
import pymysql
import datetime
import time
import ELO_Simulation
import ACR_Stats
import matplotlib.pyplot as plt

# Database connection
connection = pymysql.connect(host="localhost",user="root",passwd="",database="acr_dat")
__cursor = connection.cursor()

def create_and_fill_ELO_table(table, row_name, dicc):
	""" Creates 2 new Tables (users_elo & problems_elo) and inserts data from the given dictionary"""
	__cursor.execute(f"SHOW TABLES LIKE '{table}'")
	if __cursor.fetchone():	print(f'Table "{table}" already exists.')
	else: 
		__cursor.execute(f"""CREATE TABLE IF NOT EXISTS {table}({row_name} INT PRIMARY KEY, elo_score DECIMAL(6,4))""")
		for k,v in dicc.items():	
			__cursor.execute(f"INSERT INTO {table}({row_name},elo_score) values({k},{v})")
			connection.commit()

def train_subjects():
	""" Selects the submissions that are going to be used for the Training Half
	Gives every user / problem an initial ELO score of 8 [ELO scores go from 0 to 16]
	Iterates over a selection of rows (Training Half) and simulates a match, which will increase/decrease the ELO score of both User and Problem involved
	Then, it will fill 2 new tables with the Users/Problems and their respective ELO score
	"""
	users = {}
	problems = {}
	problem_already_solved = []

	# The Training Half includes all submissions from September 2015 and September 2017
	__cursor.execute("SELECT * from submission where submissionDate >= '2015-09-01 00:00:00' and submissionDate < '2017-09-01 00:00:00'")

	for row in __cursor.fetchall():
		if row[2] not in users:	users[row[2]] = 8
		if row[1] not in problems:	problems[row[1]] = 8

		# We check if the problem has already been solved by one specific user
		# This is so we can omit those submissions meant to reduce exeution time, memory use, etc
		if (row[2],row[1]) not in problem_already_solved:
			ELO_Simulation.simulate(users, problems, row[2], row[1], row[5])
			if row[5] in ('AC', 'PE'): problem_already_solved.append((row[2],row[1]))


	create_and_fill_ELO_table('problems_elo', 'problem_id', problems)
	create_and_fill_ELO_table('users_elo', 'user_id', users)

def main():
	train_subjects()
	ACR_Stats.print_submissions_per_months()
	ACR_Stats.print_elo_distribution('users_elo', 'Users')
	ACR_Stats.print_elo_distribution('problems_elo', 'Problems')
	ACR_Stats.connection.close()
	connection.close()


if __name__== "__main__":
	main()
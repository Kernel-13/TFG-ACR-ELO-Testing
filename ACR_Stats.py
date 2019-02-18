import math
import pymysql
import matplotlib.pyplot as plt

# Database connection
connection = pymysql.connect(host="localhost",user="root",passwd="",database="acr_dat")
__cursor = connection.cursor()


def print_submissions_per_months():

	months = {}
	[months.update({k:0}) for k in range(1,13)]
	__cursor.execute("""SELECT * from submission order by submissionDate asc""")
	for r in __cursor.fetchall():
		months[int(str(r[-1]).split('-')[1])] += 1

	month = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
	values = []
	print("\nNº of Submissions Per Month")

	for k,v in months.items(): 
		print(f"Month {k} :	{v}")
		values.append(v)

	plt.bar(month, values)
	plt.ylabel("Nº of Submissions")
	plt.xlabel("Months")
	plt.suptitle("Nº of Submissions Per Month")
	plt.show()

def print_elo_differences():
	
	__cursor.execute("""SELECT * from submission where submissionDate >= '2017-09-01 00:00:00' and submissionDate < '2018-09-01 00:00:00' AND user_id in (SELECT user_id from users_elo natural join 
	(SELECT user_id from submission where submissionDate >= '2017-09-01 00:00:00' and submissionDate < '2018-09-01 00:00:00' group by user_id having count(id) >= 50) as active_users) 
	AND (status='AC' OR status='PE') order by user_id,problem_id,submissionDate""")

	rows = __cursor.fetchall()
	problem_already_solved = []
	elo_diff = []

	users = {}
	__cursor.execute("SELECT * FROM users_elo")
	[users.update({k:v}) for k,v in __cursor.fetchall()]

	problems = {}
	__cursor.execute("SELECT * FROM problems_elo")
	[problems.update({k:v}) for k,v in __cursor.fetchall()]

	elo_diff = {}
	[elo_diff.update({k:0}) for k in range(16)]

	for row in rows:
		try:
			if (row[2], row[1]) not in problem_already_solved:
				#print(f"User {row[2]} with ELO {users[row[2]]} tried Problem {row[1]} with ELO {problems[row[1]]}	- ELO Difference {abs(users[row[2]] - problems[row[1]])}_	- Status: {row[5]}")
				problem_already_solved.append((row[2], row[1]))
				if math.floor(abs(users[row[2]] - problems[row[1]])) == 16: elo_diff[15] += 1
				else: elo_diff[math.floor(abs(users[row[2]] - problems[row[1]]))] += 1
		except:
			pass

	ranges = []
	values = []
	print("\nELO Differences")

	for k,v in elo_diff.items(): 
		print(f"Range [{k} - {k+1}]   :	{v}")
		ranges.append(f"[{k} - {k+1}]")
		values.append(v)

	plt.bar(ranges, values)
	plt.ylabel("Nº of Submissions with Status AC or PE")
	plt.xlabel("ELO Ranges")
	plt.suptitle('ELO Differences between Users and the Problems they solved')
	plt.show()

def print_elo_distribution(table, items):
	u_elo = {}
	[u_elo.update({k:0}) for k in range(16)]
	__cursor.execute(f"SELECT elo_score FROM {table}")
	for r in __cursor.fetchall():
		if r[0] != 16: u_elo[math.floor(r[0])] += 1 
		else: u_elo[15] += 1

	ranges = []
	values = []
	print(f"\nELO Distribution ({items})")

	for k,v in u_elo.items(): 
		print(f"Range [{k} - {k+1}]   :	{v}")
		ranges.append(f"[{k} - {k+1}]")
		values.append(v)

	plt.bar(ranges, values)
	plt.ylabel(f"Nº of {items}")
	plt.xlabel("ELO Ranges")
	plt.suptitle(f'ELO Distribution ({items})')
	plt.show()

def print_tries_average():
	n_submissions = 0
	u_elo = {}
	[u_elo.update({k:0}) for k in range(16)]
	__cursor.execute("""SELECT distinct(user_id), count(id), elo_score from submission natural join users_elo group by user_id""")

	rows = __cursor.fetchall()
	for r in rows:
		if r[2] != 16: u_elo[math.floor(r[2])] += 1 
		else: u_elo[15] += 1
		n_submissions += r[1]

	print("Nº of Users: ", len(rows))
	print("Nº of Submissions: ", n_submissions)
	print("Average: ", n_submissions/len(rows))

def print_users_elo():
	__cursor.execute("""SELECT * from users_elo order by elo_score""")
	for r in __cursor.fetchall():
		print("ELO: ", r[1], "	- User: ", r[0])
		
def print_problems_elo():
	__cursor.execute("""SELECT * from problems_elo order by elo_score asc """)
	for r in __cursor.fetchall():
		print("ELO: ", r[1], "	- Problem: ", r[0])

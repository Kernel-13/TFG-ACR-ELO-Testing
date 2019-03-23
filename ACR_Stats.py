import math
import pymysql
import matplotlib
import matplotlib.pyplot as plt
matplotlib.style.use('ggplot')

def print_submissions_per_months(__cursor):

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

	show_bar_plot(month,values,x_label="Months", y_label="Nº of Submissions", title="Nº of Submissions Per Month")

def print_elo_differences(__cursor, kind='perc'):
	
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

	value_sum = sum([v for k,v in elo_diff.items()])
	perc_sum = 0

	print("\nELO Differences between Users and the Problems they solved")
	for k,v in elo_diff.items(): 
		print(f"Range [{k} - {k+1})   :	{v}		-	Percentage: {(v/value_sum)*100}%")

		if kind == 'sum':
			perc_sum += (v/value_sum)*100
			ranges.append(f"[0 - {k+1})")
			values.append(perc_sum)
		else:
			ranges.append(f"[{k} - {k+1})")
			if kind == 'numb': values.append(v)
			else: values.append((v/value_sum)*100)

	show_bar_plot(ranges,values,x_label="ELO Difference (Ranges)", y_label="Submissions with Status AC or PE", title="ELO Differences between Users and the Problems they solved")

def print_elo_distribution(__cursor, items):
	elo_scores = {}
	[elo_scores.update({k:0}) for k in range(16)]

	field = 'user_id' if items=='Users' else 'problem_id'

	#__cursor.execute(f"SELECT * FROM submission WHERE submissionDate >= '2015-09-01 00:00:00' AND submissionDate < '2017-09-01 00:00:00' AND problem_elo IS NOT NULL AND user_elo IS NOT NULL AND id IN (SELECT MAX(id) FROM submission WHERE submissionDate >= '2015-09-01 00:00:00' AND submissionDate < '2017-09-01 00:00:00' GROUP BY {field})")

	__cursor.execute(f"""SELECT {field} FROM submission WHERE submissionDate >= '2015-09-01 00:00:00' AND submissionDate < '2017-09-01 00:00:00' GROUP BY {field}""")
	rows = __cursor.fetchall()

	for row in rows:
		__cursor.execute(f"""SELECT * FROM submission WHERE submissionDate >= '2015-09-01 00:00:00' AND submissionDate < '2017-09-01 00:00:00' 
			AND {field}={row[0]} AND problem_elo IS NOT NULL AND user_elo IS NOT NULL ORDER BY id DESC LIMIT 1""")
		r = __cursor.fetchall()

		ELO = r[0][7] if items=='Users' else r[0][8]
		
		if ELO != 16: elo_scores[math.floor(ELO)] += 1 
		else: elo_scores[15] += 1

	ranges = []
	values = []
	print(f"\nELO Distribution ({items})")

	for k,v in elo_scores.items(): 
		print(f"Range [{k} - {k+1}]   :	{v}")
		ranges.append(f"[{k} - {k+1})")
		values.append(v)

	show_bar_plot(ranges,values,x_label="ELO Ranges", y_label=f"Nº of {items}", title=f"ELO Distribution ({items})")

def print_tries_average(__cursor):
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

def print_tries_till_solved(__cursor):
	__cursor.execute("""SELECT * from submission where submissionDate >= '2015-09-01 00:00:00' and submissionDate < '2017-09-01 00:00:00' 
		AND user_elo IS NOT NULL ORDER BY user_id, problem_id, submissionDate""")

	num_subm = {}
	for i in range(1,21): num_subm[str(i)] = 0
	num_subm['20+'] = 0

	problem_already_solved = []
	previous_tuple = (-1,-1)
	tries = 0

	for row in __cursor.fetchall():
		if (row[2],row[1]) not in problem_already_solved:
			tries += 1
			if (row[2],row[1]) != previous_tuple: 
				previous_tuple = (row[2],row[1])
				tries = 1
			if row[5] in ('AC', 'PE'):
				problem_already_solved.append((row[2],row[1]))
				if tries < 21:  num_subm[str(tries)] += 1
				else: num_subm['20+'] += 1
				tries = 0

	x = []
	y = []
	for k,v in num_subm.items():
		x.append(k)
		y.append(v)

	show_bar_plot(x,y, x_label="Nº of Tries (Submissions) until the problem is solved", y_label="Nº of Distinct User/Problem Confrontations", title="")

def show_bar_plot(x,y,x_label="", y_label="", title=""):
	x_idx = [i for i, _ in enumerate(x)]
	_, ax = plt.subplots()
	bars = ax.bar(x_idx, y, color='b')
	plt.xlabel(x_label)
	plt.ylabel(y_label)
	plt.suptitle(title)
	plt.xticks(x_idx, x)

	for bar in bars:
	    height = bar.get_height()
	    ax.text(bar.get_x() + bar.get_width()/2., 1.05*height,str(round(height, 2)),ha='center', va='bottom')

	plt.show()

def show_spider_chart(chart_data, title=""):
	categories = []
	values = []
	for k,v in chart_data.items():
		categories.append(k)
		values.append(v)

	angles = [n / float(len(categories)) * 2 * math.pi for n in range(len(categories))]
	ax = plt.subplot(111, polar=True)
	plt.xticks(angles, categories, color='grey', size=8)
	
	ax.set_rlabel_position(0)
	plt.yticks([4,8,12], ["4","8","12"], color="grey", size=7)
	plt.ylim(0,16)

	for idx, v in enumerate(angles):
		position = (v,values[idx]+1) if values[idx] <= 14 else (v,values[idx]-1.3)
		plt.text(v, values[idx], str(values[idx]), color="black", size=12 ,ha='center', va='center', alpha=0.5, position=position)

	# We add the first value again so the plot draws all lines 
	# Otherwise, the line connecting the first & last value wont get drawn
	angles.append(angles[0])
	values.append(values[0])

	ax.plot(angles, values, 'o-', linewidth=1)
	ax.fill(angles, values, 'b', alpha=0.5)
	plt.show()

def show_line_plot(x,y,filename):
	fig, ax = plt.subplots()
	ax.plot(x,y,'ro-')
	ax.grid()
	axes = plt.gca()
	axes.set_ylim([0,16])
	for idx, v in enumerate(x):
		position = (v,float(y[idx])+0.5) if y[idx] < 16 else (v,100)
		plt.text(v, y[idx], str(y[idx]), color="black", size=12 ,ha='center', va='center', alpha=0.5, position=position)
	fig.set_size_inches(12, 10)
	fig.savefig(filename)
	plt.close(fig)
	#plt.show()

'''
__cursor.execute("""SELECT * from submission s inner join problems_elo p on s.problem_id = p.problem_id  inner join users_elo u on s.user_id = u.user_id
	where s.submissionDate >= '2017-09-01 00:00:00' and s.submissionDate < '2018-09-01 00:00:00' AND s.user_id in 
	(SELECT user_id from submission where submissionDate >= '2017-09-01 00:00:00' and submissionDate < '2018-09-01 00:00:00' group by user_id having count(id) >= 50) 
	AND (s.status='AC' OR s.status='PE') group by s.user_id, s.problem_id, s.status order by s.user_id""")

__cursor.execute("""SELECT * from submission s inner join problems_elo p on s.problem_id = p.problem_id  inner join users_elo u on s.user_id = u.user_id
	where s.submissionDate >= '2017-09-01 00:00:00' and s.submissionDate < '2018-09-01 00:00:00' AND s.user_id in 
	(SELECT user_id from submission where submissionDate >= '2017-09-01 00:00:00' and submissionDate < '2018-09-01 00:00:00' group by user_id having count(id) >= 50) 
	AND (s.status='AC' OR s.status='PE') group by s.user_id, s.problem_id, s.status""")

__cursor.execute("""SELECT * from submission s inner join problems_elo p on s.problem_id = p.problem_id 
	where s.submissionDate >= '2017-09-01 00:00:00' and s.submissionDate < '2018-09-01 00:00:00' AND s.user_id in (SELECT user_id from users_elo natural join 
	(SELECT user_id from submission where submissionDate >= '2017-09-01 00:00:00' and submissionDate < '2018-09-01 00:00:00' group by user_id having count(id) >= 50) as active_users) 
	AND (s.status='AC' OR s.status='PE') group by user_id, s.problem_id, s.status""")

__cursor.execute(""" SELECT distinct s.user_id as u_id FROM submission s 
	inner join users_elo u on s.user_id = u.user_id
	inner join problems_elo p on s.problem_id = p.problem_id
	where s.submissionDate >= '2017-09-01 00:00:00' and s.submissionDate < '2018-09-01 00:00:00'
	AND (s.status='AC' OR s.status='PE')
	GROUP BY u_id
	HAVING count(id) >= 50""")

__cursor.execute("""SELECT DISTINCT user_id
	 from submission natural join problems_elo natural join users_elo 
	 where submissionDate >= '2017-09-01 00:00:00' and submissionDate < '2018-09-01 00:00:00' AND user_id in 
	 (SELECT user_id from submission where submissionDate >= '2017-09-01 00:00:00' and submissionDate < '2018-09-01 00:00:00' group by user_id having count(id) >= 50)
	  AND (status='AC' OR status='PE') group by user_id""")

__cursor.execute(""" SELECT s.user_id as u_id, s.problem_id as s_id, u.elo_score as u_score, p.elo_score as u_score FROM submission s 
	inner join users_elo u on s.user_id = u.user_id
	inner join problems_elo p on s.problem_id = p.problem_id
	where s.submissionDate >= '2017-09-01 00:00:00' and s.submissionDate < '2018-09-01 00:00:00'
	AND (s.status='AC' OR s.status='PE')
	GROUP BY u_id, s_id, s.status""")

__cursor.execute(""" SELECT s.user_id as u_id, s.problem_id as s_id, u.elo_score as u_score, p.elo_score as p_score FROM users_elo u
	INNER JOIN (SELECT user_id from submission where submissionDate >= '2017-09-01 00:00:00' and submissionDate < '2018-09-01 00:00:00'	group by user_id having count(id) >= 50) as s on s.user_id = u.user_id
	INNER JOIN problems_elo p on s.problem_id = p.problem_id
	WHERE s.submissionDate >= '2017-09-01 00:00:00' and s.submissionDate < '2018-09-01 00:00:00' 
	AND (s.status='AC' OR s.status='PE')
	order by s.user_id,s.problem_id,s.submissionDate """)

__cursor.execute(""" SELECT submission.user_id, submission.problem_id, users_elo.elo_score as u_score, problems_elo.elo_score as p_score FROM users_elo u
	INNER JOIN submission on submission.user_id = users_elo.user_id
	INNER JOIN problems_elo on submission.problem_id = problems_elo.problem_id
	WHERE submission.submissionDate >= '2017-09-01 00:00:00' and submission.submissionDate < '2018-09-01 00:00:00' 
	AND (submission.status='AC' OR submission.status='PE')""")

'''
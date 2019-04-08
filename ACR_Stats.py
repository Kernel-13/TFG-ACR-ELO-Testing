import math
import pymysql
import ACR_Globals
import matplotlib
import matplotlib.pyplot as plt
matplotlib.style.use('ggplot')

def print_submissions_per_months():

	months = {}
	[months.update({k:0}) for k in range(1,13)]
	ACR_Globals.__CURSOR.execute("""SELECT * from submission order by submissionDate asc""")
	for r in ACR_Globals.__CURSOR.fetchall():
		months[int(str(r[-1]).split('-')[1])] += 1

	month = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
	values = []
	print("\nNº of Submissions Per Month")

	for k,v in months.items(): 
		print(f"Month {k} :	{v}")
		values.append(v)

	show_bar_plot(month,values,x_label="Months", y_label="Nº of Submissions", title="Nº of Submissions Per Month")

def print_elo_differences():
	
	elo_diff = {}
	[elo_diff.update({k:0}) for k in range(16)]

	# We get the user/problem couples
	ACR_Globals.__CURSOR.execute("""SELECT user_id, problem_id FROM submission 
		WHERE id <= {}
		AND (status='AC' OR status='PE')
		GROUP BY user_id, problem_id
		ORDER BY id""".format(ACR_Globals.__DB_SPLITTER))
	
	for row in ACR_Globals.__CURSOR.fetchall():
		usr = row[0]
		prb = row[1]
		
		ACR_Globals.__CURSOR.execute("SELECT elo_global FROM user_scores WHERE user_id = {}".format(usr))
		usr_elo = ACR_Globals.__CURSOR.fetchone()[0]

		ACR_Globals.__CURSOR.execute("SELECT elo_global FROM problem_scores WHERE problem_id = {}".format(prb))
		prb_elo = ACR_Globals.__CURSOR.fetchone()[0]

		if math.floor(abs(usr_elo - prb_elo)) == 16: 
			elo_diff[15] += 1
		else: 
			elo_diff[math.floor(abs(usr_elo - prb_elo))] += 1

	ranges = []
	values = []

	value_sum = sum([v for k,v in elo_diff.items()])
	for k,v in elo_diff.items(): 
		ranges.append(f"[{k} - {k+1})")
		values.append((v/value_sum)*100)

	show_bar_plot(ranges,values,x_label="ELO Difference (Ranges)", y_label="Submissions with Status AC or PE", title="ELO Differences between Users and the Problems they solved")

def print_actual_elo_distribution(items):
	elo_scores = {}
	[elo_scores.update({k:0}) for k in range(16)]

	field = 'user_scores' if items=='Users' else 'problem_scores'

	ACR_Globals.__CURSOR.execute(f"""SELECT elo_global FROM {field} WHERE elo_global != 8.0""")
	rows = ACR_Globals.__CURSOR.fetchall()

	for row in rows:
		if row[0] != 16: 
			elo_scores[math.floor(row[0])] += 1 
		else: 
			elo_scores[15] += 1

	ranges = []
	values = []
	value_sum = sum([v for k,v in elo_scores.items()])

	for k,v in elo_scores.items(): 
		ranges.append(f"[{k} - {k+1})")
		values.append((v/value_sum)*100)

	show_bar_plot(ranges,values,x_label="ELO Ranges", y_label=f"Nº of {items}", title=f"ELO Distribution ({items})")

def print_elo_distribution(items, start_date, end_date):
	elo_scores = {}
	[elo_scores.update({k:0}) for k in range(16)]

	field = 'user_id' if items=='Users' else 'problem_id'

	ACR_Globals.__CURSOR.execute(f"""SELECT {field} FROM submission WHERE submissionDate >= '{start_date}' AND submissionDate < '{end_date}' GROUP BY {field}""")
	rows = ACR_Globals.__CURSOR.fetchall()

	for row in rows:

		ACR_Globals.__CURSOR.execute(f"""SELECT * FROM submission 
			WHERE submissionDate >= '{start_date}'
			AND submissionDate < '{end_date}'
			AND {field}={row[0]} 
			AND problem_elo IS NOT NULL 
			AND user_elo IS NOT NULL 
			ORDER BY id DESC 
			LIMIT 1""")

		r = ACR_Globals.__CURSOR.fetchall()
		try:
			ELO = r[0][7] if items=='Users' else r[0][8]
			if ELO != 16: 
				elo_scores[math.floor(ELO)] += 1 
			else: 
				elo_scores[15] += 1
		except:
			# User #1952:  second-to-last submission on 2016-12-19 / last submission on 2018-05-16
			pass

	ranges = []
	values = []
	print(f"\nELO Distribution ({items})")

	for k,v in elo_scores.items(): 
		#print(f"Range [{k} - {k+1}]   :	{v}")
		ranges.append(f"[{k} - {k+1})")
		values.append(v)

	show_bar_plot(ranges,values,x_label="ELO Ranges", y_label=f"Nº of {items}", title=f"ELO Distribution ({items})")

def print_tries_till_solved(start_date, end_date):
	ACR_Globals.__CURSOR.execute(f"""SELECT * from submission 
		WHERE submissionDate >= '{start_date}' 
		AND submissionDate < '{end_date}' 
		AND user_elo IS NOT NULL 
		ORDER BY user_id, problem_id, submissionDate""")

	num_subm = {}
	for i in range(1,21): num_subm[str(i)] = 0
	num_subm['20+'] = 0

	problem_already_solved = []
	previous_tuple = (-1,-1)
	tries = 0

	for row in ACR_Globals.__CURSOR.fetchall():
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

def print_tries_average(start_date, end_date):
	ACR_Globals.__CURSOR.execute(f"""SELECT user_id, SUM(CASE WHEN status='AC' THEN 1 ELSE 0 END), SUM(CASE WHEN status!='AC' THEN 1 ELSE 0 END) from submission 
		WHERE submissionDate >= '{start_date}' 
		AND submissionDate < '{end_date}' 
		GROUP BY user_id""")

	num_subm = {}
	for i in range(21): num_subm[str(i)] = 0
	num_subm['20+'] = 0
	num_subm['NS'] = 0

	for row in ACR_Globals.__CURSOR.fetchall():
		if row[1] != 0:
			average = math.floor(row[2] / row[1])
			if average < 21:  num_subm[str(average)] += 1
			else: num_subm['20+'] += 1
		else:
			num_subm['NS'] += 1
	x = []
	y1 = []
	y2 = []
	for k,v in num_subm.items():
		x.append(k)
		y1.append(v)

	perc_sum = 0
	for i in y1:
		perc_sum += i
		y2.append((perc_sum/sum(y1))*100)

	ACR_Stats.show_bar_and_cumulative(x,y1,y2, x_label="Nº of AC / NON_AC Submissions", y_label="Nº of Users", title="")

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
	    ax.text(bar.get_x() + bar.get_width()/2., 1.05*height,str(round(height, 2))+'%',ha='center', va='bottom')

	plt.show()
	plt.close()

def show_spider_chart(chart_data, filename, title=""):
	categories = []
	values = []
	for k,v in chart_data.items():
		categories.append(k)
		values.append(v)

	angles = [n / float(len(categories)) * 2 * math.pi for n in range(len(categories))]
	ax = plt.subplot(111, polar=True)
	plt.xticks(angles, categories, color='grey', size=12)
	
	ax.set_rlabel_position(0)
	plt.yticks([4,8,12], ["4","8","12"], color="grey", size=7)
	plt.ylim(0,16)

	for idx, v in enumerate(angles):
		position = (v,values[idx]+1.5) if values[idx] <= 10 else (v,values[idx]-1.8)
		str_value = str(round(values[idx],3)) if values[idx] != 8.0 else "Not\nAttempted"
		plt.text(v, values[idx], str_value, fontweight='bold', color="black", size=11 ,ha='center', va='center', alpha=0.5, position=position)

	# We add the first value again so the plot draws all lines 
	# Otherwise, the line connecting the first & last value wont get drawn
	angles.append(angles[0])
	values.append(values[0])

	ax.plot(angles, values, 'o-', linewidth=1)
	ax.fill(angles, values, 'r', alpha=0.5)

	fig = plt.gcf()
	fig.set_size_inches(9,9)
	plt.savefig(filename)
	plt.close()
	#plt.show()

def show_line_plot(x,y,filename, x_label="", y_label="", title=""):
	fig, ax = plt.subplots()
	ax.plot(x,y,'ro-')
	ax.grid()
	axes = plt.gca()
	axes.set_ylim([0,16])

	position = (x[len(x)-1],float(y[len(y)-1])+0.5) if y[len(y)-1] < 16 else (x[len(x)-1],100)
	plt.text(x[len(x)-1], y[len(y)-1], str(round(y[len(y)-1],2)), color="black", size=12 ,ha='center', va='center', alpha=0.5, position=position)

	"""
	for idx, v in enumerate(x):
		position = (v,float(y[idx])+0.5) if y[idx] < 16 else (v,100)
		plt.text(v, y[idx], str(round(y[idx],2)), color="black", size=12 ,ha='center', va='center', alpha=0.5, position=position)
	"""
	fig.set_size_inches(12, 10)
	fig.savefig(filename)
	plt.close()
	#plt.show()

def show_scatter(x,y,label, x_label="", y_label="", title=""):
	fig, ax1 = plt.subplots()

	ax1.set_xlabel(x_label)
	ax1.set_ylabel(y_label)

	color = 'tab:red'
	ax1.scatter(x, y, color=color, label=label)

	axes = plt.gca()
	axes.set_xlim([-16,16])
	axes.set_ylim([-5,5])

	fig.set_size_inches(18, 15)
	ax1.legend(loc="best")
	fig.savefig(f"whatever_{label}.png")
	plt.close()

	#fig.set_size_inches(180, 150)
	#fig.savefig(f"whatever_big_{label}.png")

def show_ELO_gain(x,y1,y2,x_label="", y_label="", title="", filename="Gain"):
	# Code from https://matplotlib.org/gallery/subplots_axes_and_figures/two_scales.html
	fig, ax1 = plt.subplots()

	ax1.set_xlabel(x_label)
	ax1.set_ylabel(y_label)

	color = 'tab:red'
	ax1.scatter(x, y1, color=color, label="User Gain")

	ax2 = ax1.twinx()  # instantiate a second axes that shares the same x-axis
	color = 'tab:blue'
	ax2.scatter(x, y2, color=color, label="Problem Gain")

	axes = plt.gca()
	axes.set_xlim([-16,16])
	ax1.set_ylim([-1,1])
	ax2.set_ylim([-1,1])

	fig.set_size_inches(18, 15)
	ax1.legend(loc="upper left")
	ax2.legend(loc="upper right")
	fig.savefig(filename)


	#fig.set_size_inches(36, 30)
	#fig.savefig("Bigger " + filename)
	plt.close()
	#plt.show()

def show_bar_and_cumulative(x,y1,y2,x_label="", y_label="", title="", filename="show_bar_and_cumulative.png"):
	# Code from https://matplotlib.org/gallery/subplots_axes_and_figures/two_scales.html
	fig, ax1 = plt.subplots()

	ax1.set_xlabel(x_label)
	ax1.set_ylabel(y_label)

	color = 'tab:blue'
	bars = ax1.bar(x, y1, color=color, label="Nº of Users")

	for bar in bars:
	    height = bar.get_height()
	    ax1.text(bar.get_x() + bar.get_width()/2., 1.05*height,str(round(height, 2)),ha='center', va='bottom')

	ax2 = ax1.twinx()  # instantiate a second axes that shares the same x-axis
	color = 'tab:red'
	plts = ax2.plot(x, y2, color=color, label="Cumulative Percentage")

	for idx, v in enumerate(x):
		ax2.text(v, y2[idx], str(round(y2[idx],1))+'%', color="black", size=8 ,ha='center', va='center', alpha=0.8, position=(v,float(y2[idx])+3.5))

	ax2.set_ylim([0,100])

	#fig.set_size_inches(15, 10)
	#ax1.legend(loc="upper left")
	#ax2.legend(loc="upper right")
	#fig.savefig(filename)


	#fig.set_size_inches(36, 30)
	#fig.savefig("Bigger " + filename)
	plt.show()
	plt.close()

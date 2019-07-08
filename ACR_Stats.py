import ELO
import os
import math
import pymysql
import ACR_Globals
import matplotlib
import matplotlib.pyplot as plt
matplotlib.style.use('ggplot')

def GRAPH_ELO_DISTRIBUTION(items):
	elo_scores = {}
	[elo_scores.update({k:0}) for k in range(16)]

	ACR_Globals.__CURSOR.execute("""SELECT elo_global FROM {} 
		WHERE elo_global != 8.0""".format('user_scores' if items=='Users' else 'problem_scores'))

	for row in ACR_Globals.__CURSOR.fetchall():
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

	BAR_PLOT(ranges,values,x_label="ELO Ranges", y_label=f"Nº of {items}", title=f"ELO Distribution ({items})")

def GRAPH_ELO_DIFFERENCES(sign):
	
	elo_diff = {}
	[elo_diff.update({k:0}) for k in range(16)]

	# We get the user/problem couples
	ACR_Globals.__CURSOR.execute("""SELECT user_id, problem_id FROM submission 
		WHERE id {} {}
		AND (status='AC' OR status='PE')
		GROUP BY user_id, problem_id
		ORDER BY id""".format(sign, ACR_Globals.__DB_SPLITTER))
	
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

	BAR_PLOT(ranges,values,x_label="ELO Difference (Ranges)", y_label="Submissions with Status AC or PE", title="ELO Differences between Users and the Problems they solved")

def GRAPH_TRIES_AVERAGE():
	ACR_Globals.__CURSOR.execute("""SELECT user_id, problem_id, SUM(CASE 
		WHEN status = 'AC' THEN 1 
		WHEN status = 'PE' THEN 1 
		ELSE 0 END), COUNT(id) 
		FROM submission 
		GROUP BY user_id, problem_id""")

	num_subm = {}
	for i in range(1,21): num_subm[str(i)] = 0
	num_subm['+ de 20'] = 0

	for row in ACR_Globals.__CURSOR.fetchall():
		if row[2] != 0:
			if row[3] < 21:  
				num_subm[str(row[3])] += 1
			else: 
				num_subm['+ de 20'] += 1

	x = []
	y0 = []
	y2 = []
	for k,v in num_subm.items():
		x.append(k)
		y0.append(v)

	y1 = [(i/sum(y0))*100 for i in y0]

	perc_sum = 0
	for i in y1:
		perc_sum += i
		y2.append((perc_sum/sum(y1))*100)

	BAR_AND_CUMULATIVE_PLOT(x,y1,y2, x_label="Nº de Intentos", y_label="% de Usuarios", title="")

def GRAPH_AVERAGE_SOLVED():
	ACR_Globals.__CURSOR.execute("""SELECT user_id, SUM(CASE 
		WHEN status = 'AC' THEN 1 
		WHEN status = 'PE' THEN 1 
		ELSE 0 END) FROM submission GROUP BY user_id""")

	tmp = {}
	for row in ACR_Globals.__CURSOR.fetchall():
		if row[1] not in tmp:
			tmp[row[1]] = 1
		else:
			tmp[row[1]] += 1

	tmp[1000] = 0
	x = []
	y = []

	for k,v in tmp.items():
		if k <= 20 :
			x.append(k)
		else :
			tmp[1000] += 1

	x.sort()
	for i in x:
		y.append(tmp[i])

	x.append('+20')
	y.append(tmp[1000])
	y = [(i/sum(y))*100 for i in y]
	BAR_PLOT(x,y,x_label="Nº of Problems Solved", y_label="Nº of Users", title="")

def GRAPH_EXPECTATION_DIFF():
	elo_test = [16,8,0]
	elos = []
	expects = []
	cnt = 0
	while cnt <= 15:
		for i in range(10):
			elos.append(round(cnt+i*0.1,1))
		cnt += 1
	elos.append(16)

	for i,t in enumerate(elo_test):
		for e in elos:
			expects.append(ELO.EXPECTATION(t,e))

		LINE_PLOT(elos,expects,f"Expectation (ELO {t}).svg",x_label="Problem ELO", y_label="Expectation", title=f"Expectation for a user with ELO {t}", ylim_down=0, ylim_up=1, plot_type=i+1)
		expects = []

def GRAPH_SUBMISSIONS_PER_MONTHS():
	months = {}
	[months.update({k:0}) for k in range(1,13)]
	ACR_Globals.__CURSOR.execute("""SELECT * FROM submission ORDER BY submissionDate ASC""")
	for r in ACR_Globals.__CURSOR.fetchall():
		months[int(str(r[-1]).split('-')[1])] += 1

	month = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
	values = []

	for k,v in months.items(): values.append(v)
	BAR_PLOT(month,values,x_label="Months", y_label="Nº of Submissions", title="Nº of Submissions Per Month")

def GRAPH_USERS_EVOLUTION():
	if not os.path.exists("Users' ELO History"):
		os.makedirs("Users' ELO History")

	ACR_Globals.__CURSOR.execute("""SELECT user_id, count(id) FROM submission 
		WHERE id <= {}
		AND user_elo IS NOT NULL 
		AND user_id in {}
		GROUP BY user_id 
		ORDER BY user_id""".format(ACR_Globals.__DB_SPLITTER, str(ACR_Globals.__USRS_CHKD)))
	
	for usr in [r[0] for r in ACR_Globals.__CURSOR.fetchall()]:
		ACR_Globals.__CURSOR.execute("""SELECT * FROM submission 
		WHERE user_id = {}
		AND user_elo IS NOT NULL 
		ORDER BY id""".format(usr))
		
		y = [x[7] for x in ACR_Globals.__CURSOR.fetchall()]
		y.insert(0,8)

		LINE_PLOT(range(len(y)), y,f"Users' ELO History\\User({str(usr)})Evolution.svg",
			x_label="Nº de Enfrentamientos", y_label="Puntuación ELO", title=f"Evolución Usuario # {str(usr)}")
		break

def GRAPH_PROBLEMS_EVOLUTION():
	if not os.path.exists("Problems' ELO History"):
		os.makedirs("Problems' ELO History")

	ACR_Globals.__CURSOR.execute("""SELECT problem_id, count(id) FROM submission 
		WHERE id <= {}
		AND problem_id in {} 
		AND problem_elo IS NOT NULL 
		GROUP BY problem_id 
		ORDER BY problem_id""".format(ACR_Globals.__DB_SPLITTER, str(ACR_Globals.__PRBS_CHKD)))

	for prob in [r[0] for r in ACR_Globals.__CURSOR.fetchall()]:

		ACR_Globals.__CURSOR.execute("""SELECT * FROM submission 
			WHERE id <= {}
			AND problem_id = {}
			AND problem_elo IS NOT NULL 
			ORDER BY id""".format(ACR_Globals.__DB_SPLITTER, prob))

		y = [x[8] for x in ACR_Globals.__CURSOR.fetchall()]
		y.insert(0,8)

		LINE_PLOT(range(len(y)), y,f"Problems' ELO History\\Problem({str(prob)})Evolution.svg",
			x_label="Nº de Enfrentamientos", y_label="Puntuación ELO", title=f"Evolución Problema # {str(usr)}")

def GRAPH_USER_CATEGORIES():
	if not os.path.exists("Categories' ELO"):
		os.makedirs("Categories' ELO")

	ACR_Globals.__CURSOR.execute("""SELECT * FROM User_Scores WHERE user_id in {}""".format(str(ACR_Globals.__USRS_CHKD)))

	for row in ACR_Globals.__CURSOR.fetchall():
		categories_data = {
			'Ad-hoc': row[2],
			'Recorridos': row[3],
			'Búsqueda': row[4],
			'Búsqueda\n Binaria': row[5],
			'Ordenación': row[6],
			'Algoritmos\n voraces': row[7],
			'Programación\n dinámica': row[8],
			'Divide y\n vencerás': row[9],
			'Búsqueda exhaustiva,\n vuelta atrás': row[10],
			'Búsqueda en el espacio\n de soluciones': row[11],
			'Grafos': row[12],
			'Geometría': row[13]
		}
		SPIDER_CHART(chart_data=categories_data,filename=f"Categories' ELO\\User {str(row[0])} Categories.svg")
		break

def GRAPH_ELO_GAIN(x,y1,y2,x_label="", y_label="", title="", filename="GAIN.svg"):
	# Code from https://matplotlib.org/gallery/subplots_axes_and_figures/two_scales.html
	fig, ax1 = plt.subplots()

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

	plt.xlabel(x_label)
	plt.ylabel(y_label)
	plt.suptitle(title)

	fig.savefig(filename, format="svg")
	plt.close()

# User / Problem Distribution with no padding OK 
# Ready to save to file
def BAR_PLOT(x,y,x_label="", y_label="", title=""):
	x_idx = [i for i, _ in enumerate(x)]
	fig, ax = plt.subplots()

	bars = ax.bar(x_idx, y, color='b')
	plt.xlabel(x_label)
	plt.ylabel(y_label)
	plt.suptitle(title)
	plt.xticks(x_idx, x)

	for bar in bars:
		height = bar.get_height()
		ax.text(bar.get_x() + bar.get_width()/2., 1.0*height,str(round(height, 2))+'%', size=14,ha='center', va='bottom')

	fig.set_size_inches(15, 8)
	plt.subplots_adjust(left=0.045, right=0.97, top=0.96, bottom=0.06)
	plt.show()
	plt.close()

# User Category with no padding OK 
def SPIDER_CHART(chart_data, filename, title=""):
	categories = []
	values = []
	for k,v in chart_data.items():
		categories.append(k)
		values.append(v)

	angles = [n / float(len(categories)) * 2 * math.pi for n in range(len(categories))]
	ax = plt.subplot(111, polar=True)
	plt.xticks(angles, categories, color='grey', size=16)
	
	ax.set_rlabel_position(0)
	plt.yticks([4,8,12], ["4","8","12"], color="grey", size=7)
	plt.ylim(0,16)

	for idx, v in enumerate(angles):
		position = (v,values[idx]+1.5) if values[idx] <= 10 else (v,values[idx]-1.8)
		str_value = str(round(values[idx],3)) if values[idx] != 8.0 else "Not\nAttempted"
		plt.text(v, values[idx], str_value, fontweight='bold', color="black", size=14 ,ha='center', va='center', alpha=0.5, position=position)

	# We add the first value again so the plot draws all lines 
	# Otherwise, the line connecting the first & last value wont get drawn
	angles.append(angles[0])
	values.append(values[0])

	ax.plot(angles, values, 'o-', linewidth=1)
	ax.fill(angles, values, 'r', alpha=0.5)

	fig = plt.gcf()
	fig.set_size_inches(9,9)
	plt.subplots_adjust(left=0.11, right=0.92, top=0.96, bottom=0.055)
	plt.savefig(filename, format="svg")
	plt.close()

# User / Problem Evolution with no padding OK 
def LINE_PLOT(x,y,filename, x_label="", y_label="", title="", ylim_down=0, ylim_up=16, plot_type=0):
	colors = ["ro-","r-", "m-", "b-", "g-", "y-", "k-"]

	fig, ax = plt.subplots()
	ax.plot(x,y,colors[plot_type])
	ax.grid()
	axes = plt.gca()
	axes.set_ylim([ylim_down,ylim_up])

	position = (x[len(x)-1],float(y[len(y)-1])+ylim_up*0.03125) if y[len(y)-1] < 16 else (x[len(x)-1],10000)
	plt.text(x[len(x)-1], y[len(y)-1], str(round(y[len(y)-1],2)), color="black", size=16 ,ha='center', va='center', alpha=0.9, position=position)

	position = (x[0],float(y[0])+ylim_up*0.03125) if y[0] < 16 else (x[0],10000)
	plt.text(x[0], y[0], str(round(y[0],2)), color="black", size=16 ,ha='center', va='center', alpha=0.9, position=position)

	plt.xlabel(x_label)
	plt.ylabel(y_label)
	plt.suptitle(title)

	"""
	for idx, v in enumerate(x):
		position = (v,float(y[idx])+0.5) if y[idx] < 16 else (v,100)
		plt.text(v, y[idx], str(round(y[idx],2)), color="black", size=12 ,ha='center', va='center', alpha=0.5, position=position)
	"""
	fig.set_size_inches(15, 8)
	plt.subplots_adjust(left=0.045, right=0.97, top=0.95, bottom=0.055)
	fig.savefig(filename, format="svg")
	#plt.show()
	plt.close()

# 
def SCATTER_PLOT(x,y,label, x_label="", y_label="", title=""):
	fig, ax1 = plt.subplots()

	plt.xlabel(x_label)
	plt.ylabel(y_label)
	plt.suptitle(title)

	color = 'tab:red'
	ax1.scatter(x, y, color=color, label=label)

	axes = plt.gca()
	axes.set_xlim([-16,16])
	axes.set_ylim([-5,5])

	fig.set_size_inches(18, 15)
	ax1.legend(loc="best")
	fig.savefig(f"SCATTER_{label}.svg", format="svg")
	plt.close()

# Average Tries with no padding OK
def BAR_AND_CUMULATIVE_PLOT(x,y1,y2,x_label="", y_label="", title="", filename="BAR_AND_CUMULATIVE_PLOT.svg"):
	# Code from https://matplotlib.org/gallery/subplots_axes_and_figures/two_scales.html
	fig, ax1 = plt.subplots()

	ax1.set_xlabel(x_label)
	ax1.set_ylabel(y_label)

	color = 'tab:blue'
	bars = ax1.bar(x, y1, color=color, label="Nº of Users")

	for bar in bars:
		height = bar.get_height()
		ax1.text(bar.get_x() + bar.get_width()/2., 1.05*height,str(round(height, 1))+'%',ha='center', va='bottom')

	ax2 = ax1.twinx()  # instantiate a second axes that shares the same x-axis
	color = 'tab:red'
	plts = ax2.plot(x, y2, color=color, label="Cumulative Percentage")

	for idx, v in enumerate(x):
		ax2.text(v, y2[idx], str(round(y2[idx],1))+'%', color="black", size=10 ,ha='center', va='center', alpha=0.8, position=(v,float(y2[idx])+3.5))

	ax2.set_ylim([0,100])
	#plt.suptitle(title)
	fig.set_size_inches(15, 8)
	plt.subplots_adjust(left=0.045, right=0.97, top=0.95, bottom=0.055)
	plt.savefig("Average_Tries.svg", format="svg")
	#plt.show()
	plt.close()

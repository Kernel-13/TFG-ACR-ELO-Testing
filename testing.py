
import pymysql
import sys
import ELO
import ACR_Stats

u = []
p = []
cnt = 0
while cnt <= 15:
	for i in range(10):
		u.append(round(cnt+i*0.1,1))
	cnt += 1
u.append(16)

p = [round(16-i,1) for i in u]

elo_differences = []
user_gain = []
problem_gain = []

#for t in range(1,11):

for x in u:
	for y in p:

		n_x, n_y = ELO.simulate_no_tries(x, y,'AC')	

		if n_x-x != 0 and n_y-y != 0:
			elo_differences.append(x-y)
			user_gain.append(n_x-x)
			problem_gain.append(n_y-y)

		"""	
		n_x, n_y = ELO.simulate_no_tries(x, y,'WA')	

		if n_x-x != 0 and n_y-y != 0:
			elo_differences.append(x-y)
			user_gain.append(n_x-x)
			problem_gain.append(n_y-y)

		#print(x,y,ELO.Expectation(x,y))
		"""

ACR_Stats.show_ELO_gain(elo_differences, user_gain, problem_gain,x_label = "USER ELO - PROBLEM ELO", y_label="OLD ELO - NEW ELO", title=f"ELO Gain For Different ELO Differences", filename=f"ELO Gain (New K-Factor Formula x 0.25) (New Expectation) [from testing.py] - No Zeros .png")
#ACR_Stats.show_scatter(elo_differences, user_gain, "User Gain",x_label = "USER ELO - PROBLEM ELO", y_label="OLD ELO - NEW ELO", title="ELO Gain For Different ELO Differences")
#ACR_Stats.show_scatter(elo_differences, problem_gain, "Problem Gain",x_label = "USER ELO - PROBLEM ELO", y_label="OLD ELO - NEW ELO", title="ELO Gain For Different ELO Differences")
import math 
import random

def Expectation(Ra, Rb): 
	""" Calculates the 'Expectation' value following the original formula """
	return 1.0 / (1 + math.pow(10, -((Ra - Rb) / 400))) 


def k_factor(x, underdog_won):
	""" Calculates the K-factor """
	if x < 1: x = 1 
	if underdog_won: 	return math.log2(x) + 4
	else:				return 4 - (math.log(x)/math.log(2))


def simulate(ELO_user, ELO_problem, Submission_State):
	""" Calculates the new ratings for both player & problem """

	User_Old_Score = ELO_user
	Problem_Old_Score = ELO_problem

	User_Expectation = Expectation(User_Old_Score, Problem_Old_Score) 
	Problem_Expectation = Expectation(Problem_Old_Score, User_Old_Score) 

	# If Player_1 beats Player_2
	if Submission_State in ('AC', 'PE'): 

		# If Player_1 Wins, and his score is lower than Player_2's score
		if User_Old_Score < Problem_Old_Score: 
			k = k_factor(Problem_Old_Score - User_Old_Score, True)

		# If Player_1 Wins, but his score is higher than Player_2's score
		else:	
			k = k_factor(User_Old_Score - Problem_Old_Score, False)
		User_New_Score = User_Old_Score + k * (1 - User_Expectation)
		Problem_New_Score = Problem_Old_Score + k * (0 - Problem_Expectation)

	# If Player_2 beats Player_1
	else : 

		# If Player_2 Wins, and his score is lower than Player_1's score
		if Problem_Old_Score < User_Old_Score: 
			k = k_factor(User_Old_Score - Problem_Old_Score, True)

		# If Player_2 Wins, but his score is higher than Player_1's score
		else:	
			k = k_factor(Problem_Old_Score - User_Old_Score, False)
		User_New_Score = User_Old_Score + k * (0 - User_Expectation)
		Problem_New_Score = Problem_Old_Score + k * (1 - Problem_Expectation)

	# The following statements prevent the scores from going over 16 or reaching negative values
	if User_New_Score < 0: User_New_Score = 0
	if User_New_Score >16: User_New_Score = 16
	if Problem_New_Score < 0: Problem_New_Score = 0
	if Problem_New_Score >16: Problem_New_Score = 16
	
	return User_New_Score, Problem_New_Score
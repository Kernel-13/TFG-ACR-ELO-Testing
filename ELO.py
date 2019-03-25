import math 
import random

def Expectation(Ra, Rb): 
	""" Calculates the 'Expectation' value following the original formula """
	return 1.0 / (1 + math.pow(10, -((Ra - Rb) / 400))) 


def k_factor(x, underdog_won):
	""" Calculates the K-factor """
	if x <= 1: return 4
	if underdog_won: 	return math.log2(x) + 4
	else:				return 4 - (math.log(x,2))

def k_factor_new_formula(x, underdog_won):
	""" Calculates the K-factor """
	if underdog_won: 	return (x+16)/16
	else:				return (1 - x/16)

def k_factor_new_formula_with_tries(x, underdog_won, tries, status):
	""" Calculates the K-factor """
	if tries >= 10 and status not in ('AC', 'PE'): return 0 
	if underdog_won: 	return ((x+16)/16)*(10 - tries/10)
	else:				return (1 - x/16)*(10 - tries/10)

def simulate_no_tries(ELO_user, ELO_problem, Submission_State):
	""" Calculates the new ratings for both player & problem """

	User_Old_Score = ELO_user
	Problem_Old_Score = ELO_problem

	User_Expectation = Expectation(User_Old_Score, Problem_Old_Score) 
	Problem_Expectation = Expectation(Problem_Old_Score, User_Old_Score) 

	# If the user solves the problem
	if Submission_State in ('AC', 'PE'): 

		# If the user Wins, and his score is lower than the problem's score
		if User_Old_Score < Problem_Old_Score: 
			k = k_factor_new_formula(Problem_Old_Score - User_Old_Score, True)

		# If the user Wins, but his score is higher than the problem's score
		else:	
			k = k_factor_new_formula(User_Old_Score - Problem_Old_Score, False)
		User_New_Score = User_Old_Score + k * (1 - User_Expectation)
		Problem_New_Score = Problem_Old_Score + k * (0 - Problem_Expectation)

	# If the problem remains unsolved
	else : 

		# If the problem Wins, and his score is lower than the user's score
		if Problem_Old_Score < User_Old_Score: 
			k = k_factor_new_formula(User_Old_Score - Problem_Old_Score, True)

		# If the problem Wins, but his score is higher than the user's score
		else:	
			k = k_factor_new_formula(Problem_Old_Score - User_Old_Score, False)
		User_New_Score = User_Old_Score + k * (0 - User_Expectation)
		Problem_New_Score = Problem_Old_Score + k * (1 - Problem_Expectation)

	# The following statements prevent the scores from going over 16 or reaching negative values
	if User_New_Score < 0 or User_New_Score >16 or Problem_New_Score < 0 or Problem_New_Score >16: 
		User_New_Score = User_Old_Score
		Problem_New_Score = Problem_Old_Score

	#return (User_Old_Score - Problem_Old_Score),(User_New_Score - User_Old_Score), (Problem_New_Score - Problem_Old_Score)
	return User_New_Score, Problem_New_Score

def simulate_with_tries(ELO_user, ELO_problem, Submission_State, tries):
	""" Calculates the new ratings for both player & problem """

	User_Old_Score = ELO_user
	Problem_Old_Score = ELO_problem

	User_Expectation = Expectation(User_Old_Score, Problem_Old_Score) 
	Problem_Expectation = Expectation(Problem_Old_Score, User_Old_Score) 

	# If Player_1 beats Player_2
	if Submission_State in ('AC', 'PE'): 

		# If Player_1 Wins, and his score is lower than Player_2's score
		if User_Old_Score < Problem_Old_Score: 
			k = k_factor_new_formula_with_tries(Problem_Old_Score - User_Old_Score, True, tries, Submission_State)

		# If Player_1 Wins, but his score is higher than Player_2's score
		else:	
			k = k_factor_new_formula_with_tries(User_Old_Score - Problem_Old_Score, False, tries, Submission_State)
		User_New_Score = User_Old_Score + k * (1 - User_Expectation)
		Problem_New_Score = Problem_Old_Score + k * (0 - Problem_Expectation)

	# If Player_2 beats Player_1
	else : 

		# If Player_2 Wins, and his score is lower than Player_1's score
		if Problem_Old_Score < User_Old_Score: 
			k = k_factor_new_formula_with_tries(User_Old_Score - Problem_Old_Score, True, tries, Submission_State)

		# If Player_2 Wins, but his score is higher than Player_1's score
		else:	
			k = k_factor_new_formula_with_tries(Problem_Old_Score - User_Old_Score, False, tries, Submission_State)
		User_New_Score = User_Old_Score + k * (0 - User_Expectation)
		Problem_New_Score = Problem_Old_Score + k * (1 - Problem_Expectation)

	# The following statements prevent the scores from going over 16 or reaching negative values
	if User_New_Score < 0: User_New_Score = 0
	if User_New_Score >16: User_New_Score = 16
	if Problem_New_Score < 0: Problem_New_Score = 0
	if Problem_New_Score >16: Problem_New_Score = 16
	
	return User_New_Score, Problem_New_Score
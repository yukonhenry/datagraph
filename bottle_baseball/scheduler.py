def generateRRSchedule(numTeams, numVenues):
    if (numTeams % 2):
        n = (numTeams+1) / 2  # results in a bye in this case
        bye_flag = True
    else:
        n = numTeams/2
        bye_flag = False
    for i in range(numTeams-1):
        j = i+1
        game_list = [(j, 2*n)]
    print numTeams, numVenues, n

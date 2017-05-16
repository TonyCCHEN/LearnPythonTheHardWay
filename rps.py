from random import randint #This is running in Python3.

#create a list of play options
t = ["Rock", "Paper", "Scissors"]

#assign a random play to the computer
computer = t[randint(0,2)]

#set player to False
player = False

while player == False:
#set player to True
    player = input("Rock, Paper, Scissors?")
    if player == computer:
        print("Tie!")
    elif player == "Rock":
        if computer == "Paper":
            print("You Lose!", computer, "covers", player)
        else:
            print("You Win!", player, "smashes", computer)
    elif player == "Paper":
        if computer == "Scissors":
            print("You Lose", computer, "cut",player)
        else:
            print("You Win!", player, "covers", computer)
    elif player == "Scissors":
        if computer == "Rock":
            print("You Lose....", computer, "smashes", player)
        else:
            print("You win!", player, "cut", computer)
    else:
        print("That's not a valid play. Check your spelling!")

    #player was set to True, but we want it to be Flase so loop continues
    player = False
    computer = t[randint(0,2)]

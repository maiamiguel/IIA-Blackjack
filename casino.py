from game import Game
from player import Player
from randomplayer import RandomPlayer
from student import StudentPlayer
import student

show_statistics = True

if __name__ == '__main__':

    players = [StudentPlayer("Human",100)]

    for i in range(5000):
    #while True:
        print(players)
        g = Game(players, min_bet=1, max_bet=5, verbose=True)
        g.run()

    double_down_winrate = float(student.double_down_wins) / (float(student.double_down_wins) + float(student.double_down_losses))
    winrate = float(student.wins) / (float(student.wins) + float(student.losses))

    if show_statistics:
        print("Double down winrate: ", double_down_winrate)
        print("Winrate: ", winrate)
        #print(student.wins + student.losses)
        print("Number of surrenders: ", student.surrender_count)
        print("Number of double downs: ", student.double_down_wins + student.double_down_losses)
        print("Number of double downs wins: ", student.double_down_wins)

    print("OVERALL: ", players)

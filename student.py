#encoding: utf8
import card
import random
import math
from player import Player
import os.path

matrix_path = "matrix.csv"
surrender_percentage = 0.3
double_down_percentage = 0.6
surrender_count = 0
play = True
debug = False
initial_train = False
auto_save_turn = 500
stop_playing_lower_limit = 50
stop_playing_higger_limit = 150
double_down_wins = 0
double_down_losses = 0
wins = 0
losses = 0

class StudentPlayer(Player):
    def __init__(self, name="Meu nome", money=0):
        super(StudentPlayer, self).__init__(name, money)
        self.matrix = Matrix(matrix_path)
        self.min_bet = 0            #minimum bet
        self.max_bet = 0            #maximum bet
        self.count = 0              #count to the turn when the matrix is auto saved
        self.current = []           #current list of turns with a tupple containing (player hand, dealer hand, play(like 's' for stand))
        self.starting_money = money #starting money
        self.surrender = False      #is the current play a surrender
        self.last_bet = 0           #last bet placed
        self.next_bet = 0           #next bet to be placed
        self.first_sequence_bet = True #First bet in the sequence
        self.double_down_bet = False   #did the bet function got called off in a double down play?
        self.betting_sequence = []

    def play(self, dealer, players):
        player_cards = [x for x in players if x.player.name == self.name][0].hand
        dealer_hand = card.value(dealer.hand)               #get the value of the dealer hand
        my_hand = card.value(player_cards)                  #get the value of the player hand
        first_turn = self.current == []                     #check if it is the first turn
        my_soft_hand = self.is_soft_hand(player_cards)      #check if the player has a soft hand
        dealer_soft_hand = self.is_soft_hand(dealer.hand)   #check if the dealer has a soft hand

        if not my_soft_hand and not dealer_soft_hand:
            soft_hand = 0
        elif my_soft_hand and not dealer_soft_hand:
            soft_hand = 1
        elif my_soft_hand and dealer_soft_hand:
            soft_hand = 2
        elif not my_soft_hand and dealer_soft_hand:
            soft_hand = 3

        if initial_train:
            num = random.randint(0,2)
            if num == 0:
                p = 'h'
            elif num == 1:
                p = 's'
            else:
                p = 'd'
        else:
            p = self.matrix.get_best_play(my_hand, dealer_hand, soft_hand, first_turn) #get the best play based on the player hand,
                                                                                #dealer hand and if it is the first turn
        self.current += [(my_hand, dealer_hand, soft_hand, p)] #add the current turn to the list of turns

        if p == 'u':
            self.surrender = True

        if p == 'd':
            self.double_down_bet = True

        if debug:
            print("Current list: " + self.current.__str__())

        return p

    #using Oscar's System (http://www.blackjackforumonline.com/content/Betting_Systems_Oscars_Blackjack_System.htm)
    def bet(self, dealer, players):
        #return 2
        if self.double_down_bet:
            self.double_down_bet = False
            return self.betting_sequence[self.last_bet % len(self.betting_sequence)]

        if self.first_sequence_bet:
            self.first_sequence_bet = False
            self.last_bet = 0
            return self.betting_sequence[self.last_bet % len(self.betting_sequence)]

        self.last_bet = self.next_bet

        return self.betting_sequence[self.last_bet % len(self.betting_sequence)]


    def payback(self, prize):
        """ receives bet + premium
            of 0 if both player and dealer have black jack
            or -bet if player lost
        """

        self.table = 0          #set the table number
        self.pocket += prize    #add/remove the prize from the total money
        global double_down_wins, double_down_losses, wins, losses
        if not self.surrender:
            if prize >= 0:                      #check if the player won or drew (a draw is better than losing soo it's considered a win)
                self.next_bet = self.last_bet   #make the next bet 1 unit more than the last one

                if prize > 0:
                    wins += 1

                if self.is_like_double_down():
                    self.matrix.update(self.current[0][0], self.current[0][1], self.current[0][2], 'd', 'w')    #add to the double down wins column
                    if debug:
                        print("Like Double Down: " + str(self.current[0][0]) + " " + str(self.current[0][1]) + " " + str(self.current[0][2]) + ' d w')
                if debug:
                    print("Loop: ")
                for p in self.current:
                    self.matrix.update(p[0], p[1], p[2], p[3], 'w')    #add all the turns from the current list that lead to the win
                    if p[3] == 'd':
                        double_down_wins += 1
                    if debug:
                        print(str(p[0]) + " " + str(p[1]) + " " + str(p[2]) + " " + str(p[3]) + ' w')
            elif prize < 0:                         #check if the player lost
                self.next_bet = self.last_bet + 1   #make the next bet equal to the last one

                losses += 1

                if self.is_like_double_down():
                    self.matrix.update(self.current[0][0], self.current[0][1], self.current[0][2], 'd', 'l')    #add to the double down losses column
                    if debug:
                        print("Like Double Down: " + str(self.current[0][0]) + " " + str(self.current[0][1]) + " " + str(self.current[0][2]) + ' d l')
                if debug:
                    print("Loop: ")
                for p in self.current:
                    self.matrix.update(p[0], p[1], p[2], p[3], 'l')    #add all the turns from the current list that lead to the lost
                    if p[3] == 'd':
                        double_down_losses += 1
                    if debug:
                        print(str(p[0]) + " " + str(p[1]) + " " + str(p[2]) + " " + str(p[3]) + ' l')
        else:
            self.surrender = False
            losses += 1

        if self.pocket > self.starting_money:
            self.first_sequence_bet = True
            self.starting_money = self.pocket

        self.current = []    #clear the current turns list

        self.count += 1
        if self.count == auto_save_turn:    #check if the current turn is an auto save turn
            self.matrix.save()              #save the matrix
            self.count = 0                  #reset the count

    def want_to_play(self, rules):      #if you have to much money and jut want to watch, return False
                                        # rules contains a Game.Rules object with information on the game rules (min_bet, max_bet, shoe_size, etc)
        #if self.pocket > stop_playing_higger_limit or self.pocket < stop_playing_lower_limit:
        #    return False

        if self.max_bet != rules.max_bet or self.min_bet != rules.min_bet:
            self.min_bet = rules.min_bet
            self.max_bet = rules.max_bet
            self.next_bet = 0
            self.last_bet = 0
            self.first_sequence_bet = True
            self.betting_sequence = []
            for i in range(self.min_bet, self.max_bet+1):
                if i % 2 == 0:
                    self.betting_sequence += [i]

        return True

    #if the first turn was a hit and the rest stands (same as double down) return True
    def is_like_double_down(self):
        if len(self.current) == 0:
            return False

        if self.current[0][2] == 'h':
            for i in self.current[1:]:
                if i[2] != 's':
                    return False
            return True
        return False

    #if is is a softHand(has an ace) return True
    def is_soft_hand(self, hand):
        for c in hand:
            if c.rank == 1:
                return True
        return False

class Entrie:

    def __init__(self, mh, dh, sh, hw=1, hl=1, sw=1, sl=1, dw=1, dl=1):
        self.mh = mh    #mh - My Hand Value
        self.dh = dh    #dh - Dealer Hand Value
        self.sh = sh    #sh - Soft Hand (lower bit on = dealer has soft hand. higher bit on = i have soft hand)
        self.hw = hw    #hw - Number of Hit wins
        self.hl = hl    #hl - Number of Hit losses
        self.sw = sw    #sw - Number of Stand wins
        self.sl = sl    #sl - Number of Stand losses
        self.dw = dw    #dw - Number of Double Down wins
        self.dl = dl    #dl - Number of Double Down losses

class Matrix:

    def __init__(self, path):
        self.path = path        #create a class variable for the path of the matrix file
        self.create_matrix()    #create the default matrix in memory

        if os.path.isfile(path):            #check if the file exists
            self.load_matrix_from_file()    #if it exists load the matrix from the file

    #creates the default matrix
    def create_matrix(self):
        self.matrix = dict()

        for i in range(2, 21):
            for j in range(2, 22):
                self.matrix[i,j,0] = Entrie(i,j,0);
                self.matrix[i,j,1] = Entrie(i,j,1);
                self.matrix[i,j,2] = Entrie(i,j,2);
                self.matrix[i,j,3] = Entrie(i,j,3);

    #load the matrix from the file to memory
    def load_matrix_from_file(self):
        f = open(self.path, 'r')

        line = f.readline()
        while line != "":
            fields = line.split(',')
            entrie = self.matrix[int(fields[0]), int(fields[1]), int(fields[2])]

            entrie.mh = int(fields[0]);
            entrie.dh = int(fields[1]);
            entrie.sh = int(fields[2])
            entrie.hw = int(fields[3]);
            entrie.hl = int(fields[4]);
            entrie.sw = int(fields[5]);
            entrie.sl = int(fields[6]);
            entrie.dw = int(fields[7]);
            entrie.dl = int(fields[8]);

            line = f.readline()

        f.close()

    #save the matrix from memory to the file
    def save(self):
        f = open(self.path, 'w')

        for i in range(2, 21):
            for j in range(2, 22):
                for k in range(0,4):
                    entrie = self.matrix[i,j,k]

                    f.write(str(entrie.mh) + "," +
                            str(entrie.dh) + "," +
                            str(entrie.sh) + "," +
                            str(entrie.hw) + "," +
                            str(entrie.hl) + "," +
                            str(entrie.sw) + "," +
                            str(entrie.sl) + "," +
                            str(entrie.dw) + "," +
                            str(entrie.dl) + "\n")

        f.close()

    #update the matrix depending on my hand (mh), dealer's hand(dh), play (p) and if the outcome was a win/loss
    def update(self, mh, dh, sh, play, win):
        entrie = self.matrix[mh,dh,sh]    #get the matrix entrie associated with the player hand and the dealer hand

        #increment the right column of the matrix in case of win or loss
        if play == 'h':
            if win == 'w':
                entrie.hw += 1
            elif win == 'l':
                entrie.hl += 1
        elif play == 's':
            if win == 'w':
                entrie.sw += 1
            elif win == 'l':
                entrie.sl += 1
        elif play == 'd':
            if win == 'w':
                entrie.dw += 1
            elif win == 'l':
                entrie.dl += 1

    #calculate the best play based on my hand (mh), the dealer's hand (dh) and if it is the first turn (first_turn)
    def get_best_play(self, mh, dh, sh, first_turn):
        entrie = self.matrix[mh,dh,sh]    #get the matrix entrie associated with the player hand and the dealer hand

        global surrender_count
        #calculate the win rate (wins/total games) for each play
        hit_win_rate = float(entrie.hw) / (float(entrie.hw) + float(entrie.hl))
        stand_win_rate = float(entrie.sw) / (float(entrie.sw) + float(entrie.sl))
        double_down_win_rate = float(entrie.dw) / (float(entrie.dw) + float(entrie.dl))

        #return a double down play if the win rate is higher than the threshold
        if play:
            if double_down_win_rate >= double_down_percentage and first_turn:
               return 'd'

        #return the play with the highest win rate, in the it is 'double down' return the second highest if it is not
        #the first turn
        if first_turn and double_down_win_rate >= hit_win_rate and double_down_win_rate >= stand_win_rate:
            if play:
                if double_down_win_rate < surrender_percentage:
                    surrender_count += 1
                    return 'u'
            return 'd'
        elif hit_win_rate >= stand_win_rate:
            if play:
                if hit_win_rate < surrender_percentage:
                    surrender_count += 1
                    return 'u'
            return 'h'
        else:
            if play:
                if stand_win_rate < surrender_percentage:
                    surrender_count += 1
                    return 'u'
            return 's'

    #print the matrix on the console (only for debugging purposes)
    def print_matrix(self):
          for i in range(2, 21):
            for j in range(2, 22):
                for k in range(0,4):
                    entrie = self.matrix[i,j,k]
                    print(str(entrie.mh) + "," +
                            str(entrie.dh) + "," +
                            str(entrie.sh) + "," +
                            str(entrie.hw) + "," +
                            str(entrie.hl) + "," +
                            str(entrie.sw) + "," +
                            str(entrie.sl) + "," +
                            str(entrie.dw) + "," +
                            str(entrie.dl) + "\n")
#
    #def print_stats(self):
    #    total = 0
    #    total_wins = 0
    #    total_losses = 0
#
    #    for l1 in self.matrix:
    #        for l2 in self.matrix[l1]:
    #            entrie = self.matrix[l1][l2]
    #            total_wins += entrie.dw + entrie.hw + entrie.sw
    #            total_losses += entrie.dl + entrie.hl + entrie.sl
    #            total += total_wins + total_losses
#
    #    print(str(total) + " " + str(total_wins) + " " + str(total_losses))
#
    #def get_entrie(self, mh, dh):
    #    entrie = self.matrix[mh][dh]
    #    return (str(entrie.mh) + "," +
    #            str(entrie.dh) + "," +
    #            str(entrie.hw) + "," +
    #            str(entrie.hl) + "," +
    #            str(entrie.sw) + "," +
    #            str(entrie.sl) + "," +
    #            str(entrie.dw) + "," +
    #            str(entrie.dl) + "\n")
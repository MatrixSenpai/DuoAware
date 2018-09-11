from tkinter import *
from tkinter import ttk, messagebox, simpledialog

from riotwatcher import RiotWatcher
from requests.exceptions import HTTPError
from exceptions import *

import os

class Window(Frame):

    infoLabel: Label
    summonerLabel: Label
    duoLabel: Label
    progressLabel: Label
    resultsLabel: Label

    progressCount: int = 0
    progressTotal: int = 0

    progress: ttk.Progressbar

    def __init__(self, master=None):
        Frame.__init__(self, master)
        self.master = master

        self.__init_window()

    def __init_window(self):
        self.master.title("Duo Games Finder")
        self.pack(fill=BOTH, expand=1)

        self.__init_menu()
        self.__init_labels()
        self.__init_progress()

    def __init_menu(self):
        menu = Menu(self.master)
        self.master.config(menu=menu)

        main = Menu(menu)
        main.add_command(label="Find Games", command=self.master.main_process)
        main.add_command(label="Exit", command=self.__client_exit)

        menu.add_cascade(label='File', menu=main)

    def __init_labels(self):
        i = Label(master=self, text="Click the File Menu and select Find Games")
        i.pack(side='top', anchor='w')

        s = Label(master=self, text="No Summoners Searched Yet")
        s.pack(side='bottom', anchor='w')

        d = Label(master=self, text="No Duos Yet")
        d.pack(side='bottom', anchor='e')

        p = Label(master=self, text="0/0 - 0%")
        p.pack(side='top', anchor='n')

        r = Label(master=self, text="")
        r.pack(side='bottom', anchor='s', pady=100)

        self.infoLabel = i
        self.summonerLabel = s
        self.duoLabel = d
        self.progressLabel = p
        self.resultsLabel = r

    def __init_progress(self):
        p = ttk.Progressbar(master=self, orient='horizontal', mode='determinate', maximum=100)
        p.pack(fill='x', anchor='s', padx=15, pady=25)

        self.progress = p

    def update_info_label(self, i):
        self.infoLabel['text'] = i

    def update_summoner_label(self, s):
        self.summonerLabel['text'] = s

    def update_duo_label(self, d):
        self.duoLabel['text'] = d

    def update_progress(self, max):
        self.progress['maximum'] = max
        self.progressTotal = max
        self.progressLabel['text'] = "0/%d - 0%%" % (max)

    def step(self):
        self.progress.step()
        self.progressCount += 1

        p = self.progressCount / self.progressTotal * 100

        self.progressLabel['text'] = "%d/%d - %d%%" % (self.progressCount, self.progressTotal, int(p))
        self.update()

    @staticmethod
    def __client_exit():
        exit()


class App(Tk):

    window: Window
    progress: int
    watcher: RiotWatcher

    summoner: RiotWatcher.summoner

    DEFAULT_INFO: str = "Click the File Menu and select Find Games"
    DEFAULT_SUMMONER: str = "No summoner searched yet"
    DEFAULT_DUO: str = "No duo searched yet"

    def __init__(self):
        Tk.__init__(self)



        self.progress = 0
        self.watcher = RiotWatcher(os.environ.get('RGAPI'))

        self.__setup_size()

        self.window = Window(master=self)
        self.window.pack(expand=True)

        self.mainloop()

    def __setup_size(self):
        ht = 500
        wh = 500

        pr = int(self.winfo_screenwidth()/2 - ht/2)
        pd = int(self.winfo_screenheight()/2 - wh/2)

        self.geometry("%dx%d-%d+%d" %(500, 500, pr, pd))
        self.resizable(0, 0)

    def main_process(self):
        self.__update_info("Waiting for summoner info...")
        while True:
            try:
                summoner = self.get_summoner()
                self.summoner = summoner
                break
            except HTTPError as e:
                self.show_error("Could not find summoner. Please try again")
                print(e)
            except EmptySummonerError as e:
                self.show_error("Please enter a summoner name!")
                print(e)
            except EndExecution:
                self.__update_info(self.DEFAULT_INFO)
                return

        self.__update_summoner("Summoner retrieved\n%s" % (summoner['name']))
        self.__update_info("Waiting for duos...")

        while True:
            try:
                (duos, names) = self.get_duos()
                break
            except HTTPError as e:
                self.show_error("One of the summoner names was not correct. Try again")
                print(e)
            except EmptySummonerError as e:
                self.show_error("Please enter one or more summoner names!")
                print(e)
            except AssertionError:
                self.show_error("There was an internal error. Tell the developer he's terrible")
                print(e)
            except EndExecution:
                self.__update_info(self.DEFAULT_INFO)
                self.__update_summoner(self.DEFAULT_SUMMONER)
                return

        self.__update_info("Gathering Matches...")
        self.__update_duos("Duos retrieved\n%s" % (names))

        while True:
            try:
                iterations = self.get_iterations()
                break
            except ValueError as e:
                self.show_error("Please enter a number!")
                print(e)
            except ValueTooLowError:
                self.show_error("Please enter a multiple of 100!")
            except EndExecution:
                return

        self.__update_max(iterations)

        print("Now searching user %s's last %d games for summoners:\n%s" % (summoner['name'], iterations, names))
        (count, playCount, wins, losses) = self.analyze_history(iterations, summoner, duos)

        self.__update_info("All done!")
        self.__update_results(count, playCount, wins, losses)

        print("Count: %d, Play Count: %d, Wins: %d, Losses: %d, Win Percentage: %.2f%%" % (count, playCount, wins, losses, (wins / playCount * 100)))

    def __update_info(self, i):
        self.window.update_info_label(i)

    def __update_summoner(self, s):
        self.window.update_summoner_label(s)

    def __update_duos(self, d):
        self.window.update_duo_label(d)

    def __step_progress(self):
        self.window.step()

    def __update_max(self, m):
        self.window.update_progress(m)

    def __update_results(self, c, p, w, l):
        r = w / p * 100
        s = "Search Results\nGames Searched: %d\nDuo Games: %d\nGames Won: %d\nGames Lost: %d\nWin Percentage: %.2f%%" % (c, p, w, l, r)
        self.window.resultsLabel['text'] = s

    def __check_summoner_valid(self, s):
        if s is None:
            raise EndExecution
        if len(s) == 0:
            raise EmptySummonerError

        return self.watcher.summoner.by_name('na1', s)

    def __check_int_valid(self, i):
        if i is None:
            raise EndExecution

        i = int(i)

        if i < 100 or (i % 100) != 0:
            raise ValueTooLowError

        return i

    def get_summoner(self):
        s = simpledialog.askstring("Summoner", "Enter your summoner name", parent=self)
        return self.__check_summoner_valid(s)

    def get_duos(self):
        d = simpledialog.askstring("Duos", "Enter your duos' summoner names (e.g. summonerOne,summonerTwo)", parent=self)

        if d is None:
            raise EndExecution
        if len(d) == 0:
            raise EmptySummonerError

        d = d.split(',')
        rtr = []
        rnm = ""

        for s in d:
            s = self.__check_summoner_valid(s)
            rtr.append(s)
            rnm += "%s\n" % (s['name'])

        assert len(rtr) == len(d)
        return (rtr, rnm)

    def get_iterations(self):
        i = simpledialog.askinteger("Games to Search", "How many games back should be searched?", parent=self)
        return self.__check_int_valid(i)

    def analyze_history(self, iterations, summoner, duos):
        count = iterations
        playCount = 0
        wins = 0
        losses = 0

        duoId = []
        duoNames = []

        for d in duos:
            duoId.append(d['accountId'])
            duoNames.append(d['name'])

        iterations = int(iterations / 100)

        for i in range(0, iterations):
            try:
                history = self.watcher.match.matchlist_by_account('na1', summoner['accountId'])

                for match in history['matches']:
                    self.__step_progress()

                    gid = match['gameId']
                    x = self.watcher.match.by_id('na1', gid)

                    part = x['participantIdentities']

                    for p in part:
                        id = p['player']['accountId']
                        name = p['player']['summonerName']
                        pid = p['participantId']

                        if id in duoId or name in duoNames:
                            playCount += 1

                            side = 0 if pid in [1, 2, 3, 4, 5] else 1
                            result = self.didWin(x, side)

                            if result:
                                wins += 1
                            else:
                                losses += 1

                            break

            except HTTPError as e:
                self.show_error("There was an error when processing matches. Please try again")
                print(e)
                return

        return count, playCount, wins, losses

    def didWin(self, match, side):
        blue = match['teams'][0]
        red = match['teams'][1]

        if side == 0:
            if blue['win'] == 'Win':
                return True
        if side == 1:
            if red['win'] == 'Win':
                return True
        return False

    def show_error(self, e):
        messagebox.showerror("Error", e, parent=self)

    def save_summoner(self):
        pass

    def retrieve_summoner(self):
        pass

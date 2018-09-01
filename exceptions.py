class SummonerError(Exception):
    summoner: str

    def __init__(self, summoner):
        super().__init__()
        self.summoner = summoner


class EmptySummonerError(SummonerError):
    pass


class EndExecution(Exception):
    pass


class ValueTooLowError(Exception):
    pass

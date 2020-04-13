
import abc


MUON = 0


class Data(abc.ABC):
    pass


class MuonData(Data):
    data_type = MUON

    def __init__(self):
        self.histograms = None
        self.asymmetry = None
        self.uncertainty = None
        self.time = None
        self.meta = None


# fixme put all those µsr functions here.


from PyQt5 import QtWidgets


# noinspection PyArgumentList
class Tree(QtWidgets.QTreeWidget):
    def __init__(self):
        super(Tree, self).__init__()
        self.__manager = TreeManager(self)


class TreeManager:
    def __init__(self, view):
        self.__view = view
        self.__run_service = RunService()
        self.__fit_service = FitService()

    def _create_tree_model(self, runs, fits):
        return self

    def update(self):
        runs = self.__run_service.get_runs()
        fits = self.__fit_service.get_fits()

        tree = self._create_tree_model(runs, fits)


class HeadingNode(QtWidgets.QTreeWidgetItem):
    def __init__(self):
        super(HeadingNode, self).__init__()

    def _set_callbacks(self):
        pass

    def _expand(self):
        pass


class RunNode(QtWidgets.QTreeWidgetItem):
    def __init__(self):
        super(RunNode, self).__init__()

    def _set_callbacks(self):
        pass

    def _expand(self):
        pass

    def _load(self):
        pass

    def _plot(self):
        pass

    def _save(self):
        pass


class HistogramNode(QtWidgets.QTreeWidgetItem):
    def __init__(self):
        super(HistogramNode, self).__init__()

    def _set_callbacks(self):
        pass

    def _expand(self):
        pass

    def _combine(self):
        pass

    def _asymmetry(self):
        pass

    def _edit(self):
        pass

    def _write(self):
        pass


class AsymmetryNode(QtWidgets.QTreeWidgetItem):
    def __init__(self):
        super(AsymmetryNode, self).__init__()

    def _set_callbacks(self):
        pass

    def _expand(self):
        pass

    def _combine(self):
        pass

    def _plot(self):
        pass

    def _edit(self):
        pass

    def _write(self):
        pass


class UncertaintyNode(QtWidgets.QTreeWidgetItem):
    def __init__(self):
        super(UncertaintyNode, self).__init__()

    def _set_callbacks(self):
        pass


class MetaNode(QtWidgets.QTreeWidgetItem):
    def __init__(self):
        super(MetaNode, self).__init__()

    def _set_callbacks(self):
        pass

    def _expand(self):
        pass


class KeyValueNode(QtWidgets.QTreeWidgetItem):
    def __init__(self):
        super(KeyValueNode, self).__init__()

    def _set_callbacks(self):
        pass

    def _edit(self):
        pass


class FitNode(QtWidgets.QTreeWidgetItem):
    def __init__(self):
        super(FitNode, self).__init__()

    def _set_callbacks(self):
        pass

    def _expand(self):
        pass

    def _load(self):
        pass

    def _plot(self):
        pass

    def _save(self):
        pass

    def _edit(self):
        pass

from textual.widgets import OptionList


# Reference: https://github.com/davidfokkema
class DoubleClickOptionList(OptionList):
    def _on_click(self, event):
        if event.chain == 1:
            event.prevent_default()

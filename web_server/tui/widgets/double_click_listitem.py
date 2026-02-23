from textual.widgets import (
    ListItem,
)


# Reference: https://github.com/davidfokkema
class DoubleClickListItem(ListItem):
    def _on_click(self, event):
        if event.chain == 1:
            event.prevent_default()

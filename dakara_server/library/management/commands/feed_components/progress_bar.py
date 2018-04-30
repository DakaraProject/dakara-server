import progressbar


class TextProgressBar(progressbar.ProgressBar):
    """Progress bar with text in the widgets

    Args:
        text (str): text to display at the left of the line.
    """

    def __init__(self, *args, text=None, **kwargs):
        super().__init__(*args, **kwargs)

        # customize the widget if text is provided
        if text is not None:
            # space padded length for text
            # set length to one quarter of terminal width
            width, _ = progressbar.utils.get_terminal_size()
            length = int(width * 0.25)

            # truncate text if necessary
            if len(text) > length:
                half = int(length * 0.5)
                text = text[:half - 2].strip() + '...' + \
                    text[-half + 1:].strip()

            widgets = [
                "{:{length}s} ".format(text, length=length)
            ]

            widgets.extend(self.default_widgets())
            self.widgets = widgets


class TextNullBar(progressbar.NullBar):
    """Muted bar

    It displays one line of text instead with the amount of actions to process.

    Args:
        text (str): text to display.
    """

    def __init__(self, *args, max_value=None, text=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.text = text
        self.max_value = max_value

        if self.text:
            print("{} ({})".format(self.text, self.max_value))

import time


def select_select2_autocomplete(page, container_selector, value):
    """Select a value from a Select2 autocomplete widget using Playwright."""
    page.locator(container_selector).click()
    page.locator(".select2-search__field").fill(value)
    page.locator(".select2-results__option").first.wait_for(state="visible")
    page.keyboard.press("Enter")


class SequentialDialogHandler:
    """Handle a sequence of browser dialogs (alert/confirm/prompt) in Playwright.

    Playwright requires dialog handlers to be registered BEFORE the action
    that triggers them. This class manages a queue of expected dialog responses.

    Usage:
        handler = SequentialDialogHandler(page)
        handler.expect_prompt("form name")  # prompt -> accept with text
        handler.expect_accept()             # confirm/alert -> accept
        handler.expect_dismiss()            # confirm -> dismiss

        page.locator("#saveButton").click()  # triggers dialogs
        handler.wait_for_count(2)            # wait until 2 dialogs handled
        handler.detach()
    """

    def __init__(self, page):
        self.page = page
        self.handled = []
        self._pending = []
        page.on("dialog", self._handle)

    def expect_accept(self):
        self._pending.append(("accept", None))
        return self

    def expect_dismiss(self):
        self._pending.append(("dismiss", None))
        return self

    def expect_prompt(self, text):
        self._pending.append(("accept", text))
        return self

    def _handle(self, dialog):
        idx = len(self.handled)
        if idx < len(self._pending):
            action, text = self._pending[idx]
            if action == "accept":
                dialog.accept(text or "")
            else:
                dialog.dismiss()
        else:
            # Default: accept unexpected dialogs so they don't block
            dialog.accept()
        self.handled.append(dialog)

    def wait_for_count(self, n, timeout=10):
        deadline = time.time() + timeout
        while len(self.handled) < n and time.time() < deadline:
            self.page.wait_for_timeout(100)
        if len(self.handled) < n:
            raise TimeoutError(
                f"Expected {n} dialogs, got {len(self.handled)} "
                f"after {timeout}s"
            )

    def detach(self):
        self.page.remove_listener("dialog", self._handle)

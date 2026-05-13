"""Basic Playwright smoke test for the htmx variant.

The htmx variant has no iframe — results swap inline into
`#multiseek-results` via htmx GET to `/htmx/results/`.
"""

import pytest

from books.models import Author, Book, Language


@pytest.fixture
def books_fixture(db):
    eng = Language.objects.create(name="english", description="English")
    smith = Author.objects.create(first_name="John", last_name="Smith")
    novak = Author.objects.create(first_name="Stephan", last_name="Novak")

    match = Book.objects.create(
        title="Quick test book",
        year=2020,
        language=eng,
        no_editors=1,
        available=True,
    )
    match.authors.add(smith)

    other = Book.objects.create(
        title="A different book",
        year=2010,
        language=eng,
        no_editors=1,
        available=False,
    )
    other.authors.add(novak)
    return {"match": match, "other": other}


@pytest.mark.django_db(transaction=True)
def test_fill_value_and_submit_filters_results(live_server, page, books_fixture):
    page.goto(f"{live_server.url}/multiseek/")
    page.wait_for_load_state("networkidle")

    # The string-field value input is inside the .ms-value-widget div.
    page.locator(".ms-value-string").first.fill("test")

    # Debounce: htmx field-value endpoint fires on 300ms keyup-changed.
    # Give it a beat so the session is updated before Send Query.
    page.wait_for_timeout(400)

    # Send Query button does hx-get to /htmx/results/ targeting #multiseek-results.
    page.get_by_role("button", name="Send query").click()

    # Results swap into #multiseek-results inline.
    results = page.locator("#multiseek-results")
    results.locator("text=Quick test book").wait_for(timeout=10000)

    text = results.inner_text()
    assert "Quick test book" in text
    assert "A different book" not in text

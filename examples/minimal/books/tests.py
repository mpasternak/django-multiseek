"""Basic Playwright smoke test for the Foundation (minimal) variant.

Fills the first value input with "test", clicks Send Query, verifies the
matching book appears in the results iframe and the non-matching one
doesn't. Run with::

    cd examples/minimal
    uv run pytest --browser chromium

(`chromium` is pytest-playwright's default; the flag just makes the intent
explicit.)
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
    page.locator("#value").first.wait_for(state="visible", timeout=5000)
    page.locator("#value").first.fill("test")
    page.locator("#sendQueryButton").click()
    # Submission posts the dynamic form into the iframe; wait for the
    # iframe to navigate and the description to land.
    iframe = page.frame_locator("#if")
    iframe.locator("text=Query: title contains").wait_for(timeout=10000)

    text = iframe.locator("body").inner_text()
    assert "Quick test book" in text
    assert "A different book" not in text

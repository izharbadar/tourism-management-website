import re
from html import unescape
from itertools import zip_longest

import nh3
from flask import request

from capture_pakistan.extensions import db
from capture_pakistan.models import (
    TourAttraction,
    TourFAQ,
    TourItinerary,
)


DESCRIPTION_CLEANER = nh3.Cleaner(
    tags={
        "p",
        "br",
        "strong",
        "em",
        "u",
        "s",
        "h2",
        "h3",
        "h4",
        "blockquote",
        "ol",
        "ul",
        "li",
        "a",
        "span",
    },
    attributes={
        "a": {
            "href",
            "title",
            "target",
        },
        "li": {
            "data-list",
        },
        "span": {
            "contenteditable",
        },
    },
    allowed_classes={
        "span": {
            "ql-ui",
        },
    },
    url_schemes={
        "http",
        "https",
        "mailto",
    },
    clean_content_tags={
        "script",
        "style",
    },
    link_rel="noopener noreferrer",
)


def create_slug(value):
    slug = (value or "").lower().strip()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    return slug.strip("-")


def generate_unique_slug(model, value, current_id=None):
    base_slug = create_slug(value) or "item"
    slug = base_slug
    counter = 2

    while True:
        query = model.query.filter_by(slug=slug)

        if current_id is not None:
            query = query.filter(model.id != current_id)

        if not query.first():
            return slug

        slug = f"{base_slug}-{counter}"
        counter += 1


def clean_tour_description(value):
    return DESCRIPTION_CLEANER.clean(value or "")


def rich_text_is_empty(value):
    plain_text = re.sub(r"<[^>]+>", "", value or "")
    plain_text = unescape(plain_text).replace("\xa0", " ").strip()
    return not plain_text


def replace_tour_sections(tour):
    """Replace itinerary, attractions and FAQ rows submitted with a tour form."""

    TourItinerary.query.filter_by(
        tour_id=tour.id
    ).delete(synchronize_session=False)

    TourAttraction.query.filter_by(
        tour_id=tour.id
    ).delete(synchronize_session=False)

    TourFAQ.query.filter_by(
        tour_id=tour.id
    ).delete(synchronize_session=False)

    itinerary_rows = zip_longest(
        request.form.getlist("itinerary_day_number[]"),
        request.form.getlist("itinerary_title[]"),
        request.form.getlist("itinerary_description[]"),
        request.form.getlist("itinerary_accommodation[]"),
        request.form.getlist("itinerary_meals[]"),
        fillvalue="",
    )

    for fallback_day, row in enumerate(itinerary_rows, start=0):
        day, title, description, accommodation, meals = row

        title = title.strip()
        description = description.strip()
        accommodation = accommodation.strip()
        meals = meals.strip()

        if not any([title, description, accommodation, meals]):
            continue

        try:
            day_number = max(0, int(day))
        except (TypeError, ValueError):
            day_number = fallback_day

        db.session.add(
            TourItinerary(
                tour_id=tour.id,
                day_number=day_number,
                title=title or f"Day {day_number}",
                description=description,
                accommodation=accommodation or None,
                meals=meals or None,
            )
        )

    attractions_text = request.form.get("attractions_text", "")
    attraction_lines = attractions_text.splitlines()

    if not any(line.strip() for line in attraction_lines):
        attraction_lines = request.form.getlist("attraction_title[]")

    seen_attractions = set()
    attraction_order = 1

    for raw_line in attraction_lines:
        title = re.sub(
            r"^\s*(?:[•*\-]|\d+[.)])\s*",
            "",
            raw_line or "",
        ).strip()

        if not title:
            continue

        normalized_title = title.casefold()

        if normalized_title in seen_attractions:
            continue

        seen_attractions.add(normalized_title)

        db.session.add(
            TourAttraction(
                tour_id=tour.id,
                title=title,
                description=None,
                sort_order=attraction_order,
            )
        )

        attraction_order += 1

    faq_rows = zip_longest(
        request.form.getlist("faq_question[]"),
        request.form.getlist("faq_answer[]"),
        fillvalue="",
    )

    for sort_order, row in enumerate(faq_rows, start=1):
        question, answer = row
        question = question.strip()
        answer = answer.strip()

        if not question or not answer:
            continue

        db.session.add(
            TourFAQ(
                tour_id=tour.id,
                question=question,
                answer=answer,
                sort_order=sort_order,
                is_active=True,
            )
        )

from shorts_factory.models import Transcript, TranscriptSegment
from shorts_factory.selector import select_highlights


def make_transcript() -> Transcript:
    return Transcript(
        source="source.mp4",
        duration=90,
        language="en",
        segments=[
            TranscriptSegment(id=0, start=0, end=8, text="Here is the secret that changes everything!"),
            TranscriptSegment(id=1, start=10, end=25, text="This is a practical explanation with useful details."),
            TranscriptSegment(id=2, start=30, end=45, text="Why do most people make this mistake?"),
            TranscriptSegment(id=3, start=50, end=70, text="The solution is simple and actionable."),
        ],
    )


def test_selects_limited_non_overlapping_clips():
    clips = select_highlights(make_transcript(), count=2, minimum=5, maximum=30, padding=0)
    assert len(clips) == 2
    assert clips[0].start < clips[0].end
    assert clips[0].end <= clips[1].start


def test_empty_transcript_returns_empty():
    assert select_highlights(Transcript(source="empty.mp4"), count=3) == []
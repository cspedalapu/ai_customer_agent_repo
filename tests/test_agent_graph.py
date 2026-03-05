from pathlib import Path
import uuid

from core.agent_graph import AgentGraphRunner
from core.appointments import AppointmentStore
from core.config import Settings
from core.database import Booking, get_db


class DummyKB:
    def query(self, query_text: str, top_k: int):
        return {"documents": [[]], "metadatas": [[]], "distances": [[]]}


def _runner(tmp_path: Path) -> AgentGraphRunner:
    settings = Settings(appointments_path=str(tmp_path / "appointments.json"))
    store = AppointmentStore(settings)
    return AgentGraphRunner(settings=settings, kb=DummyKB(), appointment_store=store)


def _ensure_open_slot(store: AppointmentStore) -> str:
    slots = store.list_open_slots(limit=1)
    if slots:
        return slots[0]
    with get_db() as db:
        booking = db.query(Booking).filter(Booking.status == "booked").first()
        if booking:
            booking.status = "cancelled"
            db.commit()
    slots = store.list_open_slots(limit=1)
    assert slots
    return slots[0]


def test_cancel_routes_before_book(tmp_path: Path):
    runner = _runner(tmp_path)
    out = runner.run(session_id="s1", message="please cancel appointment APT-1234567890")
    assert out["intent"] == "cancel_appointment"


def test_list_route(tmp_path: Path):
    runner = _runner(tmp_path)
    out = runner.run(session_id="s2", message="show my appointment using 5125551212")
    assert out["intent"] == "list_appointments"


def test_booking_flow_continues_across_turns(tmp_path: Path):
    runner = _runner(tmp_path)
    session_id = f"s3-{uuid.uuid4().hex[:8]}"
    open_slot = _ensure_open_slot(runner.appointment_store)
    service_type = open_slot.split("|", 1)[0].strip()

    first = runner.run(session_id=session_id, message="I am John, want to book an appointment")
    assert first["intent"] == "book_appointment"
    assert "email address" in first["answer"].lower()

    second = runner.run(session_id=session_id, message="john@example.com")
    assert second["intent"] == "book_appointment"
    assert "what service" in second["answer"].lower()

    third = runner.run(session_id=session_id, message=service_type)
    assert third["intent"] == "book_appointment"
    assert "please pick one of these available slots" in third["answer"].lower()
    assert "1." in third["answer"]

    fourth = runner.run(session_id=session_id, message="1")
    assert fourth["intent"] == "book_appointment"
    assert "appointment is confirmed" in fourth["answer"].lower()
    assert "booking id:" in fourth["answer"].lower()


def test_booking_accepts_datetime_only_slot_selection(tmp_path: Path):
    runner = _runner(tmp_path)
    session_id = f"s4-{uuid.uuid4().hex[:8]}"
    open_slot = _ensure_open_slot(runner.appointment_store)
    service_type = open_slot.split("|", 1)[0].strip()
    dt_only = open_slot.split("|", 1)[1].strip()

    runner.run(session_id=session_id, message="My name is Jamie, I need an appointment")
    runner.run(session_id=session_id, message="jamie@example.com")
    runner.run(session_id=session_id, message=service_type)
    out = runner.run(session_id=session_id, message=dt_only)

    assert out["intent"] == "book_appointment"
    assert "appointment is confirmed" in out["answer"].lower()

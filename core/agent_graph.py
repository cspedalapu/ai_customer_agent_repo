from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Literal, Optional, TypedDict
import re

from langgraph.graph import END, START, StateGraph

from .agent import answer_question
from .appointments import AppointmentRequest, AppointmentStore
from .config import Settings
from .name_parser import extract_name
from .session_store import get_session, update_session

Intent = Literal["book_appointment", "cancel_appointment", "list_appointments", "kb_query"]


class AgentState(TypedDict, total=False):
    session_id: str
    message: str
    intent: Intent
    answer: str
    payload: Dict[str, Any]


@dataclass
class AgentGraphRunner:
    settings: Settings
    kb: Any
    appointment_store: AppointmentStore

    def __post_init__(self) -> None:
        self.graph = _build_graph(self)

    def run(self, session_id: str, message: str) -> Dict[str, Any]:
        state: AgentState = {"session_id": session_id, "message": message}
        out = self.graph.invoke(state, config={"configurable": {"thread_id": session_id}})
        return {
            "answer": out.get("answer", "I don't have that information in my knowledge base."),
            "refusal": bool(out.get("payload", {}).get("refusal", False)),
            "sources": out.get("payload", {}).get("sources", []),
            "best_similarity": out.get("payload", {}).get("best_similarity"),
            "timings_ms": out.get("payload", {}).get("timings_ms", {}),
            "intent": out.get("intent"),
        }


def _build_graph(runner: AgentGraphRunner):
    graph = StateGraph(AgentState)
    graph.add_node("route", lambda s: _route_node(runner, s))
    graph.add_node("kb_query", lambda s: _kb_node(runner, s))
    graph.add_node("book_appointment", lambda s: _book_node(runner, s))
    graph.add_node("cancel_appointment", lambda s: _cancel_node(runner, s))
    graph.add_node("list_appointments", lambda s: _list_node(runner, s))

    graph.add_edge(START, "route")
    graph.add_conditional_edges(
        "route",
        lambda s: s["intent"],
        {
            "kb_query": "kb_query",
            "book_appointment": "book_appointment",
            "cancel_appointment": "cancel_appointment",
            "list_appointments": "list_appointments",
        },
    )
    graph.add_edge("kb_query", END)
    graph.add_edge("book_appointment", END)
    graph.add_edge("cancel_appointment", END)
    graph.add_edge("list_appointments", END)
    return graph.compile()


def _route_node(runner: AgentGraphRunner, state: AgentState) -> AgentState:
    session_id = state["session_id"]
    session = get_session(session_id)
    msg = (state.get("message") or "").strip().lower()

    if _wants_to_reset_flow(msg):
        update_session(
            session_id,
            pending_intent=None,
            pending_booking_phone=None,
            pending_booking_email=None,
            pending_booking_service_type=None,
        )
        return {"intent": "kb_query"}

    if any(k in msg for k in ("cancel appointment", "cancel booking", "cancel my", "rescind")):
        update_session(session_id, pending_intent="cancel_appointment")
        return {"intent": "cancel_appointment"}
    if any(k in msg for k in ("my booking", "my appointment", "list appointment", "status appointment", "check booking")):
        update_session(session_id, pending_intent="list_appointments")
        return {"intent": "list_appointments"}
    if any(k in msg for k in ("book", "appointment", "schedule", "slot")):
        update_session(session_id, pending_intent="book_appointment")
        return {"intent": "book_appointment"}

    if session.pending_intent in {"book_appointment", "cancel_appointment", "list_appointments"}:
        return {"intent": session.pending_intent}

    return {"intent": "kb_query"}


def _kb_node(runner: AgentGraphRunner, state: AgentState) -> AgentState:
    result = answer_question(runner.settings, runner.kb, state.get("message", ""))
    return {"answer": result["answer"], "payload": result}


def _book_node(runner: AgentGraphRunner, state: AgentState) -> AgentState:
    session_id = state["session_id"]
    message = state.get("message", "")
    session = get_session(session_id)

    name = session.name or extract_name(message)
    if not name:
        update_session(session_id, pending_intent="book_appointment")
        return {"answer": "To book your appointment, may I have your full name first?", "payload": {"refusal": False}}
    if not session.name:
        update_session(session_id, name=name, stage="active")

    email = _extract_email(message) or session.pending_booking_email or ""
    requested_slot = _extract_slot(message)
    slot_service = _service_from_slot(requested_slot)
    service_type = _extract_service_type(message) or slot_service or session.pending_booking_service_type

    update_session(
        session_id,
        pending_intent="book_appointment",
        pending_booking_phone=None,
        pending_booking_email=email or None,
        pending_booking_service_type=service_type or None,
    )

    if not email:
        return {
            "answer": "Great, please share the best email address for your appointment confirmation.",
            "payload": {"refusal": False},
        }

    if not service_type:
        return {
            "answer": (
                "What service do you need an appointment for? "
                "Please choose: `dl_appointment`, `state_id`, or `renewal`."
            ),
            "payload": {"refusal": False},
        }

    slots = runner.appointment_store.list_open_slots(service_type=service_type)
    if not slots:
        return {
            "answer": "I could not find open slots for that service right now. Try a different service type.",
            "payload": {"refusal": False},
        }

    # Accept shorthand choices such as "1", "first one", or just "YYYY-MM-DD HH:MM".
    if not requested_slot:
        requested_slot = _resolve_slot_choice(message, slots)

    if not requested_slot:
        options = _format_slot_options(slots, limit=3)
        return {
            "answer": f"Please pick one of these available slots:\n{options}",
            "payload": {"refusal": False},
        }

    if requested_slot not in slots:
        options = _format_slot_options(slots, limit=3)
        return {
            "answer": f"That slot is unavailable. Please choose one of:\n{options}",
            "payload": {"refusal": False},
        }

    booking = runner.appointment_store.create_booking(
        AppointmentRequest(
            service_type=service_type,
            customer_name=name,
            customer_email=email,
            customer_phone="",
            slot=requested_slot,
        )
    )
    update_session(
        session_id,
        pending_intent=None,
        pending_booking_phone=None,
        pending_booking_email=None,
        pending_booking_service_type=None,
    )
    return {
        "answer": (
            f"You're all set. Your appointment is confirmed.\n"
            f"Booking ID: {booking['booking_id']}\n"
            f"Service: {booking['service_type']}\n"
            f"Slot: {booking['slot']}\n"
            f"Email: {booking.get('customer_email', email)}"
        ),
        "payload": {"refusal": False, "booking": booking},
    }


def _cancel_node(runner: AgentGraphRunner, state: AgentState) -> AgentState:
    session_id = state["session_id"]
    msg = state.get("message", "")
    m = re.search(r"\bAPT-[A-Z0-9]{10}\b", msg.upper())
    if not m:
        update_session(session_id, pending_intent="cancel_appointment")
        return {
            "answer": "Please provide your booking ID in this format: APT-XXXXXXXXXX",
            "payload": {"refusal": False},
        }
    booking_id = m.group(0)
    ok = runner.appointment_store.cancel_booking(booking_id)
    if not ok:
        return {"answer": "I could not find an active booking with that ID.", "payload": {"refusal": False}}
    update_session(session_id, pending_intent=None)
    return {"answer": f"Your appointment {booking_id} has been cancelled.", "payload": {"refusal": False}}


def _list_node(runner: AgentGraphRunner, state: AgentState) -> AgentState:
    session_id = state["session_id"]
    email = _extract_email(state.get("message", ""))
    if not email:
        update_session(session_id, pending_intent="list_appointments")
        return {
            "answer": "Please share the email address used for your booking so I can look it up.",
            "payload": {"refusal": False},
        }
    items = runner.appointment_store.bookings_for_email(email)
    if not items:
        return {"answer": "I couldn't find active appointments for that email address.", "payload": {"refusal": False}}
    update_session(session_id, pending_intent=None)
    lines = [f"- {b['booking_id']} | {b['service_type']} | {b['slot']}" for b in items]
    return {"answer": "Here are your active appointments:\n" + "\n".join(lines), "payload": {"refusal": False}}


def _extract_phone(text: str) -> str:
    digits = "".join(ch for ch in (text or "") if ch.isdigit())
    if len(digits) >= 10:
        return digits[-10:]
    return ""


def _extract_email(text: str) -> str:
    m = re.search(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", text or "", re.IGNORECASE)
    return m.group(0).strip().lower() if m else ""


def _extract_service_type(text: str) -> Optional[str]:
    t = (text or "").lower()
    if "dl_appointment" in t:
        return "dl_appointment"
    if "state_id" in t:
        return "state_id"
    if "renewal" in t:
        return "renewal"
    if "renew" in t:
        return "renewal"
    if "state id" in t or "id card" in t:
        return "state_id"
    if "driver license" in t or "driver licence" in t or "dl" in t:
        return "dl_appointment"
    return None


def _extract_slot(text: str) -> str:
    m = re.search(r"(dl_appointment|state_id|renewal)\s*\|\s*\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}", text or "", re.IGNORECASE)
    return m.group(0).lower() if m else ""


def _extract_datetime(text: str) -> str:
    m = re.search(r"\b\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}\b", text or "")
    return m.group(0) if m else ""


def _parse_slot_index_choice(text: str) -> Optional[int]:
    t = (text or "").strip().lower()
    if not t:
        return None

    # Bare numeric choice: "1", "2"
    m = re.fullmatch(r"\s*(\d{1,2})\s*", t)
    if m:
        return int(m.group(1))

    # "option 1", "slot 2", "pick 3", etc.
    m = re.search(r"\b(?:option|slot|pick|choose|select)\s*(\d{1,2})\b", t)
    if m:
        return int(m.group(1))

    # Common ordinals.
    if "first" in t:
        return 1
    if "second" in t:
        return 2
    if "third" in t:
        return 3
    if "fourth" in t:
        return 4
    if "fifth" in t:
        return 5
    return None


def _resolve_slot_choice(text: str, slots: list[str]) -> str:
    if not slots:
        return ""

    idx = _parse_slot_index_choice(text)
    if idx is not None and 1 <= idx <= len(slots):
        return slots[idx - 1]

    dt = _extract_datetime(text)
    if dt:
        for slot in slots:
            if dt in slot:
                return slot

    return ""


def _format_slot_options(slots: list[str], limit: int = 3) -> str:
    chosen = slots[:limit]
    return "\n".join(f"{i}. {slot}" for i, slot in enumerate(chosen, start=1))


def _service_from_slot(slot: str) -> Optional[str]:
    if not slot:
        return None
    return slot.split("|", 1)[0].strip().lower()


def _wants_to_reset_flow(message: str) -> bool:
    msg = (message or "").lower()
    return any(
        token in msg
        for token in (
            "never mind",
            "nevermind",
            "start over",
            "new topic",
            "forget it",
            "stop booking",
        )
    )

from src.healthtech_ingest import Appointment, notification_for


def test_cancelled_appointment_gets_reschedule_message() -> None:
    appointment = Appointment("p-1", "a-1", "cancelled", "2026-09-03 09:30")
    assert notification_for(appointment) == (
        "Appointment a-1 was cancelled. Contact the clinic to reschedule."
    )

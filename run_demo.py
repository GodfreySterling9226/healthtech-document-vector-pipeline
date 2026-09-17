import os

from src.healthtech_ingest import Appointment, InfraiClient, notification_for


def main() -> None:
    appointment = Appointment("p-104", "a-882", "confirmed", "2026-09-03 09:30")
    notification = notification_for(appointment)
    print(notification)
    if os.environ.get("INFRAI_API_KEY"):
        client = InfraiClient()
        embedding = client.embed(notification or "")
        print({"embedding_dimension": len(embedding)})


if __name__ == "__main__":
    main()

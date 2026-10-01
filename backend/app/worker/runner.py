from redis import Redis
from rq import Queue, Worker

from app.core.config import get_settings
from app.services.scans import QUEUE_NAME


def main() -> None:
    settings = get_settings()
    connection = Redis.from_url(settings.redis_url, socket_connect_timeout=5, socket_timeout=5)
    connection.ping()
    queue = Queue(QUEUE_NAME, connection=connection, default_timeout=settings.scan_job_timeout_seconds)
    Worker([queue], connection=connection).work(with_scheduler=False)


if __name__ == "__main__":
    main()

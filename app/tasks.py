from .celery_app import celery_app
from .database import SessionLocal
from .models import DocumentTask
from datetime import datetime, timezone
import re


@celery_app.task
def process_document(task_id: int, content: str):
    db = SessionLocal()
    try:
        task = db.query(DocumentTask).filter(DocumentTask.id == task_id).first()
        if not task:
            db.close()
            return

        task.status = "processing"
        db.commit()

        words = content.split()
        word_count = len(words)
        sentence_count = len(re.findall(r'[.!?]+', content))
        char_count = len(content)
        reading_time_minutes = round(word_count / 200, 2)

        word_freq = {}
        for word in words:
            word = word.lower().strip('.,!?";:')
            if len(word) > 3:
                word_freq[word] = word_freq.get(word, 0) + 1

        top_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:10]

        task.status = "completed"
        task.result = {
            "word_count": word_count,
            "sentence_count": sentence_count,
            "char_count": char_count,
            "reading_time_minutes": reading_time_minutes,
            "top_words": dict(top_words)
        }
        task.completed_at = datetime.now(timezone.utc)
        db.commit()

    except Exception as e:
        if task:
            task.status = "failed"
            task.error_message = str(e)
            db.commit()
    finally:
        db.close()
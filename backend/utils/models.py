from sqlalchemy import Column, Integer, Sequence, String

from .database import Base, SessionLocal, engine


class LlmData(Base):
    __tablename__ = "llm_data"

    id = Column(Integer, Sequence("llm_data_id_seq"), primary_key=True)
    prompt = Column(String)
    response = Column(String)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


def create_llm_data(prompt: str, response: str) -> LlmData:
    """Store one prompt/response pair, the raw material for later fine-tuning."""
    with SessionLocal() as db:
        record = LlmData(prompt=prompt, response=response)
        db.add(record)
        db.commit()
        db.refresh(record)
        return record

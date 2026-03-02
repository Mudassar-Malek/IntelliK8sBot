"""Database configuration and models."""

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.config import get_settings

settings = get_settings()

engine = create_async_engine(settings.database_url, echo=settings.debug)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

Base = declarative_base()


class Conversation(Base):
    """Stores conversation history."""

    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(255), index=True, nullable=False)
    role = Column(String(50), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    extra_data = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class K8sOperation(Base):
    """Tracks Kubernetes operations performed by the bot."""

    __tablename__ = "k8s_operations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(255), index=True, nullable=False)
    operation_type = Column(String(100), nullable=False)
    resource_type = Column(String(100), nullable=False)
    resource_name = Column(String(255), nullable=True)
    namespace = Column(String(255), nullable=True)
    status = Column(String(50), nullable=False)  # success, failed, pending
    details = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Alert(Base):
    """Stores cluster alerts and recommendations."""

    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    alert_type = Column(String(100), nullable=False)
    severity = Column(String(50), nullable=False)  # critical, warning, info
    resource_type = Column(String(100), nullable=True)
    resource_name = Column(String(255), nullable=True)
    namespace = Column(String(255), nullable=True)
    message = Column(Text, nullable=False)
    recommendation = Column(Text, nullable=True)
    acknowledged = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)


async def init_db():
    """Initialize the database."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db() -> AsyncSession:
    """Get database session."""
    async with async_session() as session:
        yield session

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String

from .database import Base


class Staff(Base):
	__tablename__ = "staff"

	id = Column(Integer, primary_key=True, index=True)
	first_name = Column(String, nullable=False)
	last_name = Column(String, nullable=False)
	email = Column(String, unique=True, index=True, nullable=False)
	phone = Column(String, nullable=True)
	role = Column(String, nullable=False)
	department = Column(String, nullable=False)
	is_active = Column(Boolean, default=True, nullable=False)
	assigned_task = Column(String, nullable=True)
	created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
	updated_at = Column(
		DateTime,
		default=datetime.utcnow,
		onupdate=datetime.utcnow,
		nullable=False,
	)

	@property
	def full_name(self) -> str:
		return f"{self.first_name} {self.last_name}"

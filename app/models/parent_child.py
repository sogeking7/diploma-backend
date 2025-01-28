from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from app.db.session import Base

class ParentChild(Base):
    __tablename__ = "parent_child_relationships"

    id = Column(Integer, primary_key=True, index=True)
    parent_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    child_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # These back_populates will reference two separate relationships in the User model
    parent = relationship("User", foreign_keys=[parent_id], back_populates="parent_links")
    child = relationship("User", foreign_keys=[child_id], back_populates="child_links")

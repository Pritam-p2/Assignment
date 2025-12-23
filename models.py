from sqlalchemy import Column, Integer, Numeric
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Wallet(Base):
    __tablename__ = "wallets"

    id = Column(Integer, primary_key=True, index=True)
    balance = Column(Numeric(12, 2), nullable=False)

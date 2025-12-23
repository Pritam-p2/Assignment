from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from decimal import Decimal

from database import SessionLocal, engine
from models import Base, Wallet

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

app = FastAPI()


@app.post("/accounts")
def create_account(starting_balance: Decimal = 100, db: Session = Depends(get_db)):
    wallet = Wallet(balance=starting_balance)
    db.add(wallet)
    db.commit()
    db.refresh(wallet)
    return {"user_id": wallet.id, "balance": wallet.balance}


@app.get("/accounts/{user_id}")
def get_balance(user_id: int, db: Session = Depends(get_db)):
    wallet = db.get(Wallet, user_id)
    if not wallet:
        raise HTTPException(status_code=404, detail="User not found")
    return {"user_id": wallet.id, "balance": wallet.balance}


@app.post("/transfer")
def transfer_money(
    from_user_id: int,
    to_user_id: int,
    amount: Decimal,
    db: Session = Depends(get_db),
):
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Invalid amount")

    try:
        sender = (
            db.execute(
                select(Wallet)
                .where(Wallet.id == from_user_id)
                .with_for_update()
            )
            .scalars()
            .first()
        )

        receiver = (
            db.execute(
                select(Wallet)
                .where(Wallet.id == to_user_id)
                .with_for_update()
            )
            .scalars()
            .first()
        )

        if not sender or not receiver:
            raise HTTPException(status_code=404, detail="User not found")

        if sender.balance < amount:
            raise HTTPException(status_code=400, detail="Insufficient balance")

        # DEBIT from sender
        sender.balance -= amount

        # CREDIT to receiver
        receiver.balance += amount

        db.commit()  # save to DB

        return {"message": "Transfer successful"}

    except Exception as e:
        db.rollback()  # rollback everything
        raise HTTPException(status_code=500, detail=str(e))

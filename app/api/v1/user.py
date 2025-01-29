from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile
from sqlalchemy.orm import Session
from typing import List
from app import schemas, crud
from app.api.dependencies import get_db, get_current_active_user, get_current_active_admin
from app.models.user import User
from app.models.user_embedding import UserEmbedding
from app.schemas import UserOut
from app.utils.pinecone_face import get_pinecone_index
from deepface import DeepFace
import numpy as np
import tempfile

router = APIRouter()

@router.get("/me", response_model=UserOut, summary="Get Current User")
def read_current_user(
    current_user: User = Depends(get_current_active_user)
) -> UserOut:
    """
    Retrieve the authenticated user's information.

    - **current_user**: User object retrieved from the access token.
    """
    return current_user

@router.post("/verify", status_code=200)
async def verify_user_image(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Verify a user's identity by comparing the uploaded image with embeddings stored in Pinecone.
    """
    try:
        # Save the uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp_file:
            temp_file.write(await file.read())
            temp_file_path = temp_file.name

        # Generate embedding for the uploaded image
        uploaded_embedding = DeepFace.represent(
            img_path=temp_file_path,
            model_name="Facenet512"
        )[0]["embedding"]

        # Normalize and convert embedding to Python list
        uploaded_embedding = normalize_embedding(np.array(uploaded_embedding)).tolist()

        # Get Pinecone index
        pinecone_index = get_pinecone_index()

        # Query Pinecone for the top 10 closest matches
        query_result = pinecone_index.query(
            vector=uploaded_embedding,
            top_k=10,  # Fetch top 10 matches
            include_metadata=True
        )

        best_match = None
        highest_score = 0

        # Iterate through the matches to find the best match
        for match in query_result["matches"]:
            similarity_score = match["score"]
            user_id = match["metadata"]["user_id"]

            # print(f"Similarity Score: {similarity_score} for user_id: {user_id}")

            if similarity_score > 0.6 and similarity_score > highest_score:  # Adjust threshold as needed
                highest_score = similarity_score
                best_match = user_id

        if best_match:
            # Fetch the user details from the database
            user = db.query(User).filter(User.id == best_match).first()
            if user:
                return {
                    "verified": True,
                    "user": {
                        "id": user.id,
                        "first_name": user.first_name,
                        "last_name": user.last_name
                    },
                    "similarity_score": highest_score
                }

        # If no match exceeds the threshold
        return {"verified": False, "message": "No matching user found."}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Verification failed: {str(e)}")


def normalize_embedding(embedding):
    """
    Normalize the embedding vector to ensure consistency in comparisons.
    """
    return embedding / np.linalg.norm(embedding)


@router.post("/users/{user_id}/upload-image", status_code=status.HTTP_201_CREATED)
def upload_user_image(
        user_id: int,
        file: UploadFile = File(...),
        db: Session = Depends(get_db),
        current_admin: User = Depends(get_current_active_admin)
):
    """
    Upload and process an image for a user, and store the embedding in Pinecone.
    """
    # Validate user existence
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Process the image with DeepFace
    try:
        temp_file_path = f"/tmp/{file.filename}"
        with open(temp_file_path, "wb") as f:
            f.write(file.file.read())

        # Generate embedding
        embedding = DeepFace.represent(img_path=temp_file_path, model_name="Facenet512")[0]["embedding"]

        # Create a unique vector ID for Pinecone
        vector_id = f"user-{user_id}"

        pinecone_index = get_pinecone_index()
        # Store the embedding in Pinecone
        pinecone_index.upsert([(vector_id, embedding, {"user_id": user_id})])

        # Save the vector ID in PostgreSQL
        new_embedding = UserEmbedding(user_id=user_id, vector_id=vector_id)
        db.add(new_embedding)
        db.commit()
        db.refresh(new_embedding)

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to process image: {str(e)}"
        )

    return {"message": "Image processed and embedding stored successfully in Pinecone"}


@router.post("/users/", response_model=schemas.UserOut)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_user(db=db, user=user)


@router.get("/users/", response_model=List[schemas.UserOut])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db),
               current_user: User = Depends(get_current_active_user)):
    users = crud.get_users(db, skip=skip, limit=limit)
    return users


@router.get("/users/{user_id}", response_model=schemas.UserOut)
def read_user(user_id: int, db: Session = Depends(get_db),
              current_user: User = Depends(get_current_active_user)):
    db_user = crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@router.put("/users/{user_id}", response_model=schemas.UserOut)
def update_user(user_id: int, updates: schemas.UserUpdate, db: Session = Depends(get_db),
                current_user: User = Depends(get_current_active_user)):
    db_user = crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return crud.update_user(db=db, db_user=db_user, updates=updates)


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, db: Session = Depends(get_db),
                current_user: User = Depends(get_current_active_user)):
    db_user = crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    crud.delete_user(db=db, db_user=db_user)
    return

from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Optional, Dict
import uuid
from datetime import datetime

# In a real application, these models would be in a separate `models.py` file.
# from .models import (
#     Proposal, ProposalCreate, ProposalDetail, ProposalStatus, Commitment, Milestone
# )
from pydantic import BaseModel, Field, EmailStr
from enum import Enum


# --- Pydantic Models (should be in models.py) ---

class ProposalStatus(str, Enum):
    """Enum for the status of a proposal."""
    DRAFT = "DRAFT"
    COMMITTED = "COMMITTED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"


class Commitment(BaseModel):
    """Represents a stakeholder's commitment to a proposal."""
    stakeholder_email: EmailStr
    committed_at: datetime


class Milestone(BaseModel):
    """Represents a key milestone for a proposal."""
    title: str
    due_date: datetime


class ProposalBase(BaseModel):
    """Base model for a proposal's core fields."""
    title: str = Field(..., min_length=3, max_length=100)
    description: str = Field(..., min_length=10)
    success_metric: str


class ProposalCreate(ProposalBase):
    """Model for creating a new proposal."""
    stakeholder_emails: List[EmailStr]


class Proposal(ProposalBase):
    """Model representing a proposal in the system (e.g., for list views)."""
    id: str
    owner_id: str
    status: ProposalStatus
    stakeholder_emails: List[EmailStr]

    class Config:
        orm_mode = True


class ProposalDetail(Proposal):
    """Full proposal model including nested commitments and milestones."""
    commitments: List[Commitment] = []
    milestones: List[Milestone] = []

# --- End of Models ---


# --- API Router Setup ---

router = APIRouter(
    prefix="/api/v1",
    tags=["Proposals"],
    responses={404: {"description": "Not found"}},
)


# --- In-Memory Database ---

# We use a dictionary to store proposal details, with the proposal ID as the key.
db: Dict[str, ProposalDetail] = {}

# Pre-populate with some dummy data for demonstration
def setup_dummy_data():
    proposal1_id = str(uuid.uuid4())
    db[proposal1_id] = ProposalDetail(
        id=proposal1_id,
        title="Project Phoenix",
        description="Rebuild the customer portal from scratch for better performance.",
        success_metric="Achieve a 20% increase in user engagement.",
        owner_id="user1",
        status=ProposalStatus.COMMITTED,
        stakeholder_emails=["stakeholder1@example.com", "stakeholder2@example.com"],
        commitments=[
            Commitment(stakeholder_email="stakeholder1@example.com", committed_at=datetime.utcnow()),
            Commitment(stakeholder_email="stakeholder2@example.com", committed_at=datetime.utcnow())
        ],
        milestones=[
            Milestone(title="Design phase complete", due_date=datetime.utcnow()),
        ]
    )
    proposal2_id = str(uuid.uuid4())
    db[proposal2_id] = ProposalDetail(
        id=proposal2_id,
        title="Marketing Campaign Q3",
        description="Launch a new social media campaign to boost brand awareness.",
        success_metric="Increase lead generation by 15%.",
        owner_id="user1",
        status=ProposalStatus.DRAFT,
        stakeholder_emails=["stakeholder1@example.com", "marketing_lead@example.com"],
        commitments=[],
        milestones=[]
    )
    proposal3_id = str(uuid.uuid4())
    db[proposal3_id] = ProposalDetail(
        id=proposal3_id,
        title="Internal Tool Upgrade",
        description="Upgrade the internal CRM to the latest version.",
        success_metric="Reduce ticket resolution time by 10%.",
        owner_id="user2", # Belongs to a different user
        status=ProposalStatus.DRAFT,
        stakeholder_emails=["stakeholder3@example.com"],
        commitments=[],
        milestones=[]
    )

setup_dummy_data()


# --- Simulated Authentication Dependency ---

async def get_current_user() -> Dict[str, str]:
    """
    Simulates retrieving the current authenticated user.
    In a real app, this would decode a JWT token or validate a session.
    """
    return {"user_id": "user1", "email": "stakeholder1@example.com"}


# --- API Endpoints ---

@router.get("/proposals", response_model=List[Proposal])
async def get_all_proposals(
    status: Optional[ProposalStatus] = None,
    current_user: dict = Depends(get_current_user)
):
    """
    Retrieve all proposals for the authenticated user.
    Can be filtered by status, e.g., ?status=COMMITTED.
    """
    user_id = current_user["user_id"]
    user_proposals = [p for p in db.values() if p.owner_id == user_id]

    if status:
        return [p for p in user_proposals if p.status == status]

    return user_proposals


@router.post("/proposals", response_model=Proposal, status_code=status.HTTP_201_CREATED)
async def create_proposal(
    proposal_in: ProposalCreate,
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new proposal.
    Body includes title, description, success_metric, and stakeholder emails.
    """
    user_id = current_user["user_id"]
    new_proposal_id = str(uuid.uuid4())

    # Create the full proposal detail object to store in our "DB"
    db_proposal = ProposalDetail(
        id=new_proposal_id,
        owner_id=user_id,
        status=ProposalStatus.DRAFT,
        **proposal_in.dict()
    )

    db[new_proposal_id] = db_proposal
    return db_proposal


@router.get("/proposals/{proposalId}", response_model=ProposalDetail)
async def get_proposal_by_id(proposalId: str):
    """
    Get detailed information for a single proposal, including its
    commitments and milestones.
    """
    proposal = db.get(proposalId)
    if not proposal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Proposal with ID {proposalId} not found"
        )
    return proposal


@router.post("/proposals/{proposalId}/commit", response_model=Commitment)
async def commit_to_proposal(
    proposalId: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Allows an invited user to make a commitment (say 'Yes') to a proposal.
    """
    proposal = db.get(proposalId)
    if not proposal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Proposal with ID {proposalId} not found"
        )

    user_email = current_user["email"]

    # Check if the user is an invited stakeholder
    if user_email not in proposal.stakeholder_emails:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not an invited stakeholder for this proposal."
        )

    # Check if the user has already committed
    if any(c.stakeholder_email == user_email for c in proposal.commitments):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You have already committed to this proposal."
        )

    # Create and add the new commitment
    new_commitment = Commitment(
        stakeholder_email=user_email,
        committed_at=datetime.utcnow()
    )
    proposal.commitments.append(new_commitment)

    # Optional: Update proposal status if all stakeholders have committed
    committed_emails = {c.stakeholder_email for c in proposal.commitments}
    if set(proposal.stakeholder_emails).issubset(committed_emails):
        proposal.status = ProposalStatus.COMMITTED

    return new_commitment
import uuid
import random
from datetime import datetime
from fastapi import APIRouter, HTTPException, status
from typing import List

# Import models from the models.py file
import models

#  In-Memory Database Simulation 
# In a production application, this dictionary would be replaced with a
# connection to a real database (e.g., PostgreSQL, MySQL) managed by an ORM
# like SQLAlchemy. A service layer would contain the database interaction logic.
DB_RECIPES: dict[uuid.UUID, models.RecipeInDB] = {}

def _populate_initial_data():
    """Helper function to add some initial data to our in-memory DB."""
    recipe1_id = uuid.uuid4()
    DB_RECIPES[recipe1_id] = models.RecipeInDB(
        id=recipe1_id,
        name="Classic Margherita Pizza",
        ingredients=["Pizza Dough", "Tomato Sauce", "Fresh Mozzarella", "Basil", "Olive Oil"],
        instructions="1. Preheat oven to 250°C (475°F). 2. Roll out dough. 3. Spread sauce, add cheese and basil. 4. Bake for 10-12 minutes.",
        prep_time_minutes=15,
        cook_time_minutes=12
    )
    
    recipe2_id = uuid.uuid4()
    DB_RECIPES[recipe2_id] = models.RecipeInDB(
        id=recipe2_id,
        name="Simple Lemon Herb Chicken",
        ingredients=["Chicken Breasts", "Lemon", "Rosemary", "Thyme", "Garlic", "Olive Oil", "Salt", "Pepper"],
        instructions="1. Season chicken. 2. Sear in a hot pan with olive oil. 3. Add herbs, garlic, and lemon slices. 4. Roast in oven at 200°C (400°F) for 20 minutes.",
        prep_time_minutes=10,
        cook_time_minutes=25
    )

_populate_initial_data()
#  End Database Simulation 

# Create a new router instance. This helps organize endpoints.
router = APIRouter()

#  Custom Exception 
class RecipeNotFoundException(HTTPException):
    """Custom exception to be raised when a recipe is not found."""
    def __init__(self, recipe_id: uuid.UUID):
        detail = f"Recipe with ID {recipe_id} not found."
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)

#  API Endpoints for Recipes 

@router.post(
    "/recipes",
    response_model=models.RecipeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a New Recipe",
    tags=["Recipes"]
)
def create_recipe(recipe_in: models.RecipeCreate) -> models.RecipeResponse:
    """
    Creates a new recipe and stores it.
    The `recipe_in` body is validated against the `RecipeCreate` Pydantic model.
    """
    new_recipe = models.RecipeInDB(**recipe_in.model_dump())
    DB_RECIPES[new_recipe.id] = new_recipe
    return new_recipe

@router.get(
    "/recipes",
    response_model=List[models.RecipeResponse],
    summary="Get All Recipes",
    tags=["Recipes"]
)
def get_all_recipes() -> List[models.RecipeResponse]:
    """Retrieves a list of all available recipes."""
    return sorted(list(DB_RECIPES.values()), key=lambda r: r.created_at, reverse=True)

@router.get(
    "/recipes/random",
    response_model=models.RecipeResponse,
    summary="Get a Random Recipe Suggestion",
    tags=["Recipes"]
)
def get_random_recipe() -> models.RecipeResponse:
    """
    The core 'What's for Dinner?' feature. Returns a random recipe from the database.
    """
    if not DB_RECIPES:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No recipes available to choose from. Please add a recipe first."
        )
    random_recipe_id = random.choice(list(DB_RECIPES.keys()))
    return DB_RECIPES[random_recipe_id]

@router.get(
    "/recipes/{recipe_id}",
    response_model=models.RecipeResponse,
    summary="Get a Specific Recipe",
    tags=["Recipes"],
    responses={404: {"model": models.Message, "description": "The recipe was not found"}}
)
def get_recipe_by_id(recipe_id: uuid.UUID) -> models.RecipeResponse:
    """Retrieves the details of a specific recipe by its unique ID."""
    recipe = DB_RECIPES.get(recipe_id)
    if not recipe:
        raise RecipeNotFoundException(recipe_id)
    return recipe

@router.put(
    "/recipes/{recipe_id}",
    response_model=models.RecipeResponse,
    summary="Update a Recipe",
    tags=["Recipes"],
    responses={404: {"model": models.Message, "description": "The recipe was not found"}}
)
def update_recipe(recipe_id: uuid.UUID, recipe_update: models.RecipeUpdate) -> models.RecipeResponse:
    """
    Updates an existing recipe's details. Only the provided fields will be updated.
    """
    existing_recipe = DB_RECIPES.get(recipe_id)
    if not existing_recipe:
        raise RecipeNotFoundException(recipe_id)
    
    update_data = recipe_update.model_dump(exclude_unset=True)
    updated_recipe = existing_recipe.model_copy(update=update_data)
    updated_recipe.updated_at = datetime.utcnow()
    
    DB_RECIPES[recipe_id] = updated_recipe
    return updated_recipe

@router.delete(
    "/recipes/{recipe_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a Recipe",
    tags=["Recipes"],
    responses={404: {"model": models.Message, "description": "The recipe was not found"}}
)
def delete_recipe(recipe_id: uuid.UUID) -> None:
    """Deletes a recipe from the database by its unique ID."""
    if recipe_id not in DB_RECIPES:
        raise RecipeNotFoundException(recipe_id)
    
    del DB_RECIPES[recipe_id]
    # A 204 response must not contain a body, so we return None.
    return None
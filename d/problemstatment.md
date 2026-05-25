## Problem Statement: AI‑Powered Restaurant Recommendation System (Zomato Use Case)

Build an AI-powered restaurant recommendation service inspired by Zomato. The system should suggest restaurants based on a user’s preferences by combining **structured restaurant data** with a **Large Language Model (LLM)** to generate personalized, human-friendly recommendations.

## Objective

Design and implement an application that:
- **Accepts user preferences** (e.g., location, budget, cuisine, minimum rating)
- **Uses a real-world restaurant dataset**
- **Uses an LLM** to rank and explain recommendations in natural language
- **Presents results clearly** in a user-friendly format

## Dataset

Use the Zomato restaurant recommendation dataset from Hugging Face:
- `https://huggingface.co/datasets/ManikaSaini/zomato-restaurant-recommendation`

## Expected Workflow

### 1) Data ingestion and preprocessing
- Load the dataset and preprocess it (clean missing values, normalize fields, handle types).
- Extract relevant fields, for example:
  - Restaurant name
  - Location / city
  - Cuisine(s)
  - Cost / price range
  - Rating (and/or number of votes, if available)

### 2) User input collection
Collect user preferences such as:
- **Location** (e.g., Delhi, Bangalore)
- **Budget** (e.g., low / medium / high or a numeric range)
- **Cuisine** (e.g., Italian, Chinese)
- **Minimum rating**
- **Optional preferences** (e.g., family-friendly, quick service, ambience)

### 3) Retrieval + prompt preparation (integration layer)
- Filter the dataset using the user’s criteria (hard constraints).
- Select a reasonable shortlist of candidates to send to the LLM.
- Construct a prompt that:
  - Provides the user preferences
  - Includes the shortlisted restaurant data in a structured form
  - Asks the LLM to compare, rank, and justify choices

### 4) Recommendation engine (LLM)
Use the LLM to:
- **Rank** the shortlisted restaurants
- **Explain** why each option matches the user’s preferences
- **Optionally** provide a short summary and trade-offs (e.g., “best value” vs “best rated”)

### 5) Output display
Display the top recommendations with:
- **Restaurant name**
- **Cuisine**
- **Rating**
- **Estimated cost / price range**
- **AI-generated explanation** (brief and specific to the user’s inputs)

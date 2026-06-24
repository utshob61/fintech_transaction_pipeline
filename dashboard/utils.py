"""
utils.py
--------
Small helper layer the dashboard uses to talk to the FastAPI backend.
Keeping HTTP calls out of app.py keeps the Streamlit file focused on
layout/UI.
"""

import os

import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

API_BASE_URL = os.getenv("DASHBOARD_API_URL", "http://localhost:8000")


@st.cache_data(ttl=30)
def fetch_json(path: str, params: dict | None = None):
    """GET a JSON endpoint from the backend API. Cached for 30s so rapid
    filter changes don't hammer the database."""
    try:
        response = requests.get(f"{API_BASE_URL}{path}", params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Could not reach the backend API at {API_BASE_URL}{path} — {e}")
        return None


def format_currency(value: float) -> str:
    return f"৳{value:,.2f}"

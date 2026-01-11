import os
from supabase import create_client, Client
from dotenv import load_dotenv
import streamlit as st
from datetime import date

load_dotenv(".env")
#SUPABASE_KEY = os.getenv("KEY")
#SUPABASE_URL = os.getenv("URL")

@st.cache_resource
def get_supabase():
    return create_client(os.getenv("URL"), os.getenv("KEY"))
supabase = get_supabase()

#supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

sb = supabase.table("users_db")

# --- READ -> cache_data ---
@st.cache_data(ttl=60)
def get_active_races():
    today = date.today().isoformat()
    return (
        supabase.table("races")
        .select("*")
        .gte("date", today)
        .order("date")
        .execute()
        .data
    )

@st.cache_data(ttl=60)
def get_positions_for_race(race_id: int):
    return (
        supabase.table("positions")
        .select("*")
        .eq("race_id", race_id)
        .order("id")
        .execute()
        .data
    )

@st.cache_data(ttl=30)
def get_race_notes(race_id: int) -> str:
    response = (
        supabase.table("races")
        .select("notes")
        .eq("id", race_id)
        .single()
        .execute()
    )
    return response.data["notes"] if response.data else ""


@st.cache_data(ttl=60)
def fetch_all_users():
    return (
        supabase.table("users_db")
        .select("*")
        .order("name")
        .execute()
        .data
    )

# --- WRITE -> no cache ---
def insert_user(username, name, password):
    supabase.table("users_db").insert({
        "username": username,
        "name": name,
        "password": password
    }).execute()

    st.cache_data.clear()   # 🔥 DŮLEŽITÉ

def signup_user(race_id, position_id, user_id):
    supabase.table("signups").insert({
        "race_id": race_id,
        "position_id": position_id,
        "user_id": user_id
    }).execute()

    st.cache_data.clear()  # 🔥 DŮLEŽITÉ

# --- Zbytek ---

#def insert_user(username, name, password):
#    response = supabase.table("users_db").insert({
#    "username": username,
#    "name": name,
#    "password": password
#}).execute()
    
#def fetch_all_users():
#    response = (supabase.table("users_db")
#    .select("*")
#    .execute()
#)
#    return response.data

def get_user_id(username):

    response = (
        supabase.table("users_db")
        .select("id")
        .eq("username", username)
        .execute()
    )

    return response.data[0]["id"]

def fetch_role(username):
    response = (supabase.table("users_db") 
        .select("role") 
        .eq("username", username) 
        .execute()
    )
    if response.data:
        return response.data[0]["role"]
    return None

def get_races():
    response = (
        supabase.table("races")
        .select("*")
        .order("date")
        .execute()
    )
    return response.data

def create_race(name, date, location, db_race_id):
    supabase.table("races").insert({
        "name": name,
        "date": str(date),
        "location": location,
        "race_id": db_race_id
    }).execute()

def delete_race(race_id):
    supabase.table("races") \
        .delete() \
        .eq("id", race_id) \
        .execute()

def get_race(race_id):
    response = (
        supabase.table("races")
        .select("*")
        .eq("id", race_id)
        .single()
        .execute()
    )
    return response.data

#def get_positions_for_race(race_id):
#    response = (
#        supabase.table("positions")
#        .select("id, name, capacity")
#        .eq("race_id", race_id)
#        .execute()
#    )
#    return response.data

def create_position(race_id, name, capacity):
    supabase.table("positions").insert({
        "race_id": race_id,
        "name": name,
        "capacity": capacity
    }).execute()

#def signup_user(race_id, position_id, user_id):
#    supabase.table("signups").insert({
#        "race_id": race_id,
#        "position_id": position_id,
#        "user_id": user_id
#    }).execute()

def get_signups_for_position(position_id):
    response = (
        supabase.table("signups")
        .select("id, user_id, users_db(name)")
        .eq("position_id", position_id)
        .execute()
    )
    return response.data

def remove_signup(signup_id):
    supabase.table("signups").delete().eq("id", signup_id).execute()

def get_occupied_count(position_id):
    response = (
        supabase.table("signups")
        .select("id", count="exact")
        .eq("position_id", position_id)
        .execute()
    )
    return response.count

def is_user_signed_up_for_race(race_id, user_id):
    response = (
        supabase.table("signups")
        .select("id")
        .eq("race_id", race_id)
        .eq("user_id", user_id)
        .execute()
    )
    return len(response.data) > 0

def admin_add_user(race_id, position_id, user_id):
    supabase.table("signups").insert({
        "race_id": race_id,
        "position_id": position_id,
        "user_id": user_id
    }).execute()


def admin_remove_signup(signup_id):
    supabase.table("signups") \
        .delete() \
        .eq("id", signup_id) \
        .execute()

def get_all_users_simple():
    response = supabase.table("users_db") \
        .select("id, name") \
        .order("name") \
        .execute()
    return response.data

def get_all_users_stats():
    response = supabase.table("users_db") \
        .select("*") \
        .order("name") \
        .execute()
    return response.data

#def get_active_races():
#    today = date.today().isoformat()
#    response = (
#        supabase.table("races")
#        .select("*")
#        .gte("date", today)   # >= DNES
#        .order("date")
#        .execute()
#    )
#    return response.data


def get_archived_races():
    today = date.today().isoformat()
    response = (
        supabase.table("races")
        .select("*")
        .lt("date", today)    # < DNES
        .order("date", desc=True)
        .execute()
    )
    return response.data

def unsubscribe_user(race_id, user_id):
    supabase.table("signups") \
        .delete() \
        .eq("race_id", race_id) \
        .eq("user_id", user_id) \
        .execute()
    
def get_user_signup_for_race(race_id, user_id):
    response = (
        supabase.table("signups")
        .select("id, position_id")
        .eq("race_id", race_id)
        .eq("user_id", user_id)
        .execute()
    )

    if response and response.data:
        return response.data[0]
    return None

def get_user_signup_for_race2(race_id, user_id):
    response = (
        supabase.table("signups")
        .select("position_id")
        .eq("race_id", race_id)
        .eq("user_id", user_id)
        .limit(1)
        .execute()
    )

    if response.data and len(response.data) > 0:
        return response.data[0]   # vrátí dict
    return None                  # není přihlášen

def get_occupied_for_race(race_id):
    response = (
        supabase.table("signups")
        .select("id", count="exact")
        .eq("race_id", race_id)
        .execute()
    )
    return response.count or 0

def get_capacity_for_race(race_id):
    response = (
        supabase.table("positions")
        .select("capacity")
        .eq("race_id", race_id)
        .execute()
    )
    return sum(p["capacity"] for p in response.data)

def get_user_signup_with_position_name(race_id, user_id):
    # nejdřív zjistíme signup
    signup = (
        supabase.table("signups")
        .select("position_id")
        .eq("race_id", race_id)
        .eq("user_id", user_id)
        .limit(1)
        .execute()
    )

    if not signup.data:
        return None

    position_id = signup.data[0]["position_id"]

    # dotáhneme název pozice
    position = (
        supabase.table("positions")
        .select("name")
        .eq("id", position_id)
        .single()
        .execute()
    )

    return position.data["name"]

# Uložit poznámku k závodu
def update_race_notes(race_id, notes):
    response = (
        supabase.table("races")
        .update({"notes": notes})
        .eq("id", race_id)
        .execute()
    )
    return response

# Načíst poznámku k závodu
#def get_race_notes(race_id):
#    response = (
#        supabase.table("races")
#        .select("notes")
#        .eq("id", race_id)
#        .single()
#        .execute()
#    )
#    return response.data.get("notes") if response.data else ""




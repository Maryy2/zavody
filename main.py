import streamlit as st
import streamlit_authenticator as stauth
import streamlit_option_menu as option_menu
from datetime import datetime, date

import database as db

#page config
st.set_page_config(page_title="Závody 2025: Kamera + AK2 + Optika + Start", page_icon="⚙️", layout = "wide")
st.header("Závody 2025", divider="gray", )

hide_streamlit_style = """
    <style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

#----- authentikace -----
users = db.fetch_all_users()

credentials = {
    "usernames": {}
}

for user in users:
    credentials["usernames"][user["username"]] = {
        "name": user["name"],
        "password": user["password"]
    }

authenticator = stauth.Authenticate(credentials, "zavody_dashboard", "abcdef", 30)

name, authentication_status, username = authenticator.login("Přihlášení", 'main')

current_username = username
role = db.fetch_role(username=current_username)

if authentication_status == False:
    st.error("Nesprávné uživatelské jméno nebo heslo")

if authentication_status == None:
    st.warning("Prosím zadejte uživatelské jméno a heslo")

if authentication_status:
#----- sidebar -----  
    with st.sidebar:    
        st.title(f"{name}")
        if role == "admin":
            st.badge("Admin", icon=":material/check:", color="yellow")

        st.divider()

        if role == "admin":
            page = st.sidebar.selectbox("Možnosti", ["Domů", "Správa závodů ⚙️"])
            st.divider()
        else:
            page = ("Domů")

        authenticator.logout("Odhlásit se")      

    #----- main page -----
    current_user_id = db.get_user_id(username)
    # admin - zadání závodu
    if page == "Správa závodů ⚙️" and role == "admin":
        st.subheader("Vytvořit závod")

        race_name = st.text_input("Název závodu")
        race_date = st.date_input("Datum")
        race_location = st.text_input("Místo")

        if st.button("Vytvořit závod"):
            if race_name.strip():
                db.create_race(race_name, race_date, race_location)
                st.success("Závod vytvořen")
                st.rerun()

    # obrazovka detail závodu
    if "selected_race" in st.session_state:
        race = db.get_race(st.session_state.selected_race)
        
        st.header(race["name"])
        st.write("📅 ", race["date"])
        st.write("📍", race["location"])

        today = date.today()

        # převod stringu z DB na date
        race_date = datetime.strptime(race["date"], "%Y-%m-%d").date()

        is_race_today_or_past = today >= race_date

        st.subheader("Pozice na závodě")

        selected_race_id = st.session_state.selected_race
        positions = db.get_positions_for_race(selected_race_id)

        user_already_signed = db.is_user_signed_up_for_race(
            selected_race_id,
            current_user_id
        )


        if not positions:
            st.info("Zatím nejsou přidané žádné pozice.")
        else:
            for pos in positions:
                occupied = db.get_occupied_count(pos["id"])
                capacity = pos["capacity"]
                free = capacity - occupied

                progress_value = occupied / capacity if capacity > 0 else 0

                # řádek: text + tlačítko
                col1, col2 = st.columns([1, 1])

                with col1:
                    st.write(f"**{pos['name']}** — {occupied}/{capacity}")

                with col2:
                    if is_race_today_or_past:
                        st.badge("Přihlašování uzavřeno", color="gray", icon=":material/lock:")
                    elif user_already_signed:
                        st.badge("Už jsi přihlášen", color="green", icon=":material/check:")
                    else:
                        if free > 0:
                            if st.button(
                                "Přihlásit",
                                key=f"signup_{pos['id']}"
                            ):
                                db.signup_user(
                                    selected_race_id,
                                    pos["id"],
                                    current_user_id
                                )
                                st.success("Přihlášen")
                                st.rerun()
                        else:
                            st.badge("Plno", color="red", icon=":material/block:")



                bar_col, _ = st.columns([1, 9])
                with bar_col:
                    st.progress(progress_value)
            
                if role == "admin" and page == "Správa závodů ⚙️":
                    st.markdown("**Přihlášení:**")

                    # Získání seznamu přihlášených uživatelů na pozici
                    signups = db.get_signups_for_position(pos["id"])

                    # Pokud nejsou přihlášeni žádní uživatelé
                    if not signups:
                        st.caption("Nikdo zatím přihlášen")
                    else:
                        # Procházení všech přihlášených
                        for s in signups:
                            user_name = s["users_db"]["name"]  # Správný přístup k jménu uživatele
                            col_a, col_b = st.columns([4, 1])
                            with col_a:
                                st.write(f"👤 {user_name}")
                            with col_b:
                                # Možnost smazat přihlášení uživatele
                                if st.button("❌", key=f"remove_{s['id']}"):
                                    db.admin_remove_signup(s["id"])
                                    st.rerun()

                    # Před přidáním nového uživatele
                    st.markdown("➕ **Přidat uživatele**")
                    users = db.get_all_users_simple()  # Seznam všech uživatelů

                    # Výběr uživatele k přidání
                    user_map = {u["name"]: u["id"] for u in users}
                    selected_name = st.selectbox(
                        "Uživatel",
                        options=list(user_map.keys()),
                        key=f"user_select_{pos['id']}"
                    )

                    # Tlačítko pro přidání uživatele na pozici
                    if st.button("Přidat", key=f"add_{pos['id']}"):
                        db.admin_add_user(
                            selected_race_id,
                            pos["id"],
                            user_map[selected_name]
                        )
                        st.rerun()



        if page == "Správa závodů ⚙️" and role == "admin":
            st.divider()
            st.subheader("Přidat pozici")

            pos_name = st.text_input("Název pozice")
            pos_capacity = st.number_input(
                "Kapacita",
                min_value=1,
                step=1
            )

            if st.button("Přidat pozici"):
                if pos_name.strip():
                    db.create_position(
                        st.session_state.selected_race,
                        pos_name,
                        pos_capacity
                    )
                    st.success("Pozice přidána")
                    st.rerun()
        
        if st.button("Zpět na seznam", type="primary"):
            del st.session_state.selected_race
            st.rerun()

            if st.button("Přidat pozici"):
                if pos_name.strip():
                    db.create_position(
                        selected_race_id,
                        pos_name.strip(),
                        pos_capacity
                    )
                    st.success("Pozice přidána")
                    st.rerun()

        st.divider()

    # seznam závodů
    st.subheader("Seznam závodů")

    if role == "admin":
        show_archive = st.checkbox("Zobrazit archiv")
        if show_archive:
            races = db.get_archived_races()
        else:
            races = db.get_active_races()
    else:
        races = db.get_active_races()


    for race in races:
        race_date = date.fromisoformat(race["date"])
        is_archived = race_date < date.today()
        is_signup_closed = race_date <= date.today()

        icon = "🗂️" if is_archived else "🏁"

        col1, col2 = st.columns([1, 2])
        with col1:
            st.write(
                f"{icon} {race['name']} – {race_date} – {race['location']}"
            )
            with col2 :
                if st.button("Detail", key=race["id"]):
                    st.session_state.selected_race = race["id"]
                    #st.switch_page("pages/race_details.py")
                    st.rerun()

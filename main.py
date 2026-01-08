import streamlit as st
import streamlit_authenticator as stauth
import streamlit_option_menu as option_menu
from datetime import datetime, date

import database as db

#page config
st.set_page_config(page_title="Závody 2025: Kamera + AK2 + Optika + Start", page_icon="⚙️", layout = "wide")
st.header("Závody 2025", divider="gray", )

if "selected_race" not in st.session_state:
    st.session_state.selected_race = None

if "dialog_race_id" not in st.session_state:
    st.session_state.dialog_race_id = None

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

name, authentication_status, username = authenticator.login("Přihlášení", "main")

current_username = username
role = db.fetch_role(username=current_username)

if authentication_status == False:
    st.error("Nesprávné uživatelské jméno nebo heslo")

if authentication_status == None:
    st.warning("Prosím zadejte uživatelské jméno a heslo")

if authentication_status:

    if "admin_mode" not in st.session_state:
        st.session_state.admin_mode = False

#----- sidebar -----  
    with st.sidebar:    
        st.title(f"{name}")
        if role == "admin":
            st.badge("Admin", icon=":material/check:", color="yellow")

        st.divider()

        if role == "admin":
            st.sidebar.subheader("🛠 Admin mód")

            st.session_state.admin_mode = st.toggle(
                "Admin mód",
                value=st.session_state.admin_mode
            )
            st.divider()

        authenticator.logout("Odhlásit se")      

    #----- main page -----
    current_user_id = db.get_user_id(username)
    if not st.session_state.admin_mode:

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

            position_name = db.get_user_signup_with_position_name(
                race["id"],
                current_user_id
            )
            if position_name: badge = f"{position_name}"

            user_signup_badge = db.get_user_signup_for_race2(
                race["id"],
                current_user_id
            )
            badge_text = None
            badge_color = "green"

            if user_signup_badge:
                badge_text = badge

            icon = "🗂️" if is_archived else "🏁"

            col1, col2, col3 = st.columns([4, 1.2, 1])

            with col1:
                st.write(f"{icon} **{race['name']}**")
                st.caption(f"📅 {race_date} • 📍 {race['location']}")

            with col2:
                if badge_text:
                    st.badge(
                        badge_text,
                        color=badge_color,
                        icon=":material/check:"
                    )

            with col3:
                if st.button("Detail", key=f"detail_{race['id']}"):
                    st.session_state.dialog_race_id = race["id"]
                    st.rerun()


        if st.session_state.dialog_race_id:

            @st.dialog("Detail závodu")
            def race_detail_dialog():
                race_id = st.session_state.dialog_race_id
                race = db.get_race(race_id)

                today = date.today()
                race_date = date.fromisoformat(race["date"])
                is_race_today_or_past = today >= race_date

                days_to_race = (race_date - today).days
                can_user_unsubscribe = days_to_race > 3

                st.subheader(race["name"])
                colA, colB = st.columns([1, 1])

                with colA:
                    st.write("📅", race["date"])
                    st.write("📍", race["location"])
                
                with colB:
                    st.write("💾 ID závodu:", race["race_id"])
                    st.write("📝 ID v databázy:", race_id)

                st.divider()
                st.subheader("Pozice")

                positions = db.get_positions_for_race(race_id)

                user_signup = db.get_user_signup_for_race(race_id, current_user_id)
                user_position_id = user_signup["position_id"] if user_signup else None

                if not positions:
                    st.info("Zatím nejsou přidané žádné pozice.")

                for pos in positions:
                    occupied = db.get_occupied_count(pos["id"])
                    capacity = pos["capacity"]
                    free = capacity - occupied
                    progress = occupied / capacity if capacity else 0

                    col1, col2, col3 = st.columns([1, 1, 1])

                    with col1:
                        st.write(f"**{pos['name']}** — {occupied}/{capacity}")

                    with col2:
                        if is_race_today_or_past:
                            st.badge("Přihlašování uzavřeno", color="gray")

                        elif user_position_id == pos["id"]:
                            st.badge("Jsi přihlášen", color="green")

                        elif free <= 0:
                            st.badge("Plno", color="red")

                    with col3:
                        if not is_race_today_or_past and user_position_id == pos["id"]:

                            if can_user_unsubscribe:
                                if st.button("Odhlásit", key=f"unsubscribe_{pos['id']}"):
                                    db.unsubscribe_user(race_id, current_user_id)
                                    st.rerun()

                        elif not is_race_today_or_past and user_position_id is None and free > 0:
                            if st.button("Přihlásit", key=f"signup_{pos['id']}"):
                                db.signup_user(race_id, pos["id"], current_user_id)
                                st.rerun()

                    st.progress(progress)

                notes = db.get_race_notes(race_id)

                if notes:
                    container = st.container(border=True)
                    container.write("**Poznámky**")
                    container.caption(notes)
                
                else:
                    st.divider()

                if st.button("Zavřít", type="primary"):
                    del st.session_state.dialog_race_id
                    st.rerun()

            if "dialog_race_id" in st.session_state:
                race_detail_dialog()



    if st.session_state.admin_mode and role == "admin":
        st.header("🛠️ Admin dashboard")

        admin_tab = st.tabs([
            "📅 Závody",
            "➕ Vytvořit závod",
            "👤 Správa uživatelů"
        ])

        with admin_tab[0]:
            races = db.get_races()

            for race in races:
                occupied = db.get_occupied_for_race(race["id"])
                capacity = db.get_capacity_for_race(race["id"])
                race_date = date.fromisoformat(race["date"])
                is_archived = race_date < date.today()
                is_full = occupied >= capacity
                icon = "🗂️" if is_archived else "🏁"
                barva = "red" if is_full else "green"

                col1, col2, col3 = st.columns([3, 2.2, 1])

                with col1:
                    st.write(f"{icon} **{race['name']}**")
                    st.caption(f"📅 {race['date']} | 📍 {race['location']}")

                with col2:
                    st.badge(f"**{occupied} / {capacity} obsazeno**", color=barva)

                with col3:
                    if st.button("Upravit", key=f"detail_{race['id']}"):
                        st.session_state.dialog_race_id = race["id"]
                        st.session_state.selected_race = race["id"]
                        st.rerun()

        with admin_tab[1]:
            st.subheader("Vytvořit závod")

            race_name = st.text_input("Název závodu")
            race_date = st.date_input("Datum")
            race_location = st.text_input("Místo")
            db_race_id = st.text_input("ID závodu")

            if st.button("Vytvořit závod"):
                st.success("Závod úspěšně vytvořen.")
                if not db_race_id:
                    db_race_id = "0"
                if not race_location:
                    race_location = "-"
                if race_name.strip():
                    db.create_race(race_name, race_date, race_location, db_race_id)
                    st.rerun()
            

        with admin_tab[2]:
            users = db.get_all_users_stats()

            for user in users:
                st.write(f"**👤 {user['name']}**")
                st.caption(f"🪪 {user['username']} | 🛡️ {user['role']}")


        if st.session_state.dialog_race_id:

            @st.dialog("Správa závodu")
            def admin_sprava_dialog():
                race_id = st.session_state.dialog_race_id
                race = db.get_race(race_id)

                st.subheader(race["name"])
                colA, colB = st.columns([1, 1])

                with colA:
                    st.write("📅", race["date"])
                    st.write("📍", race["location"])
                
                with colB:
                    st.write("💾 ID závodu:", race["race_id"])
                    st.write("📝 ID v databázy:", race_id)

                st.divider()

                selected_race_id = st.session_state.selected_race
                positions = db.get_positions_for_race(selected_race_id)

                for pos in positions:
                    occupied = db.get_occupied_count(pos["id"])
                    capacity = pos["capacity"]

                    st.write(f"**{pos['name']}** — {occupied}/{capacity}")
                    
                    if role == "admin":
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

                        users = db.get_all_users_simple()  # Seznam všech uživatelů

                        # Výběr uživatele k přidání
                        user_map = {u["name"]: u["id"] for u in users}
                        selected_name = st.selectbox(
                            "**Přidat uživatele**",
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
                        st.divider()

                #####
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

                existing_notes = db.get_race_notes(race_id) if race_id else ""
                notes_input = st.text_area("Poznámka", value=existing_notes, height=100)

                if st.button("Uložit poznámku", key=f"save_notes_{race_id}"):
                    db.update_race_notes(race_id, notes_input)
                    st.rerun()

                st.divider()

                colC, colD = st.columns([1, 1])

                with colC:
                    if st.button("Zavřít", type="secondary"):
                        del st.session_state.dialog_race_id
                        st.rerun()
                
                with colD:
                    st.subheader("⚠️ Smazání závodu")

                    if st.button("Zatím nee", type="primary", disabled=True):
                            db.delete_race(st.session_state.selected_race)

                            st.session_state.selected_race = None
                            st.session_state.dialog_race_id = None
                            st.rerun()

            if "dialog_race_id" in st.session_state:
                admin_sprava_dialog()

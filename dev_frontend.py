import streamlit as st
import requests
import time

if 'session_id' not in st.session_state:
    st.session_state.session_id = None

if 'game_status' not in st.session_state:
    st.session_state.game_status = None

tab1, tab2, tab3, tab4 = st.tabs(
    ["Hangman Game", "Leaderboard", "Backend Status","about"]
    )

with tab1:
    st.title('Hangman Game')

    session_id = st.session_state.get('session_id', None)
    game_status = st.session_state.get('game_status', None)

    # Add a difficulty selection
    difficulty = st.selectbox("Select Difficulty", ["easy", "medium", "hard"])

    if st.button("Start New Game"):
        # Pass the selected difficulty to the backend
        if st.session_state.session_id is None:
            response = requests.get(f"http://localhost:8000/start?difficulty={difficulty}")
            data = response.json()
            session_id = data['session_id']
            st.session_state.session_id = session_id
            st.session_state.game_status = "Game started"
            st.write(f"Game started! Your session ID is {session_id}")


    if st.session_state.session_id:
        letter = st.text_input("Guess a letter:")
        if st.button("Guess"):
            response = requests.get(f"http://localhost:8000/guess/{session_id}/{letter}")
            data = response.json()
            st.session_state.game_status = data['status']
            st.write(f"Status: {data['status']}")
            st.write(f"Guessed Letters: {data['guessed_letters']}")
            st.write(f"Remaining Tries: {data['remaining_tries']}")

        if st.button("Get Hint"):
            response = requests.get(f"http://localhost:8000/hint/{session_id}")
            data = response.json()
            st.write(f"Hint: {data['hint']}")

        if st.button("End Game"):
            response = requests.get(f"http://localhost:8000/end/{session_id}")
            st.session_state.session_id = None
            st.session_state.game_status = None
            st.write("Game ended!")

        if game_status == "You Won!" or game_status == "Game Over":
            st.write(f"Status: {game_status}")
            st.session_state.session_id = None
            st.session_state.game_status = None


with tab2:
    col1, col2 = st.columns(2)

    with col1:
        st.write("Leaderboard")
        # Use pandas DataFrame to display the leaderboard
        pass
    with col2:
        st.write("My Score")
        # Use pandas DataFrame to display the your score
        pass

with tab3:
    response = requests.get("http://localhost:8000/alive")
    if response.status_code == 200:
        data = response.json()
        st.write(data)
        st.write("Server is alive!")

        # Check if 'info' exists and then proceed
        if 'info' in data and all(key in data['info'] for key in ['db_status', 'cpu_status', 'cpu_percent', 'ip_address', 'memory_percent', 'disk_percent']):
            st.write(f"Database status: {data['info']['db_status']}")
            st.write(f"CPU status: {data['info']['cpu_status']} ({data['info']['cpu_percent']})")
            st.write(f"IP Address: {data['info']['ip_address']}")
            st.write(f"Memory Usage: {data['info']['memory_percent']}")
            st.write(f"Disk Usage: {data['info']['disk_percent']}")
        else:
            st.write("Some expected information is missing from the server response.")
    else:
        st.write("Server is down!")


with tab4:
    st.write("This is a simple hangman game built using Python and Streamlit. The backend is built using FastAPI and MongoDB. The source code for this project can be found on GitHub.")
    st.write("Our team members are:")
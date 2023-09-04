import streamlit as st
import requests

st.title('Hangman Game')

session_id = st.session_state.get('session_id', None)
game_status = st.session_state.get('game_status', None)

# Add a difficulty selection
difficulty = st.selectbox("Select Difficulty", ["easy", "medium", "hard"])

if st.button("Start New Game"):
    # Pass the selected difficulty to the backend
    response = requests.get(f"http://localhost:8000/start?difficulty={difficulty}")
    data = response.json()
    session_id = data['session_id']
    st.session_state.session_id = session_id
    st.session_state.game_status = "Game started"
    st.write(f"Game started! Your session ID is {session_id}")


if session_id:
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

with st.container():
    response = requests.get(f"http://localhost:8000/leaderboard")
    data = response.json()
    st.write("Leaderboard")
    # Use pandas DataFrame to display the leaderboard
    pass

with st.container():
    response = requests.get("http://localhost:8000/alive")
    data = response.json()
    st.write(f"Backend Status: {data['status']}")


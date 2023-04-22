import { useRef, useState } from "react";
import ChatMessage from "./chat-message";

const ChatRoom = (props) => {
  const { uid = 'abc', photoURL = '' } = props;
  const dummy = useRef<HTMLSpanElement>();
  const messages = [];

  const [formValue, setFormValue] = useState('');


  const sendMessage = async (e) => {
    e.preventDefault();

    //   await messagesRef.add({
    //     text: formValue,
    //     createdAt: firebase.firestore.FieldValue.serverTimestamp(),
    //     uid,
    //     photoURL
    //   })

    setFormValue('');
    dummy.current.scrollIntoView({ behavior: 'smooth' });
  }

  return (<>
    <main>

      {messages && messages.map(msg => <ChatMessage key={msg.id} message={msg} />)}

      <span ref={dummy}></span>

    </main>

    <form onSubmit={sendMessage}>

      <input value={formValue} onChange={(e) => setFormValue(e.target.value)} placeholder="say something nice" />

      <button type="submit" disabled={!formValue}>🕊️</button>

    </form>
  </>)
}

export default ChatRoom;
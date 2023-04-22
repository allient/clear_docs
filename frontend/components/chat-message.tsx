const ChatMessage = (props) => {
  const { text, photoURL } = props.message;

  const messageClass = 'sent';

  return (<>
    <div className={`message ${messageClass}`}>
      <img src={photoURL || 'https://api.adorable.io/avatars/23/abott@adorable.png'} />
      <p>{text}</p>
    </div>
  </>)
}

export default ChatMessage;
import React from 'react';

const AddTodo = () => {
  const [text, setText] = React.useState('');

  return (
    <div>
      <input type="text" value={text} onChange={(e) => setText(e.target.value)} />
      <button onClick={() => console.log(text)}>Adicionar</button>
    </div>
  );
};

export default AddTodo;
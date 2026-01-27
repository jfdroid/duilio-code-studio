import React from 'react';

const TodoItem = ({ todo, onDelete }) => {
  return (
    <li>
      <input type="checkbox" checked={todo.completed} onChange={() => console.log(todo)} />
      <span style={{ textDecoration: todo.completed ? 'line-through' : 'none' }}>
        {todo.text}
      </span>
      <button onClick={() => onDelete(todo)}>Remover</button>
    </li>
  );
};

export default TodoItem;
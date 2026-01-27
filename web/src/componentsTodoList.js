import React from 'react';

const TodoList = () => {
  const [todos, setTodos] = React.useState([
    { id: 1, text: 'Comprar leite', completed: false },
    { id: 2, text: 'Fazer caminhada', completed: false },
  ]);

  return (
    <div>
      <h1>Minha Lista de Tarefas</h1>
      <ul>
        {todos.map((todo) => (
          <li key={todo.id}>
            <input
              type="checkbox"
              checked={todo.completed}
              onChange={() => {
                setTodos(
                  todos.map((t) =>
                    t.id === todo.id ? { ...t, completed: !t.completed } : t,
                  ),
                );
              }}
            />
            <span style={{ textDecoration: todo.completed ? 'line-through' : 'none' }}>
              {todo.text}
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
};

export default TodoList;
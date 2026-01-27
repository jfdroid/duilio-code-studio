import React from 'react';
import TodoList from './components/TodoList';
import AddTodo from './components/AddTodo';

const TodoListContainer = () => {
  const [todos, setTodos] = React.useState([
    { id: 1, text: 'Comprar leite', completed: false },
    { id: 2, text: 'Fazer caminhada', completed: false },
  ]);

  const onDelete = (todo) => {
    setTodos(todos.filter((t) => t.id !== todo.id));
  };

  return (
    <div>
      <TodoList todos={todos} />
      <AddTodo />
    </div>
  );
};

export default TodoListContainer;
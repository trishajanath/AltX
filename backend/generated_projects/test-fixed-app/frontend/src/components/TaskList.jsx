import React from 'react';
import TaskItem from './TaskItem';
import { ClipboardList } from 'lucide-react';

/**
 * TaskList Component
 * 
 * 🛡️ Advanced Security Analysis: TaskList Component
 * This component acts as a "dumb" or presentational component. Its sole responsibility is to render a list of items.
 * 1.  **Prop Drilling Control**: By receiving functions (`onDeleteTask`, `onToggleComplete`) as props and passing them down, it adheres to the unidirectional data flow. This prevents security vulnerabilities that could arise if child components had direct access to modify the application's state or make arbitrary API calls.
 * 2.  **Key Prop Usage**: The `key={task.id}` is crucial not just for React's performance but also for state integrity. Without a stable and unique key, React might confuse list items, leading to incorrect state being displayed or updated, which could have security implications if the data were sensitive.
 * 3.  **Content Rendering**: It handles the "no tasks" case gracefully, providing clear user feedback instead of a blank screen. This is good practice for user experience and prevents user confusion.
 *
 * This component is responsible for rendering the list of tasks. It maps over
 * the `tasks` array and renders a `TaskItem` for each one, passing down the
 * necessary props and callbacks.
 */
function TaskList({ tasks, onDeleteTask, onToggleComplete }) {
  if (tasks.length === 0) {
    return (
      <div className="container mx-auto p-4">
        <div className="flex items-center justify-center min-h-64">
          <div className="text-center">
            <ClipboardList className="mx-auto h-12 w-12 text-gray-400 mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No tasks yet</h3>
            <p className="text-gray-500">Add a new task above to get started!</p>
          </div>
        </div>
      </div>
    );
  }

  // Sort tasks to show incomplete ones first
  const sortedTasks = [...tasks].sort((a, b) => a.completed - b.completed);

  return (
    <div className="space-y-2">
      {sortedTasks.map((task) => (
        <TaskItem
          key={task.id}
          task={task}
          onDeleteTask={onDeleteTask}
          onToggleComplete={onToggleComplete}
        />
      ))}
    </div>
  );
}

export default TaskList;
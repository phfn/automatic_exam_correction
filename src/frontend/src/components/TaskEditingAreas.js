import React from "react"
import TaskEditingArea from "./TaskEditingArea"
const TaskEditingAreas = ({
	tasks,
	setTasks,
	loadCroppingArea,
	deleteTask,
	saveCropInTask,
	editing,
	setEditing,
	canEditAnswer,
	setHoverIndex,
}) => {
	const setTask = (index, newTask) => {
		const newTasks = tasks.map((task) => {
			return task.clone()
		})
		newTasks[index] = newTask.clone()
		setTasks(newTasks)
	}

	return (
		<div className="Tasks">
			{tasks.map((task, index) => (
				<TaskEditingArea
					key={index}
					task={task}
					taskId={index}
					setTask={(newTask) => {
						setTask(index, newTask)
					}}
					loadCroppingArea={() => {
						loadCroppingArea(index)
					}}
					deleteTask={() => deleteTask(index)}
					editing={editing}
					saveCropInTask={() => {
						saveCropInTask(index)
					}}
					setEditing={setEditing}
					canEditAnswer={canEditAnswer}
					onHover={() => {
						setHoverIndex(index)
					}}
					onHoverLeave={() => {
						setHoverIndex(-1)
					}}
				/>
			))}
		</div>
	)
}
export default TaskEditingAreas

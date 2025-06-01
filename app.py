from flask import Flask, jsonify, request

app = Flask(__name__)

tasks = [
    {'id': 1, 'title': 'Task 1', 'completed': False},
    {'id': 2, 'title': 'Task 2', 'completed': True}
]

users = []
calendar_events = []
notifications = []
settings = {}

# User Authentication
@app.route('/api/register', methods=['POST'])
def register_user():
    user = request.json
    users.append(user)
    return jsonify(user), 201

@app.route('/api/login', methods=['POST'])
def login_user():
    # Implement login logic here
    return jsonify({'message': 'User logged in'}), 200

@app.route('/api/logout', methods=['POST'])
def logout_user():
    # Implement logout logic here
    return jsonify({'message': 'User logged out'}), 200

# User Management
@app.route('/api/users', methods=['GET'])
def get_users():
    return jsonify(users)

@app.route('/api/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    user = next((user for user in users if user['id'] == user_id), None)
    if user is None:
        return jsonify({'error': 'User not found'}), 404
    return jsonify(user)

@app.route('/api/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    user = next((user for user in users if user['id'] == user_id), None)
    if user is None:
        return jsonify({'error': 'User not found'}), 404
    user.update(request.json)
    return jsonify(user)

@app.route('/api/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    global users
    users = [user for user in users if user['id'] != user_id]
    return jsonify({'message': 'User deleted'}), 200

# Calendar Integration
@app.route('/api/calendar/events', methods=['GET'])
def get_calendar_events():
    return jsonify(calendar_events)

@app.route('/api/calendar/events', methods=['POST'])
def create_calendar_event():
    event = request.json
    calendar_events.append(event)
    return jsonify(event), 201

@app.route('/api/calendar/events/<int:event_id>', methods=['PUT'])
def update_calendar_event(event_id):
    event = next((event for event in calendar_events if event['id'] == event_id), None)
    if event is None:
        return jsonify({'error': 'Event not found'}), 404
    event.update(request.json)
    return jsonify(event)

@app.route('/api/calendar/events/<int:event_id>', methods=['DELETE'])
def delete_calendar_event(event_id):
    global calendar_events
    calendar_events = [event for event in calendar_events if event['id'] != event_id]
    return jsonify({'message': 'Event deleted'}), 200

# Notifications
@app.route('/api/notifications', methods=['GET'])
def get_notifications():
    return jsonify(notifications)

@app.route('/api/notifications', methods=['POST'])
def create_notification():
    notification = request.json
    notifications.append(notification)
    return jsonify(notification), 201

@app.route('/api/notifications/<int:notification_id>', methods=['DELETE'])
def delete_notification(notification_id):
    global notifications
    notifications = [notification for notification in notifications if notification['id'] != notification_id]
    return jsonify({'message': 'Notification deleted'}), 200

# Settings
@app.route('/api/settings', methods=['GET'])
def get_settings():
    return jsonify(settings)

@app.route('/api/settings', methods=['PUT'])
def update_settings():
    settings.update(request.json)
    return jsonify(settings)

@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    return jsonify(tasks)

@app.route('/api/tasks', methods=['POST'])
def create_task():
    new_task = request.json
    new_task['id'] = len(tasks) + 1
    tasks.append(new_task)
    return jsonify(new_task), 201

@app.route('/api/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    task = next((task for task in tasks if task['id'] == task_id), None)
    if task is None:
        return jsonify({'error': 'Task not found'}), 404
    task.update(request.json)
    return jsonify(task)

@app.route('/api/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    global tasks
    tasks = [task for task in tasks if task['id'] != task_id]
    return '', 204

if __name__ == '__main__':
    app.run(debug=True) 
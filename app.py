from flask import Flask, request, jsonify
from models.Users import db, User
from Utils.codigo import generate_recovery_code
from Utils.email_sender import send_email
from Utils.sms_sender import send_sms
from config import Config
import os

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    if User.query.filter_by(email=data['email']).first() or User.query.filter_by(username=data['username']).first():
        return jsonify({'message': 'Usuario o correo ya registrados'}), 400

    new_user = User(
        email=data['email'],
        first_name=data['first_name'],
        last_name=data['last_name'],
        username=data['username'],
        phone_number=data.get('phone_number')
    )
    new_user.set_password(data['password'])
    db.session.add(new_user)
    db.session.commit()

    return jsonify({'message': 'Usuario registrado exitosamente'}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    user = User.query.filter_by(username=data['username']).first()
    if user and user.check_password(data['password']):
        return jsonify({'message': 'Inicio de sesión exitoso'}), 200
    return jsonify({'message': 'Usuario o contraseña incorrectos'}), 401

@app.route('/recover', methods=['POST'])
def recover():
    data = request.json

    # Validar si se proporciona el método (email o sms)
    if 'method' not in data or data['method'] not in ['email', 'sms']:
        return jsonify({'message': 'Debes especificar un método válido: "email" o "sms"'}), 400

    user = User.query.filter_by(email=data.get('email')).first()
    if not user:
        return jsonify({'message': 'Correo no registrado'}), 404

    recovery_code = generate_recovery_code()
    user.recovery_code = recovery_code
    db.session.commit()

    if data['method'] == 'email':
        # Verificar que se proporcione un correo electrónico
        if 'email' not in data or not data['email']:
            return jsonify({'message': 'Debes proporcionar un correo electrónico válido'}), 400

        # Enviar código por correo
        template_path = os.path.join('templates', 'email.html')
        with open(template_path, 'r') as file:
            html_body = file.read()

        html_body = html_body.replace('{{ first_name }}', user.first_name)
        html_body = html_body.replace('{{ last_name }}', user.last_name)
        html_body = html_body.replace('{{ recovery_code }}', recovery_code)

        send_email("Código de recuperación", data['email'], html_body)
        return jsonify({'message': 'Código de recuperación enviado al correo'}), 200

    elif data['method'] == 'sms':
        # Verificar que se proporcione un número de teléfono
        if not user.phone_number:
            return jsonify({'message': 'No se encontró un número de teléfono asociado a este usuario'}), 400

        message = f"Hola {user.first_name}, tu código de recuperación es: {recovery_code}"
        send_sms(message, user.phone_number)
        return jsonify({'message': 'Código de recuperación enviado al teléfono'}), 200

    return jsonify({'message': 'Método de recuperación inválido'}), 400

@app.route('/reset-password', methods=['POST'])
def reset_password():
    data = request.json
    user = User.query.filter_by(email=data['email'], recovery_code=data['recovery_code']).first()
    if not user:
        return jsonify({'message': 'Código de recuperación inválido o expirado'}), 404

    user.set_password(data['new_password'])
    user.recovery_code = None
    db.session.commit()

    return jsonify({'message': 'Contraseña restablecida exitosamente'}), 200

@app.route('/users', methods=['GET'])
def get_users():
    users = User.query.all()
    users_list = [
        {
            'id': user.id,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'username': user.username,
            'phone_number': user.phone_number
        } for user in users
    ]
    return jsonify(users_list), 200

@app.route('/update-user/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    """
    Endpoint para actualizar la información de un usuario.
    """
    data = request.json
    user = User.query.get(user_id)
    if not user:
        return jsonify({'message': 'Usuario no encontrado'}), 404

    # Actualizar información solo si los campos están presentes en el JSON
    if 'email' in data:
        if User.query.filter(User.email == data['email'], User.id != user_id).first():
            return jsonify({'message': 'El correo ya está registrado por otro usuario'}), 400
        user.email = data['email']

    if 'username' in data:
        if User.query.filter(User.username == data['username'], User.id != user_id).first():
            return jsonify({'message': 'El nombre de usuario ya está registrado por otro usuario'}), 400
        user.username = data['username']

    if 'first_name' in data:
        user.first_name = data['first_name']

    if 'last_name' in data:
        user.last_name = data['last_name']

    if 'phone_number' in data:
        user.phone_number = data['phone_number']

    if 'password' in data:
        user.set_password(data['password'])  # Actualizar la contraseña encriptada

    db.session.commit()
    return jsonify({'message': 'Información del usuario actualizada exitosamente'}), 200


@app.route('/delete-user/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    """
    Endpoint para eliminar un usuario.
    """
    user = User.query.get(user_id)
    if not user:
        return jsonify({'message': 'Usuario no encontrado'}), 404

    db.session.delete(user)
    db.session.commit()
    return jsonify({'message': f'Usuario con ID {user_id} eliminado exitosamente'}), 200


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)

from flask import Flask, request, jsonify
from flask_cors import CORS  # Importa flask-cors
from models.Users import db, User
from Utils.codigo import generate_recovery_code
from Utils.email_sender import send_email
from Utils.sms_sender import send_sms
from config import Config
import os

app = Flask(__name__)
app.config.from_object(Config)

# Habilitar CORS
CORS(app, resources={r"/*": {"origins": "*"}})  # Permitir todas las rutas y todos los orígenes

db.init_app(app)

@app.route('/')
def index():
    return jsonify({'Hola': 'esta es tu api'})

@app.route('/register', methods=['POST'])
def register():
    try:
        # Validar que todos los campos requeridos estén presentes
        data = request.json
        required_fields = ['email', 'username', 'first_name', 'last_name', 'password']
        
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({
                    'message': f'El campo {field} es requerido',
                    'error': 'MISSING_FIELD'
                }), 400

        # Verificar si el usuario o email ya existen
        if User.query.filter_by(email=data['email']).first():
            return jsonify({
                'message': 'El correo electrónico ya está registrado',
                'error': 'EMAIL_EXISTS'
            }), 400

        if User.query.filter_by(username=data['username']).first():
            return jsonify({
                'message': 'El nombre de usuario ya está registrado',
                'error': 'USERNAME_EXISTS'
            }), 400

        # Crear nuevo usuario
        new_user = User(
            email=data['email'],
            username=data['username'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            phone_number=data.get('phone_number', '')  # Campo opcional
        )
        
        # Establecer la contraseña
        new_user.set_password(data['password'])

        # Guardar en la base de datos
        db.session.add(new_user)
        db.session.commit()

        return jsonify({
            'message': 'Usuario registrado exitosamente',
            'user': {
                'email': new_user.email,
                'username': new_user.username,
                'first_name': new_user.first_name,
                'last_name': new_user.last_name
            }
        }), 201

    except Exception as e:
        db.session.rollback()
        print(f"Error en registro: {str(e)}")
        return jsonify({
            'message': 'Error interno del servidor',
            'error': str(e)
        }), 500

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

    if 'method' not in data or data['method'] not in ['email', 'sms']:
        return jsonify({'message': 'Debes especificar un método válido: "email" o "sms"'}), 400

    user = User.query.filter_by(email=data.get('email')).first()
    if not user:
        return jsonify({'message': 'Correo no registrado'}), 404

    recovery_code = generate_recovery_code()
    user.recovery_code = recovery_code
    db.session.commit()

    if data['method'] == 'email':
        if 'email' not in data or not data['email']:
            return jsonify({'message': 'Debes proporcionar un correo electrónico válido'}), 400

        template_path = os.path.join('templates', 'email.html')
        with open(template_path, 'r') as file:
            html_body = file.read()

        html_body = html_body.replace('{{ first_name }}', user.first_name)
        html_body = html_body.replace('{{ last_name }}', user.last_name)
        html_body = html_body.replace('{{ recovery_code }}', recovery_code)

        send_email("Código de recuperación", data['email'], html_body)
        return jsonify({'message': 'Código de recuperación enviado al correo'}), 200

    elif data['method'] == 'sms':
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
    data = request.json
    user = User.query.get(user_id)
    if not user:
        return jsonify({'message': 'Usuario no encontrado'}), 404

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
        user.set_password(data['password'])

    db.session.commit()
    return jsonify({'message': 'Información del usuario actualizada exitosamente'}), 200

@app.route('/delete-user/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({'message': 'Usuario no encontrado'}), 404

    db.session.delete(user)
    db.session.commit()
    return jsonify({'message': f'Usuario con ID {user_id} eliminado exitosamente'}), 200

# Visor de esquema de la base de datos
@app.route('/debug-schema', methods=['GET'])
def debug_schema():
    from sqlalchemy import inspect
    inspector = inspect(db.engine)
    columns = inspector.get_columns('users')
    return jsonify({col['name']: str(col['type']) for col in columns})

@app.route('/migrate-schema', methods=['POST'])
def migrate_schema():
    try:
        with db.engine.connect() as conn:
            conn.execute("""
                ALTER TABLE users 
                MODIFY COLUMN password_hash VARCHAR(256) NOT NULL;
            """)
            return jsonify({'message': 'Schema updated successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    with app.app_context():
        db.drop_all()  # Solo si estás seguro de que quieres borrar todo
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=True)